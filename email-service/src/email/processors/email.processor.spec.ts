import { Test, TestingModule } from '@nestjs/testing';
import { EmailProcessor } from './email.processor';
import { UserServiceClient } from '../http/user.service.client';
import { TemplateServiceClient } from '../http/template.service.client';
import { ApiGatewayClient } from '../http/api-gateway.client';
import { AbstractEmailProvider } from '../../shared/interfaces/email-provider.interface';
import { MessageValidationException } from '../../common/exceptions/message-validation.exception';
import { ServiceUnavailableException } from '../../common/exceptions/service-unavailable.exception';
import { NotificationType } from '../../shared/interfaces/notification-message.interface';

describe('EmailProcessor', () => {
  let processor: EmailProcessor;
  let userServiceClient: jest.Mocked<UserServiceClient>;
  let templateServiceClient: jest.Mocked<TemplateServiceClient>;

  const mockMessage = {
    message_id: 'msg_123',
    request_id: 'req_123',
    notification_type: NotificationType.EMAIL,
    user_id: 'user_123',
    template_code: 'welcome',
    to: 'test@example.com',
    template_id: 'welcome',
    variables: {
      name: 'John Doe',
      activation_link: 'https://app.com/activate/token',
    },
  };

  const mockUser = {
    id: 'user_123',
    email: 'test@example.com',
    name: 'John Doe',
    preferences: {
      email: true,
      push: false,
    },
  };

  const mockTemplate = {
    id: 'welcome',
    name: 'Welcome Email',
    code: 'welcome',
    language: 'en',
    version: 1,
    subject: 'Welcome {{name}}!',
    body: 'Hello {{name}}, click here: {{activation_link}}',
  };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        EmailProcessor,
        {
          provide: UserServiceClient,
          useValue: {
            getUser: jest.fn(),
          },
        },
        {
          provide: TemplateServiceClient,
          useValue: {
            getTemplate: jest.fn(),
          },
        },
        {
          provide: ApiGatewayClient,
          useValue: {
            updateStatus: jest.fn().mockResolvedValue({ success: true }),
          },
        },
        {
          provide: AbstractEmailProvider,
          useValue: {
            sendEmail: jest.fn().mockResolvedValue({ success: true }),
          },
        },
      ],
    }).compile();

    processor = module.get<EmailProcessor>(EmailProcessor);
    userServiceClient = module.get(UserServiceClient);
    templateServiceClient = module.get(TemplateServiceClient);
  });

  describe('process', () => {
    it('should process email successfully with valid data', async () => {
      userServiceClient.getUser.mockResolvedValue(mockUser);
      templateServiceClient.getTemplate.mockResolvedValue(mockTemplate);

      await processor.process(mockMessage);

      expect(userServiceClient.getUser).toHaveBeenCalledWith(
        mockMessage.user_id,
      );
      expect(templateServiceClient.getTemplate).toHaveBeenCalledWith(
        mockMessage.template_id,
      );
    });

    it('should throw MessageValidationException when template variables are missing', async () => {
      const incompleteMessage = {
        ...mockMessage,
        variables: {
          name: 'John Doe',
          // Missing activation_link
        },
      };

      templateServiceClient.getTemplate.mockResolvedValue(mockTemplate);

      await expect(processor.process(incompleteMessage)).rejects.toThrow(
        MessageValidationException,
      );
      await expect(processor.process(incompleteMessage)).rejects.toThrow(
        'Invalid message format',
      );
    });

    it('should throw ServiceUnavailableException when user service fails', async () => {
      userServiceClient.getUser.mockRejectedValue(
        new ServiceUnavailableException('User Service', 'Connection refused'),
      );

      templateServiceClient.getTemplate.mockResolvedValue(mockTemplate);

      await expect(processor.process(mockMessage)).rejects.toThrow(
        ServiceUnavailableException,
      );
    });

    it('should throw ServiceUnavailableException when template service fails', async () => {
      templateServiceClient.getTemplate.mockRejectedValue(
        new ServiceUnavailableException(
          'Template Service is currently unavailable',
        ),
      );

      await expect(processor.process(mockMessage)).rejects.toThrow(
        ServiceUnavailableException,
      );
    });

    it('should extract placeholders correctly from template', async () => {
      const complexTemplate = {
        id: 'test',
        name: 'Test Template',
        code: 'test',
        language: 'en',
        version: 1,
        subject: '{{greeting}} {{name}}',
        body: '{{greeting}} {{name}}, your code is {{code}}. {{footer}}',
      };

      const messageWithAllVars = {
        ...mockMessage,
        variables: {
          greeting: 'Hello',
          name: 'John',
          code: '12345',
          footer: 'Thanks',
        },
      };

      userServiceClient.getUser.mockResolvedValue(mockUser);
      templateServiceClient.getTemplate.mockResolvedValue(complexTemplate);

      await processor.process(messageWithAllVars);

      expect(userServiceClient.getUser).toHaveBeenCalled();
      expect(templateServiceClient.getTemplate).toHaveBeenCalled();
    });

    it('should handle template with no variables', async () => {
      const simpleTemplate = {
        id: 'simple',
        name: 'Simple Template',
        code: 'simple',
        language: 'en',
        version: 1,
        subject: 'Welcome!',
        body: 'This is a simple email with no variables.',
      };

      const simpleMessage = {
        ...mockMessage,
        template_id: 'simple',
        variables: {},
      };

      userServiceClient.getUser.mockResolvedValue(mockUser);
      templateServiceClient.getTemplate.mockResolvedValue(simpleTemplate);

      await processor.process(simpleMessage);

      expect(userServiceClient.getUser).toHaveBeenCalled();
    });

    it('should merge user data with message variables', async () => {
      const templateWithUserData = {
        id: 'user_data',
        name: 'User Data Template',
        code: 'user_data',
        language: 'en',
        version: 1,
        subject: 'Hello {{user.name}}',
        body: 'Your email is {{user.email}} and custom: {{custom_field}}',
        text_version:
          'Your email is {{user.email}} and custom: {{custom_field}}',
      };

      const messageWithCustomVars = {
        ...mockMessage,
        variables: {
          'user.name': 'John Doe',
          'user.email': 'john@example.com',
          custom_field: 'Custom Value',
        },
      };

      userServiceClient.getUser.mockResolvedValue(mockUser);
      templateServiceClient.getTemplate.mockResolvedValue(templateWithUserData);

      await processor.process(messageWithCustomVars);

      expect(userServiceClient.getUser).toHaveBeenCalled();
    });
  });
});
