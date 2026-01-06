import { Injectable, Logger } from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { ConfigService } from '@nestjs/config';
import { firstValueFrom } from 'rxjs';
import { NotificationStatusUpdate, ApiResponse } from '../../shared/interfaces/notification-message.interface';

@Injectable()
export class ApiGatewayClient {
  private readonly logger = new Logger(ApiGatewayClient.name);
  private readonly baseUrl: string;

  constructor(
    private readonly httpService: HttpService,
    private readonly configService: ConfigService,
  ) {
    this.baseUrl = this.configService.get<string>('API_GATEWAY_URL', 'http://localhost:3000');
  }

  async updateStatus(statusUpdate: NotificationStatusUpdate): Promise<void> {
    try {
      this.logger.log(`Updating notification status: ${statusUpdate.notification_id} -> ${statusUpdate.status}`);

      const response = await firstValueFrom(
        this.httpService.post<ApiResponse>(
          `${this.baseUrl}/api/v1/notifications/${statusUpdate.notification_id}/status`,
          statusUpdate
        )
      );

      if (!response.data.success) {
        throw new Error(`API Gateway error: ${response.data.error || 'Unknown error'}`);
      }

      this.logger.log(`Status updated successfully for: ${statusUpdate.notification_id}`);
    } catch (error) {
      this.logger.error(`Failed to update status for ${statusUpdate.notification_id}`, error);
      
      // Don't throw error here to prevent message reprocessing
      // Status update failure shouldn't fail the entire message processing
      this.logger.warn('Status update failed but continuing...');
    }
  }

  async isHealthy(): Promise<boolean> {
    try {
      const response = await firstValueFrom(
        this.httpService.get(`${this.baseUrl}/api/v1/health`, { timeout: 3000 })
      );
      return response.status === 200;
    } catch (error) {
      this.logger.warn('API Gateway health check failed', error);
      return false;
    }
  }
}
