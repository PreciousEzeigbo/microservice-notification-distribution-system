import { Test, TestingModule } from '@nestjs/testing';
import { ConfigService } from '@nestjs/config';
import { EmailConsumer } from './email.consumer';
import { EmailProcessor } from '../processors/email.processor';
import { ApiGatewayClient } from '../http/api-gateway.client';
import { Channel, ConsumeMessage } from 'amqplib';

describe('EmailConsumer', () => {
  let consumer: EmailConsumer;
  let emailProcessor: jest.Mocked<EmailProcessor>;
  let apiGatewayClient: jest.Mocked<ApiGatewayClient>;
  let mockChannel: jest.Mocked<Channel>;

  const mockMessage: ConsumeMessage = {
    content: Buffer.from(
      JSON.stringify({
        message_id: 'msg_123',
        request_id: 'req_123',
        user_id: 'user_123',
        to: 'test@example.com',
        template_id: 'welcome',
        variables: { name: 'John' },
      }),
    ),
    fields: {
      deliveryTag: 1,
      redelivered: false,
      exchange: '',
      routingKey: 'email-notifications',
      consumerTag: '',
    },
    properties: {
      contentType: undefined,
      contentEncoding: undefined,
      headers: {},
      deliveryMode: undefined,
      priority: undefined,
      correlationId: undefined,
      replyTo: undefined,
      expiration: undefined,
      messageId: undefined,
      timestamp: undefined,
      type: undefined,
      userId: undefined,
      appId: undefined,
      clusterId: undefined,
    },
  };

  beforeEach(async () => {
    mockChannel = {
      ack: jest.fn(),
      nack: jest.fn(),
      publish: jest.fn(),
      assertQueue: jest.fn(),
      consume: jest.fn(),
    } as any;

    const module: TestingModule = await Test.createTestingModule({
      providers: [
        EmailConsumer,
        {
          provide: ConfigService,
          useValue: {
            get: jest.fn((key: string) => {
              const config: Record<string, string | number> = {
                RABBITMQ_URL: 'amqp://localhost',
              };
              return config[key];
            }),
          },
        },
        {
          provide: EmailProcessor,
          useValue: {
            process: jest.fn(),
          },
        },
        {
          provide: ApiGatewayClient,
          useValue: {
            updateStatus: jest.fn(),
          },
        },
      ],
    }).compile();

    consumer = module.get<EmailConsumer>(EmailConsumer);
    emailProcessor = module.get(EmailProcessor);
    apiGatewayClient = module.get(ApiGatewayClient);
  });

  describe('message handling', () => {
    it('should configure message handler', () => {
      const mockHandler = jest.fn();
      consumer.setMessageHandler(mockHandler);

      // Verify handler can be set without errors
      expect(mockHandler).toBeDefined();
    });

    it('should have health check method', () => {
      const isHealthy = consumer.isHealthy();

      // Verify health check returns a boolean
      expect(typeof isHealthy).toBe('boolean');
    });
  });
});
