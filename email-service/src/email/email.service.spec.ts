import { Test, TestingModule } from '@nestjs/testing';
import { EmailService } from './email.service';
import { EmailProcessor } from './processors/email.processor';
import { EmailConsumer } from './consumers/email.consumer';
import { SmtpEmailProvider } from './providers/smtp.provider';
import { AbstractEmailProvider } from '../shared/interfaces/email-provider.interface';
import { UserServiceClient } from './http/user.service.client';
import { TemplateServiceClient } from './http/template.service.client';
import { ApiGatewayClient } from './http/api-gateway.client';

describe('EmailService', () => {
  let service: EmailService;
  let emailConsumer: jest.Mocked<EmailConsumer>;
  let emailProcessor: jest.Mocked<EmailProcessor>;
  let smtpProvider: jest.Mocked<SmtpEmailProvider>;
  let userServiceClient: jest.Mocked<UserServiceClient>;
  let templateServiceClient: jest.Mocked<TemplateServiceClient>;
  let apiGatewayClient: jest.Mocked<ApiGatewayClient>;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        EmailService,
        {
          provide: EmailConsumer,
          useValue: {
            setMessageHandler: jest.fn(),
            startConsuming: jest.fn(),
            isHealthy: jest.fn(),
          },
        },
        {
          provide: EmailProcessor,
          useValue: {
            process: jest.fn(),
          },
        },
        {
          provide: AbstractEmailProvider,
          useValue: {
            verifyConnection: jest.fn(),
          },
        },
        {
          provide: UserServiceClient,
          useValue: {
            isHealthy: jest.fn(),
          },
        },
        {
          provide: TemplateServiceClient,
          useValue: {
            isHealthy: jest.fn(),
          },
        },
        {
          provide: ApiGatewayClient,
          useValue: {
            isHealthy: jest.fn(),
          },
        },
      ],
    }).compile();

    service = module.get<EmailService>(EmailService);
    emailConsumer = module.get(EmailConsumer);
    emailProcessor = module.get(EmailProcessor);
    smtpProvider = module.get(AbstractEmailProvider);
    userServiceClient = module.get(UserServiceClient);
    templateServiceClient = module.get(TemplateServiceClient);
    apiGatewayClient = module.get(ApiGatewayClient);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  describe('onModuleInit', () => {
    it('should set message handler and start consuming', async () => {
      await service.onModuleInit();

      expect(emailConsumer.setMessageHandler).toHaveBeenCalledWith(
        expect.any(Function),
      );
      expect(emailConsumer.startConsuming).toHaveBeenCalled();
    });
  });

  describe('getHealth', () => {
    it('should return healthy status when all services are healthy', async () => {
      emailConsumer.isHealthy.mockReturnValue(true);
      smtpProvider.verifyConnection.mockResolvedValue(true);
      userServiceClient.isHealthy.mockResolvedValue(true);
      templateServiceClient.isHealthy.mockResolvedValue(true);
      apiGatewayClient.isHealthy.mockResolvedValue(true);

      const result = await service.getHealth();

      expect(result.healthy).toBe(true);
      expect(result.degraded).toBe(false);
      expect(result.unhealthy_dependencies).toEqual([]);
      expect(result.details.service).toBe('email-service');
    });

    it('should return degraded status when external services are unhealthy', async () => {
      emailConsumer.isHealthy.mockReturnValue(true);
      smtpProvider.verifyConnection.mockResolvedValue(true);
      userServiceClient.isHealthy.mockResolvedValue(false);
      templateServiceClient.isHealthy.mockResolvedValue(true);
      apiGatewayClient.isHealthy.mockResolvedValue(true);

      const result = await service.getHealth();

      expect(result.healthy).toBe(true);
      expect(result.degraded).toBe(true);
      expect(result.unhealthy_dependencies).toContain('user_service');
    });

    it('should return unhealthy status when critical services fail', async () => {
      emailConsumer.isHealthy.mockReturnValue(false);
      smtpProvider.verifyConnection.mockResolvedValue(true);
      userServiceClient.isHealthy.mockResolvedValue(true);
      templateServiceClient.isHealthy.mockResolvedValue(true);
      apiGatewayClient.isHealthy.mockResolvedValue(true);

      const result = await service.getHealth();

      expect(result.healthy).toBe(false);
      expect(result.unhealthy_dependencies).toContain('rabbitmq');
    });

    it('should return unhealthy status when SMTP fails', async () => {
      emailConsumer.isHealthy.mockReturnValue(true);
      smtpProvider.verifyConnection.mockResolvedValue(false);
      userServiceClient.isHealthy.mockResolvedValue(true);
      templateServiceClient.isHealthy.mockResolvedValue(true);
      apiGatewayClient.isHealthy.mockResolvedValue(true);

      const result = await service.getHealth();

      expect(result.healthy).toBe(false);
      expect(result.unhealthy_dependencies).toContain('smtp');
    });

    it('should return all unhealthy dependencies', async () => {
      emailConsumer.isHealthy.mockReturnValue(false);
      smtpProvider.verifyConnection.mockResolvedValue(false);
      userServiceClient.isHealthy.mockResolvedValue(false);
      templateServiceClient.isHealthy.mockResolvedValue(false);
      apiGatewayClient.isHealthy.mockResolvedValue(false);

      const result = await service.getHealth();

      expect(result.healthy).toBe(false);
      expect(result.unhealthy_dependencies).toEqual([
        'rabbitmq',
        'smtp',
        'user_service',
        'template_service',
        'api_gateway',
      ]);
    });

    it('should return snake_case formatted response', async () => {
      emailConsumer.isHealthy.mockReturnValue(true);
      smtpProvider.verifyConnection.mockResolvedValue(true);
      userServiceClient.isHealthy.mockResolvedValue(true);
      templateServiceClient.isHealthy.mockResolvedValue(true);
      apiGatewayClient.isHealthy.mockResolvedValue(true);

      const result = await service.getHealth();

      expect(result).toHaveProperty('unhealthy_dependencies');
      expect(result.details).toHaveProperty('external_services');
      expect(result.details.external_services).toHaveProperty('user_service');
      expect(result.details.external_services).toHaveProperty(
        'template_service',
      );
      expect(result.details.external_services).toHaveProperty('api_gateway');
    });
  });
});
