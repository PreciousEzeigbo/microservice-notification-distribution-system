import { Injectable, Logger } from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { ConfigService } from '@nestjs/config';
import { firstValueFrom } from 'rxjs';
import { UserData, ApiResponse } from '../../shared/interfaces/notification-message.interface';

@Injectable()
export class UserServiceClient {
  private readonly logger = new Logger(UserServiceClient.name);
  private readonly baseUrl: string;

  constructor(
    private readonly httpService: HttpService,
    private readonly configService: ConfigService,
  ) {
    this.baseUrl = this.configService.get<string>('USER_SERVICE_URL', 'http://localhost:3001');
  }

  async getUser(userId: string): Promise<UserData> {
    try {
      this.logger.log(`Fetching user details for: ${userId}`);

      const response = await firstValueFrom(
        this.httpService.get<ApiResponse<UserData>>(`${this.baseUrl}/api/v1/users/${userId}`)
      );

      // Handle different response formats
      if (response.data.success && response.data.data) {
        return response.data.data;
      }

      throw new Error(`User service error: ${response.data.error || 'Unknown error'}`);
    } catch (error) {
      this.logger.error(`Failed to fetch user ${userId}`, error);
      
      // TODO: Implement circuit breaker and fallback
      if (error instanceof Error) {
        throw new Error(`User service unavailable: ${error.message}`);
      }
      throw error;
    }
  }

  async isHealthy(): Promise<boolean> {
    try {
      const response = await firstValueFrom(
        this.httpService.get(`${this.baseUrl}/api/v1/health`, { timeout: 3000 })
      );
      return response.status === 200;
    } catch (error) {
      this.logger.warn('User service health check failed', error);
      return false;
    }
  }
}
