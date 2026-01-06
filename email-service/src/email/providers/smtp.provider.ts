import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import * as nodemailer from 'nodemailer';
import { AbstractEmailProvider, EmailPayload, EmailResult } from '../../shared/interfaces/email-provider.interface';

@Injectable()
export class SmtpEmailProvider extends AbstractEmailProvider {
  private readonly logger = new Logger(SmtpEmailProvider.name);
  private transporter: nodemailer.Transporter;

  constructor(private readonly configService: ConfigService) {
    super();
    this.initializeTransporter();
  }

  private initializeTransporter(): void {
    const config = {
      host: this.configService.get<string>('SMTP_HOST', 'smtp.gmail.com'),
      port: this.configService.get<number>('SMTP_PORT', 587),
      secure: this.configService.get<boolean>('SMTP_SECURE', false), // true for 465, false for other ports
      auth: {
        user: this.configService.get<string>('SMTP_USER'),
        pass: this.configService.get<string>('SMTP_PASSWORD'),
      },
    };

    this.transporter = nodemailer.createTransport(config);

    // Verify connection configuration
    this.transporter.verify((error, success) => {
      if (error) {
        this.logger.error('SMTP connection verification failed', error);
      } else {
        this.logger.log('SMTP server is ready to send emails');
      }
    });
  }

  async sendEmail(payload: EmailPayload): Promise<EmailResult> {
    try {
      const from = payload.from || this.configService.get<string>('SMTP_FROM_EMAIL', 'noreply@example.com');
      
      const mailOptions: nodemailer.SendMailOptions = {
        from,
        to: payload.to,
        subject: payload.subject,
        html: payload.html,
        text: payload.text,
        replyTo: payload.replyTo,
        attachments: payload.attachments,
      };

      this.logger.log(`Sending email to ${payload.to} via SMTP`);
      const info = await this.transporter.sendMail(mailOptions);

      this.logger.log(`Email sent successfully: ${info.messageId}`);

      return {
        success: true,
        messageId: info.messageId,
        provider: this.getName(),
      };
    } catch (error) {
      this.logger.error('Failed to send email via SMTP', error);
      
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown SMTP error',
        provider: this.getName(),
      };
    }
  }

  async verifyConnection(): Promise<boolean> {
    try {
      await this.transporter.verify();
      return true;
    } catch (error) {
      this.logger.error('SMTP connection verification failed', error);
      return false;
    }
  }

  getName(): string {
    return 'SMTP';
  }
}
