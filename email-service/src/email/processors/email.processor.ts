import { Injectable, Logger } from '@nestjs/common';
import { NotificationMessage, NotificationStatus } from '../../shared/interfaces/notification-message.interface';
import { UserServiceClient } from '../http/user.service.client';
import { TemplateServiceClient } from '../http/template.service.client';
import { ApiGatewayClient } from '../http/api-gateway.client';
import { AbstractEmailProvider } from '../../shared/interfaces/email-provider.interface';
import * as Handlebars from 'handlebars';

@Injectable()
export class EmailProcessor {
  private readonly logger = new Logger(EmailProcessor.name);

  constructor(
    private readonly userServiceClient: UserServiceClient,
    private readonly templateServiceClient: TemplateServiceClient,
    private readonly apiGatewayClient: ApiGatewayClient,
    private readonly emailProvider: AbstractEmailProvider,
  ) {}

  async process(message: NotificationMessage): Promise<void> {
    const correlationId = message.correlation_id || message.message_id;
    this.logger.log(`[${correlationId}] Processing email notification: ${message.message_id}`);

    try {
      // 1. Validate message
      this.validateMessage(message);

      // 2. Fetch user details
      this.logger.log(`[${correlationId}] Fetching user details for user: ${message.user_id}`);
      const user = await this.userServiceClient.getUser(message.user_id);

      // 3. Check user preferences
      if (!user.preferences.email) {
        this.logger.warn(`[${correlationId}] User ${message.user_id} has disabled email notifications`);
        await this.apiGatewayClient.updateStatus({
          notification_id: message.message_id,
          status: NotificationStatus.DELIVERED,
          timestamp: new Date().toISOString(),
          error: 'User has disabled email notifications',
        });
        return;
      }

      // 4. Fetch template
      this.logger.log(`[${correlationId}] Fetching template: ${message.template_code}`);
      const template = await this.templateServiceClient.getTemplate(message.template_code);

      // 5. Compile template with variables
      this.logger.log(`[${correlationId}] Compiling template with variables`);
      const compiledSubject = this.compileTemplate(template.subject, message.variables);
      const compiledBody = this.compileTemplate(template.body, message.variables);
      const compiledText = template.text_version
        ? this.compileTemplate(template.text_version, message.variables)
        : undefined;

      // 6. Send email
      this.logger.log(`[${correlationId}] Sending email to: ${user.email}`);
      const result = await this.emailProvider.sendEmail({
        to: user.email,
        subject: compiledSubject,
        html: compiledBody,
        text: compiledText,
      });

      if (!result.success) {
        throw new Error(`Email sending failed: ${result.error}`);
      }

      // 7. Update status to delivered
      this.logger.log(`[${correlationId}] Email sent successfully`);
      await this.apiGatewayClient.updateStatus({
        notification_id: message.message_id,
        status: NotificationStatus.DELIVERED,
        timestamp: new Date().toISOString(),
        provider_response: result,
      });

      this.logger.log(`[${correlationId}] Email notification processed successfully`);
    } catch (error) {
      this.logger.error(`[${correlationId}] Failed to process email notification`, error);

      // Update status to failed
      await this.apiGatewayClient.updateStatus({
        notification_id: message.message_id,
        status: NotificationStatus.FAILED,
        timestamp: new Date().toISOString(),
        error: error instanceof Error ? error.message : 'Unknown error',
      }).catch((statusError) => {
        this.logger.error(`[${correlationId}] Failed to update status`, statusError);
      });

      throw error;
    }
  }

  private validateMessage(message: NotificationMessage): void {
    const required = ['message_id', 'request_id', 'user_id', 'template_code', 'variables'];
    const missing = required.filter((field) => !message[field as keyof NotificationMessage]);

    if (missing.length > 0) {
      throw new Error(`Missing required fields: ${missing.join(', ')}`);
    }
  }

  private compileTemplate(template: string, variables: Record<string, unknown>): string {
    try {
      const compiledTemplate = Handlebars.compile(template);
      return compiledTemplate(variables);
    } catch (error) {
      this.logger.error('Template compilation failed', error);
      throw new Error(`Template compilation error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }
}
