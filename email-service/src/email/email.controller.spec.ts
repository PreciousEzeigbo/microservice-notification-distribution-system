import { Test, TestingModule } from '@nestjs/testing';
import { EmailController } from './email.controller';
import { EmailService } from './email.service';
import { UserServiceClient } from './http/user.service.client';
import { TemplateServiceClient } from './http/template.service.client';
import { ApiGatewayClient } from './http/api-gateway.client';
import { SmtpEmailProvider } from './providers/smtp.provider';

describe('EmailController', () => {
  let controller: EmailController;
  let emailService: jest.Mocked<EmailService>;
  let userServiceClient: jest.Mocked<UserServiceClient>;
  let templateServiceClient: jest.Mocked<TemplateServiceClient>;
  let apiGatewayClient: jest.Mocked<ApiGatewayClient>;
  let smtpProvider: jest.Mocked<SmtpEmailProvider>;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [EmailController],
      providers: [
        {
          provide: EmailService,
          useValue: {
            getHealth: jest.fn(),
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
        {
          provide: SmtpEmailProvider,
          useValue: {
            onModuleInit: jest.fn(),
          },
        },
      ],
    }).compile();

    controller = module.get<EmailController>(EmailController);
    emailService = module.get(EmailService);
    userServiceClient = module.get(UserServiceClient);
    templateServiceClient = module.get(TemplateServiceClient);
    apiGatewayClient = module.get(ApiGatewayClient);
    smtpProvider = module.get(SmtpEmailProvider);
  });

  it('should be defined', () => {
    expect(controller).toBeDefined();
  });

  describe('checkHealth', () => {
    it('should return health status with all services healthy', async () => {
      const mockHealth = {
        healthy: true,
        degraded: false,
        unhealthy_dependencies: [],
        details: {
          service: 'email-service',
          rabbitmq: true,
          smtp: true,
          external_services: {
            user_service: true,
            template_service: true,
            api_gateway: true,
          },
          timestamp: new Date().toISOString(),
        },
      };

      jest.spyOn(emailService, 'getHealth').mockResolvedValue(mockHealth);

      const mockRes = {
        status: jest.fn().mockReturnThis(),
        json: jest.fn().mockReturnValue({
          status_code: 200,
          message: 'Email service is healthy',
          data: expect.any(Object),
        }),
      } as any;

      await controller.checkHealth(mockRes);

      expect(mockRes.status).toHaveBeenCalledWith(200);
      expect(mockRes.json).toHaveBeenCalled();
    });

    it('should return health status with some services unhealthy', async () => {
      const mockHealth = {
        healthy: true,
        degraded: true,
        unhealthy_dependencies: ['user_service'],
        details: {
          service: 'email-service',
          rabbitmq: true,
          smtp: true,
          external_services: {
            user_service: false,
            template_service: true,
            api_gateway: true,
          },
          timestamp: new Date().toISOString(),
        },
      };

      jest.spyOn(emailService, 'getHealth').mockResolvedValue(mockHealth);

      const mockRes = {
        status: jest.fn().mockReturnThis(),
        json: jest.fn(),
      } as any;

      await controller.checkHealth(mockRes);

      expect(mockRes.status).toHaveBeenCalled();
      expect(mockRes.json).toHaveBeenCalled();
    });

    it('should return snake_case formatted response', async () => {
      const mockHealth = {
        healthy: true,
        degraded: false,
        unhealthy_dependencies: [],
        details: {
          service: 'email-service',
          rabbitmq: true,
          smtp: true,
          external_services: {
            user_service: true,
            template_service: true,
            api_gateway: true,
          },
          timestamp: new Date().toISOString(),
        },
      };

      jest.spyOn(emailService, 'getHealth').mockResolvedValue(mockHealth);

      const mockRes = {
        status: jest.fn().mockReturnThis(),
        json: jest.fn().mockImplementation((data) => data),
      } as any;

      await controller.checkHealth(mockRes);
      const result = mockRes.json.mock.calls[0][0];

      // Check that all keys are in snake_case
      expect(result).toHaveProperty('status_code');
      expect(result).toHaveProperty('message');
      expect(result).toHaveProperty('data');
    });
  });
});
