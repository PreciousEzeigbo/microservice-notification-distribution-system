import { Injectable, Logger, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import * as amqp from 'amqplib';
import { QUEUE_CONFIG } from '../../shared/constants/queue.constants';
import * as MSG from '../../constants/system.messages';
import { UserServiceClient } from '../http/user.service.client';
import { TemplateServiceClient } from '../http/template.service.client';

const DLQ_CHECK_INTERVAL_MS = 300000; // Check DLQ every 5 minutes
const MAX_DLQ_REPROCESS_ATTEMPTS = 5; // Max times to reprocess from DLQ
const BATCH_SIZE = 10; // Process up to 10 messages per check

@Injectable()
export class DlqReprocessor implements OnModuleInit, OnModuleDestroy {
  private readonly logger = new Logger(DlqReprocessor.name);
  private connection: Awaited<ReturnType<typeof amqp.connect>> | null = null;
  private channel: amqp.ConfirmChannel | null = null;
  private check_interval: NodeJS.Timeout | null = null;
  private is_shutting_down = false;

  // Track last health status to log only on change
  private lastServicesHealthy: boolean | null = null;

  constructor(
    private readonly configService: ConfigService,
    private readonly userServiceClient: UserServiceClient,
    private readonly templateServiceClient: TemplateServiceClient,
  ) {}

  async onModuleInit() {
    await this.connect();
    this.startReprocessing();
  }

  async onModuleDestroy() {
    this.is_shutting_down = true;
    if (this.check_interval) {
      clearInterval(this.check_interval);
      this.check_interval = null;
    }
    await this.disconnect();
  }

  private async connect(): Promise<void> {
    try {
      const rabbitmqUrl = this.configService.get<string>(
        'RABBITMQ_URL',
        'amqp://guest:guest@localhost:5672'
      );

      this.logger.log(MSG.DLQ_REPROCESSOR_CONNECTING(rabbitmqUrl));
      this.connection = await amqp.connect(rabbitmqUrl);
      
      this.connection.on('error', (err: Error) => {
        this.logger.error('DLQ Reprocessor connection error', err);
      });

      this.connection.on('close', () => {
        this.logger.warn('DLQ Reprocessor connection closed');
      });

      this.channel = await this.connection.createConfirmChannel();

      this.channel.on('error', (err: Error) => {
        this.logger.error('DLQ Reprocessor channel error', err);
      });

      this.logger.log(MSG.DLQ_REPROCESSOR_CONNECTED);
    } catch (error) {
      this.logger.error(MSG.DLQ_REPROCESSOR_CONNECTION_FAILED, error);
      throw error;
    }
  }

  private startReprocessing(): void {
    this.logger.log(MSG.DLQ_REPROCESSOR_STARTED(DLQ_CHECK_INTERVAL_MS));

    this.check_interval = setInterval(async () => {
      if (!this.is_shutting_down) {
        await this.checkAndReprocessDLQ();
      }
    }, DLQ_CHECK_INTERVAL_MS);
  }

  private async checkAndReprocessDLQ(): Promise<void> {
    if (!this.channel) {
      this.logger.warn('Channel not available for DLQ reprocessing');
      return;
    }

    try {
      // Check if dependent services are healthy
      const servicesHealthy = await this.checkDependentServicesHealth();

      // Log only if health status changed
      if (this.lastServicesHealthy === null || this.lastServicesHealthy !== servicesHealthy) {
        if (servicesHealthy) {
          this.logger.log('DLQ reprocessing enabled: all dependent services are healthy');
        } else {
          this.logger.warn(MSG.DLQ_REPROCESSOR_SERVICES_UNHEALTHY);
        }
        this.lastServicesHealthy = servicesHealthy;
      }

      if (!servicesHealthy) {
        return;
      }

      this.logger.log(MSG.DLQ_REPROCESSOR_CHECKING);

      // Get messages from DLQ
      let processed_count = 0;
      let message = await this.channel.get(QUEUE_CONFIG.FAILED_QUEUE, { noAck: false });

      while (message && processed_count < BATCH_SIZE) {
        await this.reprocessMessage(message);
        processed_count++;
        message = await this.channel.get(QUEUE_CONFIG.FAILED_QUEUE, { noAck: false });
      }

      if (processed_count > 0) {
        this.logger.log(MSG.DLQ_REPROCESSOR_BATCH_COMPLETED(processed_count));
      }
    } catch (error) {
      this.logger.error(MSG.DLQ_REPROCESSOR_ERROR, error);
    }
  }

  private async reprocessMessage(msg: amqp.GetMessage): Promise<void> {
    if (!this.channel) {
      return;
    }

    try {
      const headers = msg.properties.headers || {};
      const dlq_retry_count = headers['x-dlq-retry-count'] || 0;

      // Check if message has exceeded DLQ reprocess attempts
      if (dlq_retry_count >= MAX_DLQ_REPROCESS_ATTEMPTS) {
        this.logger.error(
          MSG.DLQ_REPROCESSOR_MAX_ATTEMPTS_EXCEEDED(MAX_DLQ_REPROCESS_ATTEMPTS)
        );
        // Keep in DLQ for manual intervention
        this.channel.nack(msg, false, true);
        return;
      }

      // Increment DLQ retry count
      headers['x-dlq-retry-count'] = dlq_retry_count + 1;
      headers['x-dlq-reprocess-time'] = new Date().toISOString();
      // Reset main retry count for fresh processing
      headers['x-retry-count'] = 0;

      this.logger.log(
        MSG.DLQ_REPROCESSOR_REQUEUING(dlq_retry_count + 1, MAX_DLQ_REPROCESS_ATTEMPTS)
      );

      // Send back to main queue for reprocessing
      this.channel.publish(
        QUEUE_CONFIG.EXCHANGE,
        QUEUE_CONFIG.EMAIL_ROUTING_KEY,
        msg.content,
        {
          headers,
          persistent: true,
        }
      );

      // Acknowledge DLQ message
      this.channel.ack(msg);
      this.logger.log(MSG.DLQ_REPROCESSOR_MESSAGE_REQUEUED);
    } catch (error) {
      this.logger.error(MSG.DLQ_REPROCESSOR_MESSAGE_ERROR, error);
      // Requeue to DLQ for retry
      if (this.channel) {
        this.channel.nack(msg, false, true);
      }
    }
  }

  private async checkDependentServicesHealth(): Promise<boolean> {
    try {
      const [userServiceHealthy, templateServiceHealthy] = await Promise.all([
        this.userServiceClient.checkHealth().catch(() => false),
        this.templateServiceClient.checkHealth().catch(() => false),
      ]);

      const all_healthy = userServiceHealthy && templateServiceHealthy;

      if (!all_healthy) {
        this.logger.debug(
          `Service health: User=${userServiceHealthy}, Template=${templateServiceHealthy}`
        );
      }

      return all_healthy;
    } catch (error) {
      this.logger.error('Failed to check service health', error);
      return false;
    }
  }

  async disconnect(): Promise<void> {
    try {
      if (this.channel) {
        await this.channel.close();
        this.logger.log('DLQ Reprocessor channel closed');
      }

      if (this.connection) {
        await this.connection.close();
        this.logger.log('DLQ Reprocessor connection closed');
      }
    } catch (error) {
      this.logger.error('Error during DLQ Reprocessor disconnect', error);
    }
  }

  async isHealthy(): Promise<boolean> {
    return this.connection !== null && this.channel !== null;
  }
}
