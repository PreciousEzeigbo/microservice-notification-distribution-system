import { Module } from '@nestjs/common';
import { HttpModule } from '@nestjs/axios';
import { ConfigModule } from '@nestjs/config';
import { EmailService } from './email.service';
import { EmailController } from './email.controller';
import { EmailConsumer } from './consumers/email.consumer';
import { DlqReprocessor } from './consumers/dlq.reprocessor';
import { EmailProcessor } from './processors/email.processor';
import { UserServiceClient } from './http/user.service.client';
import { TemplateServiceClient } from './http/template.service.client';
import { ApiGatewayClient } from './http/api-gateway.client';
import { SmtpEmailProvider } from './providers/smtp.provider';
import { AbstractEmailProvider } from '../shared/interfaces/email-provider.interface';

@Module({
  imports: [
    HttpModule.register({
      timeout: 10000,
      maxRedirects: 5,
    }),
    ConfigModule,
  ],
  controllers: [EmailController],
  providers: [
    EmailService,
    EmailConsumer,
    DlqReprocessor,
    EmailProcessor,
    UserServiceClient,
    TemplateServiceClient,
    ApiGatewayClient,
    {
      provide: AbstractEmailProvider,
      useClass: SmtpEmailProvider,
    },
  ],
  exports: [EmailService],
})
export class EmailModule {}
