import { Injectable, Logger, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import * as amqp from 'amqplib';
import { QUEUE_CONFIG } from '../../shared/constants/queue.constants';
import { NotificationMessage } from '../../shared/interfaces/notification-message.interface';

@Injectable()
export class EmailConsumer implements OnModuleInit, OnModuleDestroy {
  private readonly logger = new Logger(EmailConsumer.name);
  private connection: Awaited<ReturnType<typeof amqp.connect>> | null = null;
  private channel: amqp.ConfirmChannel | null = null;
  private messageHandler: ((message: NotificationMessage) => Promise<void>) | null = null;

  constructor(private readonly configService: ConfigService) {}

  async onModuleInit() {
    await this.connect();
  }

  async onModuleDestroy() {
    await this.disconnect();
  }

  private async connect(): Promise<void> {
    try {
      const rabbitmqUrl = this.configService.get<string>(
        'RABBITMQ_URL',
        'amqp://guest:guest@localhost:5672'
      );

      this.logger.log(`Connecting to RabbitMQ at ${rabbitmqUrl}`);
      this.connection = await amqp.connect(rabbitmqUrl);
      this.channel = await this.connection.createConfirmChannel();

      // Set prefetch to process one message at a time
      await this.channel!.prefetch(1);

      // Assert exchange
      await this.channel!.assertExchange(
        QUEUE_CONFIG.EXCHANGE,
        'direct',
        { durable: true }
      );

      // Assert dead letter exchange
      await this.channel!.assertExchange(
        QUEUE_CONFIG.DLX_EXCHANGE,
        'direct',
        { durable: true }
      );

      // Assert dead letter queue
      await this.channel!.assertQueue(QUEUE_CONFIG.FAILED_QUEUE, {
        durable: true,
      });

      // Bind failed queue to DLX
      await this.channel!.bindQueue(
        QUEUE_CONFIG.FAILED_QUEUE,
        QUEUE_CONFIG.DLX_EXCHANGE,
        QUEUE_CONFIG.DLX_ROUTING_KEY
      );

      // Assert email queue with DLX config
      await this.channel!.assertQueue(QUEUE_CONFIG.EMAIL_QUEUE, {
        durable: true,
        deadLetterExchange: QUEUE_CONFIG.DLX_EXCHANGE,
        deadLetterRoutingKey: QUEUE_CONFIG.DLX_ROUTING_KEY,
      });

      // Bind email queue to exchange
      await this.channel!.bindQueue(
        QUEUE_CONFIG.EMAIL_QUEUE,
        QUEUE_CONFIG.EXCHANGE,
        QUEUE_CONFIG.EMAIL_ROUTING_KEY
      );

      this.logger.log('RabbitMQ connection established successfully');
    } catch (error) {
      this.logger.error('Failed to connect to RabbitMQ', error);
      throw error;
    }
  }

  async startConsuming(): Promise<void> {
    if (!this.channel) {
      throw new Error('Channel not initialized');
    }

    if (!this.messageHandler) {
      throw new Error('Message handler not set. Call setMessageHandler first.');
    }

    this.logger.log(`Starting to consume from ${QUEUE_CONFIG.EMAIL_QUEUE}`);

    await this.channel.consume(
      QUEUE_CONFIG.EMAIL_QUEUE,
      async (msg) => {
        if (!msg) {
          this.logger.warn('Received null message');
          return;
        }

        const messageContent = msg.content.toString();
        this.logger.log(`Received message: ${messageContent.substring(0, 100)}...`);

        try {
          const message: NotificationMessage = JSON.parse(messageContent);
          
          // Call the registered message handler
          await this.messageHandler!(message);

          // Acknowledge message on success
          this.channel!.ack(msg);
          this.logger.log(`Message processed successfully: ${message.message_id}`);
        } catch (error) {
          this.logger.error('Error processing message', error);
          
          // Reject and requeue (will go to DLQ after max retries)
          // Note: Consider implementing retry count tracking
          this.channel!.nack(msg, false, false);
        }
      },
      { noAck: false }
    );

    this.logger.log('Email consumer started successfully');
  }

  setMessageHandler(handler: (message: NotificationMessage) => Promise<void>): void {
    this.messageHandler = handler;
  }

  async disconnect(): Promise<void> {
    try {
      if (this.channel) {
        await this.channel.close();
        this.logger.log('Channel closed');
      }

      if (this.connection) {
        await this.connection.close();
        this.logger.log('RabbitMQ connection closed');
      }
    } catch (error) {
      this.logger.error('Error during disconnect', error);
    }
  }

  async isHealthy(): Promise<boolean> {
    return this.connection !== null && this.channel !== null;
  }
}
