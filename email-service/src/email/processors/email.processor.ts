import { Injectable, Logger, BadRequestException } from '@nestjs/common';
import {
  NotificationMessage,
  NotificationStatus,
} from '../../shared/interfaces/notification-message.interface';
import { UserServiceClient } from '../http/user.service.client';
import { TemplateServiceClient } from '../http/template.service.client';
import { ApiGatewayClient } from '../http/api-gateway.client';
import { AbstractEmailProvider } from '../../shared/interfaces/email-provider.interface';
import { MessageValidationException } from '../../common/exceptions/message-validation.exception';
import * as Handlebars from 'handlebars';
import * as MSG from '../../constants/system.messages';

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
    this.logger.log(
      `${MSG.CORRELATION_PREFIX(correlationId)} ${MSG.EMAIL_PROCESSING_STARTED}: ${message.message_id}`,
    );

    try {
      // 1. Validate message and fetch template (cached for reuse)
      const template = await this.validateMessage(message);

      // 2. Fetch user details
      this.logger.log(
        `${MSG.CORRELATION_PREFIX(correlationId)} ${MSG.USER_SERVICE_FETCHING(message.user_id)}`,
      );
      const user = await this.userServiceClient.getUser(message.user_id);

      // 3. Check user preferences (with null safety)
      if (!user.preferences?.email) {
        this.logger.warn(
          `${MSG.CORRELATION_PREFIX(correlationId)} ${MSG.USER_DISABLED_EMAIL_NOTIFICATIONS(message.user_id)}`,
        );
        await this.apiGatewayClient.updateStatus({
          notification_id: message.message_id,
          status: NotificationStatus.SKIPPED,
          timestamp: new Date().toISOString(),
          error: MSG.USER_DISABLED_EMAIL_NOTIFICATIONS(message.user_id),
        });
        return;
      }

      // 4. Template already fetched during validation

      // 5. Compile template with variables
      this.logger.log(
        `${MSG.CORRELATION_PREFIX(correlationId)} ${MSG.TEMPLATE_COMPILING}`,
      );
      const compiledSubject = this.compileTemplate(
        template.subject,
        message.variables,
      );
      const compiledBody = this.compileTemplate(
        template.body,
        message.variables,
      );
      const compiledText = template.text_version
        ? this.compileTemplate(template.text_version, message.variables)
        : undefined;

      // 6. Send email
      this.logger.log(
        `${MSG.CORRELATION_PREFIX(correlationId)} ${MSG.SMTP_SENDING_EMAIL(user.email)}`,
      );
      const result = await this.emailProvider.sendEmail({
        to: user.email,
        subject: compiledSubject,
        html: compiledBody,
        text: compiledText,
      });

      if (!result.success) {
        throw new Error(`${MSG.EMAIL_SENDING_FAILED}: ${result.error}`);
      }

      // 7. Update status to delivered
      this.logger.log(
        `${MSG.CORRELATION_PREFIX(correlationId)} ${MSG.EMAIL_SENT_SUCCESSFULLY}`,
      );
      await this.apiGatewayClient.updateStatus({
        notification_id: message.message_id,
        status: NotificationStatus.DELIVERED,
        timestamp: new Date().toISOString(),
        provider_response: result,
      });

      this.logger.log(
        `${MSG.CORRELATION_PREFIX(correlationId)} ${MSG.EMAIL_PROCESSING_COMPLETED}`,
      );
    } catch (error) {
      this.logger.error(
        `${MSG.CORRELATION_PREFIX(correlationId)} ${MSG.EMAIL_PROCESSING_FAILED}`,
        error,
      );

      // Update status to failed
      await this.apiGatewayClient
        .updateStatus({
          notification_id: message.message_id,
          status: NotificationStatus.FAILED,
          timestamp: new Date().toISOString(),
          error: error instanceof Error ? error.message : MSG.UNKNOWN_ERROR,
        })
        .catch((statusError) => {
          this.logger.error(
            `${MSG.CORRELATION_PREFIX(correlationId)} ${MSG.API_GATEWAY_STATUS_UPDATE_FAILED(message.message_id)}`,
            statusError,
          );
        });

      throw error;
    }
  }

  private async validateMessage(message: NotificationMessage) {
    const required = [
      'message_id',
      'request_id',
      'user_id',
      'template_code',
      'variables',
    ];
    const missing = required.filter(
      (field) => !message[field as keyof NotificationMessage],
    );

    if (missing.length > 0) {
      throw new MessageValidationException(missing);
    }

    // Fetch template to extract required placeholders (return it to avoid duplicate fetch)
    const template = await this.templateServiceClient.getTemplate(
      message.template_code,
    );
    const placeholders = this.extractPlaceholders(template.subject).concat(
      this.extractPlaceholders(template.body),
    );
    if (template.text_version) {
      placeholders.push(...this.extractPlaceholders(template.text_version));
    }
    const uniquePlaceholders = Array.from(new Set(placeholders));
    const missingVars = uniquePlaceholders.filter(
      (ph) => !(ph in message.variables),
    );
    if (missingVars.length > 0) {
      throw new MessageValidationException(missingVars);
    }

    return template;
  }

  // Extract Handlebars-style {{variable}} placeholders from a template string
  private extractPlaceholders(template: string): string[] {
    if (!template) return [];
    const regex = /{{\s*([\w.]+)\s*}}/g;
    const matches = [];
    let match;
    while ((match = regex.exec(template)) !== null) {
      matches.push(match[1]);
    }
    return matches;
  }

  private compileTemplate(
    template: string,
    variables: Record<string, unknown>,
  ): string {
    try {
      const compiledTemplate = Handlebars.compile(template);
      return compiledTemplate(variables);
    } catch (error) {
      this.logger.error(MSG.TEMPLATE_COMPILATION_FAILED, error);
      throw new BadRequestException(
        MSG.TEMPLATE_COMPILATION_ERROR(
          error instanceof Error ? error.message : MSG.UNKNOWN_ERROR,
        ),
      );
    }
  }
}
