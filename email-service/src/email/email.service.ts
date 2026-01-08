import { Injectable, Logger, OnModuleInit } from '@nestjs/common';
import { EmailConsumer } from './consumers/email.consumer';
import { EmailProcessor } from './processors/email.processor';
import { AbstractEmailProvider } from '../shared/interfaces/email-provider.interface';
import { UserServiceClient } from './http/user.service.client';
import { TemplateServiceClient } from './http/template.service.client';
import { ApiGatewayClient } from './http/api-gateway.client';
import * as MSG from '../constants/system.messages';

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
    this.logger.log(MSG.EMAIL_SERVICE_INITIALIZING);

    // Ensure consumer is connected before starting (call connect explicitly)
    await this.emailConsumer['connect']();

    // Set the message handler
    this.emailConsumer.setMessageHandler(async (message) => {
      await this.emailProcessor.process(message);
    });

    // Start consuming messages
    await this.emailConsumer.startConsuming();

    this.logger.log(MSG.EMAIL_SERVICE_INITIALIZED);
  }

  async getHealth() {
    // Run all health checks in parallel for faster response
    const [
      rabbitmqHealthy,
      smtpHealthy,
      userServiceHealthy,
      templateServiceHealthy,
      apiGatewayHealthy,
    ] = await Promise.all([
      this.emailConsumer.isHealthy(),
      this.emailProvider.verifyConnection(),
      this.userServiceClient.isHealthy(),
      this.templateServiceClient.isHealthy(),
      this.apiGatewayClient.isHealthy(),
    ]);

    const unhealthyDependencies: string[] = [];

    // Critical dependencies
    if (!rabbitmqHealthy) unhealthyDependencies.push('rabbitmq');
    if (!smtpHealthy) unhealthyDependencies.push('smtp');

    // External services (non-critical)
    if (!userServiceHealthy) unhealthyDependencies.push('user_service');
    if (!templateServiceHealthy) unhealthyDependencies.push('template_service');
    if (!apiGatewayHealthy) unhealthyDependencies.push('api_gateway');

    const criticalServicesHealthy = rabbitmqHealthy && smtpHealthy;
    const allServicesHealthy =
      criticalServicesHealthy &&
      userServiceHealthy &&
      templateServiceHealthy &&
      apiGatewayHealthy;

    return {
      healthy: criticalServicesHealthy,
      degraded: criticalServicesHealthy && !allServicesHealthy,
      unhealthy_dependencies: unhealthyDependencies,
      details: {
        service: 'email-service',
        rabbitmq: rabbitmqHealthy,
        smtp: smtpHealthy,
        external_services: {
          user_service: userServiceHealthy,
          template_service: templateServiceHealthy,
          api_gateway: apiGatewayHealthy,
        },
        timestamp: new Date().toISOString(),
      },
    };
  }
}
