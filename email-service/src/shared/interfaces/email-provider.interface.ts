export interface EmailProviderConfig {
  from: string;
  reply_to?: string;
}

export interface EmailAttachment {
  filename: string;
  content?: string | Buffer;
  path?: string;
  content_type?: string;
  cid?: string;
}

export interface EmailPayload {
  to: string;
  subject: string;
  html: string;
  text?: string;
  from?: string;
  reply_to?: string;
  attachments?: EmailAttachment[];
}

export interface EmailResult {
  success: boolean;
  message_id?: string;
  error?: string;
  provider: string;
  [key: string]: string | number | boolean | undefined;
}

export abstract class AbstractEmailProvider {
  abstract sendEmail(payload: EmailPayload): Promise<EmailResult>;
  abstract verifyConnection(): Promise<boolean>;
  abstract getName(): string;
}
