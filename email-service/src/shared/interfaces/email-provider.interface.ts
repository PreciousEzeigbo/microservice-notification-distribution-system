export interface EmailProviderConfig {
  from: string;
  replyTo?: string;
}

export interface EmailAttachment {
  filename: string;
  content?: string | Buffer;
  path?: string;
  contentType?: string;
  cid?: string;
}

export interface EmailPayload {
  to: string;
  subject: string;
  html: string;
  text?: string;
  from?: string;
  replyTo?: string;
  attachments?: EmailAttachment[];
}

export interface EmailResult {
  success: boolean;
  messageId?: string;
  error?: string;
  provider: string;
  [key: string]: string | number | boolean | undefined;
}

export abstract class AbstractEmailProvider {
  abstract sendEmail(payload: EmailPayload): Promise<EmailResult>;
  abstract verifyConnection(): Promise<boolean>;
  abstract getName(): string;
}
