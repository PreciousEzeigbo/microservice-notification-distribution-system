import { Injectable, Logger, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import * as amqp from 'amqplib';
import { QUEUE_CONFIG } from '../../shared/constants/queue.constants';
import { NotificationMessage } from '../../shared/interfaces/notification-message.interface';
import * as MSG from '../../constants/system.messages';

const MAX_RETRY_ATTEMPTS = 3;
const RETRY_DELAY_MS = 5000;
const CONNECTION_RETRY_DELAY_MS = 10000;

@Injectable()
export class EmailConsumer implements OnModuleInit, OnModuleDestroy {
  private readonly logger = new Logger(EmailConsumer.name);
  private connection: Awaited<ReturnType<typeof amqp.connect>> | null = null;
  private channel: amqp.ConfirmChannel | null = null;
  private message_handler: ((message: NotificationMessage) => Promise<void>) | null = null;
  private is_shutting_down = false;
  private reconnect_timeout: NodeJS.Timeout | null = null;

  constructor(private readonly configService: ConfigService) {}

  async onModuleInit() {
    await this.connect();
  }

  async onModuleDestroy() {
    this.is_shutting_down = true;
    if (this.reconnect_timeout) {
      clearTimeout(this.reconnect_timeout);
      this.reconnect_timeout = null;
    }
    await this.disconnect();
  }

  private async connect(): Promise<void> {
    if (this.connection && this.channel) {
      return;
    }

    try {
      const rabbitmqUrl = this.configService.get<string>(
        'RABBITMQ_URL',
        'amqp://guest:guest@localhost:5672'
      );

      this.logger.log(MSG.RABBITMQ_CONNECTING(rabbitmqUrl));
      this.connection = await amqp.connect(rabbitmqUrl);
      
      // Setup connection event handlers for resilience
      this.connection.on('error', (err: Error) => {
        this.logger.error('RabbitMQ connection error', err);
        if (!this.is_shutting_down) {
          this.handleConnectionLoss();
        }
      });

      this.connection.on('close', () => {
        this.logger.warn('RabbitMQ connection closed');
        if (!this.is_shutting_down) {
          this.handleConnectionLoss();
        }
      });

      this.channel = await this.connection.createConfirmChannel();

      // Setup channel event handlers
      this.channel.on('error', (err: Error) => {
        this.logger.error('RabbitMQ channel error', err);
      });

      this.channel.on('close', () => {
        this.logger.warn('RabbitMQ channel closed');
      });

      // Set prefetch to process one message at a time
      await this.channel.prefetch(1);

      // Assert exchange
      await this.channel.assertExchange(
        QUEUE_CONFIG.EXCHANGE,
        'direct',
        { durable: true }
      );

      // Assert dead letter exchange
      await this.channel.assertExchange(
        QUEUE_CONFIG.DLX_EXCHANGE,
        'direct',
        { durable: true }
      );

      // Assert dead letter queue
      await this.channel.assertQueue(QUEUE_CONFIG.FAILED_QUEUE, {
        durable: true,
      });

      // Bind failed queue to DLX
      await this.channel.bindQueue(
        QUEUE_CONFIG.FAILED_QUEUE,
        QUEUE_CONFIG.DLX_EXCHANGE,
        QUEUE_CONFIG.DLX_ROUTING_KEY
      );

      // Assert email queue with DLX config
      await this.channel.assertQueue(QUEUE_CONFIG.EMAIL_QUEUE, {
        durable: true,
        deadLetterExchange: QUEUE_CONFIG.DLX_EXCHANGE,
        deadLetterRoutingKey: QUEUE_CONFIG.DLX_ROUTING_KEY,
      });

      // Bind email queue to exchange
      await this.channel.bindQueue(
        QUEUE_CONFIG.EMAIL_QUEUE,
        QUEUE_CONFIG.EXCHANGE,
        QUEUE_CONFIG.EMAIL_ROUTING_KEY
      );

      // Assert delay queue for retry with TTL
      await this.channel.assertQueue('email_delay_queue', {
        durable: true,
        arguments: {
          'x-message-ttl': RETRY_DELAY_MS,
          'x-dead-letter-exchange': QUEUE_CONFIG.EXCHANGE,
          'x-dead-letter-routing-key': QUEUE_CONFIG.EMAIL_ROUTING_KEY,
        },
      });

      this.logger.log(MSG.RABBITMQ_CONNECTED);
    } catch (error) {
      this.logger.error(MSG.RABBITMQ_CONNECTION_FAILED, error);
      throw error;
    }
  }

  async startConsuming(): Promise<void> {
    if (!this.channel) {
      await this.connect();
    }

    if (!this.message_handler) {
      throw new Error(MSG.QUEUE_HANDLER_NOT_SET);
    }

    if (!this.channel) {
      throw new Error(MSG.QUEUE_CHANNEL_NOT_INITIALIZED);
    }

    this.logger.log(MSG.QUEUE_CONSUMING_STARTED(QUEUE_CONFIG.EMAIL_QUEUE));

    await this.channel.consume(
      QUEUE_CONFIG.EMAIL_QUEUE,
      async (msg) => {
        if (!msg) {
          this.logger.warn(MSG.QUEUE_MESSAGE_NULL);
          return;
        }

        const message_content = msg.content.toString();
        this.logger.log(MSG.QUEUE_MESSAGE_RECEIVED(message_content));

        try {
          const message: NotificationMessage = JSON.parse(message_content);
          const retry_count = this.getRetryCount(msg);
          
          // Call the registered message handler
          if (this.message_handler) {
            await this.message_handler(message);
          }

          // Acknowledge message on success
          if (this.channel) {
            this.channel.ack(msg);
            this.logger.log(MSG.QUEUE_MESSAGE_PROCESSED(message.message_id));
          }
        } catch (error) {
          await this.handleMessageError(msg, error);
        }
      },
      { noAck: false }
    );

    this.logger.log(MSG.QUEUE_CONSUMER_STARTED);
  }

  /**
   * Get retry count from message headers
   */
  private getRetryCount(msg: amqp.ConsumeMessage): number {
    if (!msg.properties.headers) {
      return 0;
    }
    const retry_count = msg.properties.headers['x-retry-count'];
    return (typeof retry_count === 'number' ? retry_count : 0);
  }

  /**
   * Handle message processing errors with retry logic
   */
  private async handleMessageError(
    msg: amqp.ConsumeMessage,
    error: unknown,
  ): Promise<void> {
    this.logger.error(MSG.QUEUE_MESSAGE_PROCESSING_ERROR, error);

    if (!this.channel) {
      this.logger.error('Cannot handle message error: channel is null');
      return;
    }

    const retry_count = this.getRetryCount(msg);

    if (retry_count < MAX_RETRY_ATTEMPTS) {
      // Increment retry count and send to delay queue
      const new_retry_count = retry_count + 1;
      this.logger.warn(
        `Delaying message retry ${new_retry_count}/${MAX_RETRY_ATTEMPTS} for ${RETRY_DELAY_MS}ms`,
      );

      // Prepare headers for retry tracking
      const headers = msg.properties.headers || {};
      headers['x-retry-count'] = new_retry_count;
      headers['x-last-error'] = error instanceof Error ? error.message : String(error);
      headers['x-last-retry-time'] = new Date().toISOString();

      // Publish to delay queue
      this.channel.sendToQueue(
        'email_delay_queue',
        msg.content,
        {
          headers,
          persistent: true,
        },
      );

      // Acknowledge the failed message to remove it from main queue
      this.channel.ack(msg);
    } else {
      // Max retries exceeded, send to dead letter queue
      this.logger.error(
        `Max retry attempts (${MAX_RETRY_ATTEMPTS}) exceeded. Sending to DLQ.`,
      );
      this.channel.nack(msg, false, false);
    }
  }

  /**
   * Handle connection loss and attempt reconnection
   */
  private handleConnectionLoss(): void {
    this.connection = null;
    this.channel = null;

    if (this.is_shutting_down) {
      return;
    }

    this.logger.warn(
      `Connection lost. Attempting reconnection in ${CONNECTION_RETRY_DELAY_MS}ms...`,
    );

    this.reconnect_timeout = setTimeout(async () => {
      try {
        await this.connect();
        if (this.message_handler) {
          await this.startConsuming();
        }
      } catch (error) {
        this.logger.error('Reconnection attempt failed', error);
        this.handleConnectionLoss();
      }
    }, CONNECTION_RETRY_DELAY_MS);
  }

  setMessageHandler(handler: (message: NotificationMessage) => Promise<void>): void {
    this.message_handler = handler;
  }

  async disconnect(): Promise<void> {
    try {
      if (this.channel) {
        await this.channel.close();
        this.logger.log(MSG.RABBITMQ_CHANNEL_CLOSED);
      }

      if (this.connection) {
        await this.connection.close();
        this.logger.log(MSG.RABBITMQ_CONNECTION_CLOSED);
      }
    } catch (error) {
      this.logger.error(MSG.RABBITMQ_DISCONNECT_ERROR, error);
    }
  }

  async isHealthy(): Promise<boolean> {
    return this.connection !== null && this.channel !== null;
  }
}
