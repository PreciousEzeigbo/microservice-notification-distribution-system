import { Test, TestingModule } from '@nestjs/testing';
import { ConfigService } from '@nestjs/config';
import { SmtpEmailProvider } from './smtp.provider';
import * as nodemailer from 'nodemailer';

jest.mock('nodemailer');

describe('SmtpEmailProvider', () => {
  let provider: SmtpEmailProvider;
  let mockTransporter: any;

  beforeEach(async () => {
    mockTransporter = {
      verify: jest.fn(),
      sendMail: jest.fn(),
    };

    (nodemailer.createTransport as jest.Mock).mockReturnValue(mockTransporter);

    const module: TestingModule = await Test.createTestingModule({
      providers: [
        SmtpEmailProvider,
        {
          provide: ConfigService,
          useValue: {
            get: jest.fn((key: string) => {
              const config: Record<string, string> = {
                SMTP_HOST: 'smtp.gmail.com',
                SMTP_PORT: '587',
                SMTP_USER: 'test@example.com',
                SMTP_PASSWORD: 'password',
                SMTP_FROM_EMAIL: 'noreply@example.com',
              };
              return config[key];
            }),
          },
        },
      ],
    }).compile();

    provider = module.get<SmtpEmailProvider>(SmtpEmailProvider);
  });

  describe('verifyConnection', () => {
    it('should verify SMTP connection successfully', async () => {
      mockTransporter.verify.mockResolvedValue(true);

      const result = await provider.verifyConnection();

      expect(result).toBe(true);
      expect(mockTransporter.verify).toHaveBeenCalled();
    });

    it('should handle SMTP connection failure', async () => {
      mockTransporter.verify.mockRejectedValue(new Error('Connection failed'));

      const result = await provider.verifyConnection();

      expect(result).toBe(false);
    });
  });

  describe('sendEmail', () => {
    it('should send email successfully', async () => {
      const emailData = {
        to: 'recipient@example.com',
        subject: 'Test Email',
        text: 'Plain text body',
        html: '<p>HTML body</p>',
      };

      const mockResult = {
        messageId: 'msg_123',
        accepted: ['recipient@example.com'],
        rejected: [],
      };

      mockTransporter.sendMail.mockResolvedValue(mockResult);

      const result = await provider.sendEmail(emailData);

      expect(result).toEqual({
        success: true,
        message_id: 'msg_123',
        provider: 'SMTP',
      });
      expect(mockTransporter.sendMail).toHaveBeenCalledWith({
        from: 'noreply@example.com',
        to: 'recipient@example.com',
        subject: 'Test Email',
        text: 'Plain text body',
        html: '<p>HTML body</p>',
      });
    });

    it('should handle send email failure', async () => {
      const emailData = {
        to: 'recipient@example.com',
        subject: 'Test Email',
        text: 'Plain text body',
        html: '<p>HTML body</p>',
      };

      mockTransporter.sendMail.mockRejectedValue(
        new Error('SMTP server error'),
      );

      const result = await provider.sendEmail(emailData);

      expect(result.success).toBe(false);
      expect(result.error).toContain('SMTP server error');
    });

    it('should send email with only plain text body', async () => {
      const emailData = {
        to: 'recipient@example.com',
        subject: 'Test Email',
        text: 'Plain text body',
        html: '',
      };

      mockTransporter.sendMail.mockResolvedValue({ messageId: 'msg_123' });

      await provider.sendEmail(emailData);

      expect(mockTransporter.sendMail).toHaveBeenCalledWith(
        expect.objectContaining({
          text: 'Plain text body',
          html: '',
        }),
      );
    });
  });
});
