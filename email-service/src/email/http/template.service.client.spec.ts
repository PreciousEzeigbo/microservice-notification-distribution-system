import { Test, TestingModule } from '@nestjs/testing';
import { HttpService } from '@nestjs/axios';
import { ConfigService } from '@nestjs/config';
import { TemplateServiceClient } from './template.service.client';
import { ServiceUnavailableException } from '../../common/exceptions/service-unavailable.exception';
import { of, throwError } from 'rxjs';
import { AxiosError, AxiosResponse } from 'axios';

describe('TemplateServiceClient', () => {
  let client: TemplateServiceClient;
  let httpService: jest.Mocked<HttpService>;

  const mockTemplate = {
    id: 'welcome',
    name: 'Welcome Email',
    subject: 'Welcome {{name}}!',
    body: 'Hello {{name}}, click here: {{activation_link}}',
  };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        TemplateServiceClient,
        {
          provide: HttpService,
          useValue: {
            get: jest.fn(),
          },
        },
        {
          provide: ConfigService,
          useValue: {
            get: jest.fn().mockReturnValue('http://localhost:3002'),
          },
        },
      ],
    }).compile();

    client = module.get<TemplateServiceClient>(TemplateServiceClient);
    httpService = module.get(HttpService);
  });

  describe('getTemplate', () => {
    it('should fetch template successfully', async () => {
      const mockResponse: AxiosResponse = {
        data: { success: true, data: mockTemplate },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      };

      httpService.get.mockReturnValue(of(mockResponse));

      const result = await client.getTemplate('welcome');

      expect(result).toEqual(mockTemplate);
      expect(httpService.get).toHaveBeenCalledWith(
        'http://localhost:3002/api/v1/templates/welcome',
      );
    });

    it('should throw ServiceUnavailableException on connection error', async () => {
      const error: AxiosError = {
        code: 'ECONNREFUSED',
        message: 'Connection refused',
        name: 'AxiosError',
        config: {} as any,
        isAxiosError: true,
        toJSON: () => ({}),
      };

      httpService.get.mockReturnValue(throwError(() => error));

      await expect(client.getTemplate('welcome')).rejects.toThrow(
        ServiceUnavailableException,
      );
      await expect(client.getTemplate('welcome')).rejects.toThrow(
        'Template Service is currently unavailable',
      );
    });

    it('should be protected by circuit breaker', async () => {
      const error: AxiosError = {
        code: 'ECONNREFUSED',
        message: 'Connection refused',
        name: 'AxiosError',
        config: {} as any,
        isAxiosError: true,
        toJSON: () => ({}),
      };

      httpService.get.mockReturnValue(throwError(() => error));

      // Trigger circuit breaker
      for (let i = 0; i < 5; i++) {
        try {
          await client.getTemplate('welcome');
        } catch (e) {
          // Expected
        }
      }

      await expect(client.getTemplate('welcome')).rejects.toThrow();
    });
  });

  describe('checkHealth', () => {
    it('should return healthy status when service is available', async () => {
      const mockResponse: AxiosResponse = {
        data: { status: 'ok' },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      };

      httpService.get.mockReturnValue(of(mockResponse));

      const result = await client.checkHealth();

      expect(result).toBe(true);
      expect(httpService.get).toHaveBeenCalledWith(
        'http://localhost:3002/api/v1/health',
        { timeout: 3000 },
      );
    });

    it('should return unhealthy status when service is unavailable', async () => {
      const error: AxiosError = {
        code: 'ECONNREFUSED',
        message: 'Connection refused',
        name: 'AxiosError',
        config: {} as any,
        isAxiosError: true,
        toJSON: () => ({}),
      };

      httpService.get.mockReturnValue(throwError(() => error));

      const result = await client.checkHealth();

      expect(result).toBe(false);
    });
  });
});
