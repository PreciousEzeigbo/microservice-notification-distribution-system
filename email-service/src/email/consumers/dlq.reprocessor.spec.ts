import { Test, TestingModule } from '@nestjs/testing';
import { ConfigService } from '@nestjs/config';
import { DlqReprocessor } from './dlq.reprocessor';
import { UserServiceClient } from '../http/user.service.client';
import { TemplateServiceClient } from '../http/template.service.client';
import { ApiGatewayClient } from '../http/api-gateway.client';
import { EmailProcessor } from '../processors/email.processor';
import { Channel } from 'amqplib';

describe('DlqReprocessor', () => {
  let reprocessor: DlqReprocessor;
  let userServiceClient: jest.Mocked<UserServiceClient>;
  let templateServiceClient: jest.Mocked<TemplateServiceClient>;
  let apiGatewayClient: jest.Mocked<ApiGatewayClient>;
  let emailProcessor: jest.Mocked<EmailProcessor>;
  let mockChannel: jest.Mocked<Channel>;

  beforeEach(async () => {
    mockChannel = {
      assertQueue: jest.fn(),
      get: jest.fn(),
      ack: jest.fn(),
      publish: jest.fn(),
    } as any;

    const module: TestingModule = await Test.createTestingModule({
      providers: [
        DlqReprocessor,
        {
          provide: ConfigService,
          useValue: {
            get: jest.fn((key: string) => {
              const config: Record<string, string | number> = {
                RABBITMQ_URL: 'amqp://localhost',
                DLQ_CHECK_INTERVAL_MS: '300000',
              };
              return config[key];
            }),
          },
        },
        {
          provide: UserServiceClient,
          useValue: {
            checkHealth: jest.fn(),
          },
        },
        {
          provide: TemplateServiceClient,
          useValue: {
            checkHealth: jest.fn(),
          },
        },
        {
          provide: ApiGatewayClient,
          useValue: {
            isHealthy: jest.fn(),
          },
        },
        {
          provide: EmailProcessor,
          useValue: {
            processEmail: jest.fn(),
          },
        },
      ],
    }).compile();

    reprocessor = module.get<DlqReprocessor>(DlqReprocessor);
    userServiceClient = module.get(UserServiceClient);
    templateServiceClient = module.get(TemplateServiceClient);
    apiGatewayClient = module.get(ApiGatewayClient);
    emailProcessor = module.get(EmailProcessor);

    // Mock the channel property
    (reprocessor as any).channel = mockChannel;
  });

  describe('checkDependentServicesHealth', () => {
    it('should return true when all services are healthy', async () => {
      userServiceClient.checkHealth.mockResolvedValue(true);
      templateServiceClient.checkHealth.mockResolvedValue(true);
      apiGatewayClient.isHealthy.mockResolvedValue(true);

      const result = await reprocessor['checkDependentServicesHealth']();

      expect(result).toBe(true);
    });

    it('should return false when user service is unhealthy', async () => {
      userServiceClient.checkHealth.mockResolvedValue(false);
      templateServiceClient.checkHealth.mockResolvedValue(true);
      apiGatewayClient.isHealthy.mockResolvedValue(true);

      const result = await reprocessor['checkDependentServicesHealth']();

      expect(result).toBe(false);
    });

    it('should return false when template service is unhealthy', async () => {
      userServiceClient.checkHealth.mockResolvedValue(true);
      templateServiceClient.checkHealth.mockResolvedValue(false);
      apiGatewayClient.isHealthy.mockResolvedValue(true);

      const result = await reprocessor['checkDependentServicesHealth']();

      expect(result).toBe(false);
    });

    it('should return true when only user and template services are healthy', async () => {
      userServiceClient.checkHealth.mockResolvedValue(true);
      templateServiceClient.checkHealth.mockResolvedValue(true);
      apiGatewayClient.isHealthy.mockResolvedValue(false);

      const result = await reprocessor['checkDependentServicesHealth']();

      expect(result).toBe(true);
    });

    it('should return false when all services are unhealthy', async () => {
      userServiceClient.checkHealth.mockResolvedValue(false);
      templateServiceClient.checkHealth.mockResolvedValue(false);
      apiGatewayClient.isHealthy.mockResolvedValue(false);

      const result = await reprocessor['checkDependentServicesHealth']();

      expect(result).toBe(false);
    });
  });

  describe('health status change logging', () => {
    it('should return correct health status', async () => {
      // First check - healthy
      userServiceClient.checkHealth.mockResolvedValue(true);
      templateServiceClient.checkHealth.mockResolvedValue(true);

      let result = await reprocessor['checkDependentServicesHealth']();
      expect(result).toBe(true);

      // Second check - unhealthy
      userServiceClient.checkHealth.mockResolvedValue(false);

      result = await reprocessor['checkDependentServicesHealth']();
      expect(result).toBe(false);
    });
  });
});
