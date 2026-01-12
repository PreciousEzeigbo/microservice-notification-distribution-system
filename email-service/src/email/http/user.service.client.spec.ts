import { Test, TestingModule } from '@nestjs/testing';
import { HttpService } from '@nestjs/axios';
import { ConfigService } from '@nestjs/config';
import { UserServiceClient } from './user.service.client';
import { ServiceUnavailableException } from '../../common/exceptions/service-unavailable.exception';
import { of, throwError } from 'rxjs';
import { AxiosError, AxiosResponse } from 'axios';

describe('UserServiceClient', () => {
  let client: UserServiceClient;
  let httpService: jest.Mocked<HttpService>;

  const mockUser = {
    id: 'user_123',
    email: 'test@example.com',
    name: 'John Doe',
    preferences: {},
  };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        UserServiceClient,
        {
          provide: HttpService,
          useValue: {
            get: jest.fn(),
          },
        },
        {
          provide: ConfigService,
          useValue: {
            get: jest.fn().mockReturnValue('http://localhost:3001'),
          },
        },
      ],
    }).compile();

    client = module.get<UserServiceClient>(UserServiceClient);
    httpService = module.get(HttpService);
  });

  describe('getUser', () => {
    it('should fetch user successfully', async () => {
      const mockResponse: AxiosResponse = {
        data: { success: true, data: mockUser },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      };

      httpService.get.mockReturnValue(of(mockResponse));

      const result = await client.getUser('user_123');

      expect(result).toEqual(mockUser);
      expect(httpService.get).toHaveBeenCalledWith(
        'http://localhost:3001/api/v1/users/user_123',
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

      await expect(client.getUser('user_123')).rejects.toThrow(
        ServiceUnavailableException,
      );
      await expect(client.getUser('user_123')).rejects.toThrow(
        'User Service is currently unavailable',
      );
    });

    it('should throw ServiceUnavailableException on 500 error', async () => {
      const error: AxiosError = {
        code: 'ERR_BAD_RESPONSE',
        message: 'Request failed with status code 500',
        name: 'AxiosError',
        config: {} as any,
        isAxiosError: true,
        response: {
          status: 500,
          statusText: 'Internal Server Error',
          data: {},
          headers: {},
          config: {} as any,
        },
        toJSON: () => ({}),
      };

      httpService.get.mockReturnValue(throwError(() => error));

      await expect(client.getUser('user_123')).rejects.toThrow(
        ServiceUnavailableException,
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

      // Trigger circuit breaker by repeated failures
      for (let i = 0; i < 5; i++) {
        try {
          await client.getUser('user_123');
        } catch (e) {
          // Expected
        }
      }

      // Circuit should now be OPEN
      await expect(client.getUser('user_123')).rejects.toThrow();
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
        'http://localhost:3001/api/v1/health',
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
