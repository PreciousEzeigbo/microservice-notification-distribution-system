import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import * as nodemailer from 'nodemailer';
import {
  AbstractEmailProvider,
  EmailPayload,
  EmailResult,
} from '../../shared/interfaces/email-provider.interface';
import * as MSG from '../../constants/system.messages';

@Injectable()
export class SmtpEmailProvider extends AbstractEmailProvider {
  private readonly logger = new Logger(SmtpEmailProvider.name);
  private transporter: nodemailer.Transporter;

  constructor(private readonly configService: ConfigService) {
    super();
    this.initializeTransporter();
  }

  private initializeTransporter(): void {
    const port = this.configService.get<number>('SMTP_PORT', 465);
    const secure = this.configService.get<boolean>('SMTP_SECURE', true);

    const config = {
      host: this.configService.get<string>('SMTP_HOST', 'smtp.gmail.com'),
      port,
      secure, // true for 465 (implicit SSL), false for 587 (STARTTLS)
      auth: {
        user: this.configService.get<string>('SMTP_USER'),
        pass: this.configService.get<string>('SMTP_PASSWORD'),
      },
      // Only require TLS upgrade for port 587
      requireTLS: !secure && port === 587,
      tls: {
        // Reject unauthorized certs in production for security
        rejectUnauthorized:
          this.configService.get<string>('NODE_ENV') === 'production',
      },
      connectionTimeout: 5000,
      greetingTimeout: 5000,
      socketTimeout: 5000,
    };

    this.transporter = nodemailer.createTransport(config);

    // Verify connection configuration (non-blocking)
    this.transporter.verify((error, success) => {
      if (error) {
        this.logger.error(MSG.SMTP_CONNECTION_VERIFICATION_FAILED, error);
      } else {
        this.logger.log(MSG.SMTP_CONNECTION_VERIFIED);
      }
    });
  }

  async sendEmail(payload: EmailPayload): Promise<EmailResult> {
    try {
      const from =
        payload.from ||
        this.configService.get<string>(
          'SMTP_FROM_EMAIL',
          'noreply@example.com',
        );

      const mailOptions: nodemailer.SendMailOptions = {
        from,
        to: payload.to,
        subject: payload.subject,
        html: payload.html,
        text: payload.text,
        replyTo: payload.reply_to,
        attachments: payload.attachments,
      };

      this.logger.log(MSG.SMTP_SENDING_EMAIL(payload.to));
      const info = await this.transporter.sendMail(mailOptions);

      this.logger.log(MSG.SMTP_EMAIL_SENT(info.messageId));

      return {
        success: true,
        message_id: info.messageId,
        provider: this.getName(),
      };
    } catch (error) {
      this.logger.error(MSG.SMTP_SEND_FAILED, error);

      return {
        success: false,
        error: error instanceof Error ? error.message : 'unknown_smtp_error',
        provider: this.getName(),
      };
    }
  }

  async verifyConnection(): Promise<boolean> {
    try {
      // Add timeout to prevent hanging health checks
      const verifyPromise = this.transporter.verify();
      const timeoutPromise = new Promise<never>((_, reject) =>
        setTimeout(() => reject(new Error('SMTP verification timeout')), 5000),
      );

      await Promise.race([verifyPromise, timeoutPromise]);
      return true;
    } catch (error) {
      this.logger.error(MSG.SMTP_CONNECTION_VERIFICATION_FAILED, error);
      return false;
    }
  }

  getName(): string {
    return 'SMTP';
  }
}
