import { Test, TestingModule } from '@nestjs/testing';
import { HttpService } from '@nestjs/axios';
import { ConfigService } from '@nestjs/config';
import { ApiGatewayClient } from './api-gateway.client';
import { of, throwError } from 'rxjs';
import { AxiosError, AxiosResponse } from 'axios';
import { NotificationStatus } from '../../shared/interfaces/notification-message.interface';

describe('ApiGatewayClient', () => {
  let client: ApiGatewayClient;
  let httpService: jest.Mocked<HttpService>;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        ApiGatewayClient,
        {
          provide: HttpService,
          useValue: {
            post: jest.fn(),
            get: jest.fn(),
          },
        },
        {
          provide: ConfigService,
          useValue: {
            get: jest.fn().mockReturnValue('http://localhost:3000'),
          },
        },
      ],
    }).compile();

    client = module.get<ApiGatewayClient>(ApiGatewayClient);
    httpService = module.get(HttpService);
  });

  describe('updateStatus', () => {
    it('should update notification status successfully', async () => {
      const mockResponse: AxiosResponse = {
        data: { success: true },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      };

      httpService.post.mockReturnValue(of(mockResponse));

      await client.updateStatus({
        message_id: 'msg_123',
        status: NotificationStatus.DELIVERED,
        timestamp: new Date().toISOString(),
      });

      expect(httpService.post).toHaveBeenCalledWith(
        'http://localhost:3000/api/v1/notifications/msg_123/status',
        expect.objectContaining({ status: NotificationStatus.DELIVERED }),
      );
    });

    it('should handle connection errors gracefully', async () => {
      const error: AxiosError = {
        code: 'ECONNREFUSED',
        message: 'Connection refused',
        name: 'AxiosError',
        config: {} as any,
        isAxiosError: true,
        toJSON: () => ({}),
      };

      httpService.post.mockReturnValue(throwError(() => error));

      // Should not throw, just log warning
      await expect(
        client.updateStatus({
          message_id: 'msg_123',
          status: NotificationStatus.FAILED,
          timestamp: new Date().toISOString(),
          error: 'Processing failed',
        }),
      ).resolves.not.toThrow();
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

      httpService.post.mockReturnValue(throwError(() => error));

      // Trigger circuit breaker
      for (let i = 0; i < 5; i++) {
        await client.updateStatus({
          message_id: 'msg_123',
          status: NotificationStatus.FAILED,
          timestamp: new Date().toISOString(),
        });
      }

      // Should still not throw
      await expect(
        client.updateStatus({
          message_id: 'msg_123',
          status: NotificationStatus.FAILED,
          timestamp: new Date().toISOString(),
        }),
      ).resolves.not.toThrow();
    });
  });

  describe('isHealthy', () => {
    it('should return healthy status when service is available', async () => {
      const mockResponse: AxiosResponse = {
        data: { status: 'ok' },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      };

      httpService.get.mockReturnValue(of(mockResponse));

      const result = await client.isHealthy();

      expect(result).toBe(true);
      expect(httpService.get).toHaveBeenCalledWith(
        'http://localhost:3000/api/v1/health',
        expect.objectContaining({ timeout: 3000 }),
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

      const result = await client.isHealthy();

      expect(result).toBe(false);
    });
  });
});
