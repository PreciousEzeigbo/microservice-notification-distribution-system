import { Injectable, Logger, OnModuleInit } from '@nestjs/common';
import { EmailConsumer } from './consumers/email.consumer';
import { EmailProcessor } from './processors/email.processor';
import { AbstractEmailProvider } from '../shared/interfaces/email-provider.interface';
import { UserServiceClient } from './http/user.service.client';
import { TemplateServiceClient } from './http/template.service.client';
import { ApiGatewayClient } from './http/api-gateway.client';

@Injectable()
export class EmailService implements OnModuleInit {
  private readonly logger = new Logger(EmailService.name);

  constructor(
    private readonly emailConsumer: EmailConsumer,
    private readonly emailProcessor: EmailProcessor,
    private readonly emailProvider: AbstractEmailProvider,
    private readonly userServiceClient: UserServiceClient,
    private readonly templateServiceClient: TemplateServiceClient,
    private readonly apiGatewayClient: ApiGatewayClient,
  ) {}

  async onModuleInit() {
    this.logger.log('Initializing Email Service...');

    // Set the message handler
    this.emailConsumer.setMessageHandler(async (message) => {
      await this.emailProcessor.process(message);
    });

    // Start consuming messages
    await this.emailConsumer.startConsuming();

    this.logger.log('Email service initialized and consuming messages');
  }

  async getHealth(): Promise<{
    service: string;
    rabbitmq: boolean;
    smtp: boolean;
    externalServices: {
      userService: boolean;
      templateService: boolean;
      apiGateway: boolean;
    };
  }> {
    return {
      service: 'email-service',
      rabbitmq: await this.emailConsumer.isHealthy(),
      smtp: await this.emailProvider.verifyConnection(),
      externalServices: {
        userService: await this.userServiceClient.isHealthy(),
        templateService: await this.templateServiceClient.isHealthy(),
        apiGateway: await this.apiGatewayClient.isHealthy(),
      },
    };
  }
}
