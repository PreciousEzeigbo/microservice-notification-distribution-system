import { Injectable, Logger } from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { ConfigService } from '@nestjs/config';
import { firstValueFrom } from 'rxjs';
import { TemplateData, ApiResponse } from '../../shared/interfaces/notification-message.interface';

@Injectable()
export class TemplateServiceClient {
  private readonly logger = new Logger(TemplateServiceClient.name);
  private readonly baseUrl: string;

  constructor(
    private readonly httpService: HttpService,
    private readonly configService: ConfigService,
  ) {
    this.baseUrl = this.configService.get<string>('TEMPLATE_SERVICE_URL', 'http://localhost:3002');
  }

  async getTemplate(templateCode: string): Promise<TemplateData> {
    try {
      this.logger.log(`Fetching template: ${templateCode}`);

      const response = await firstValueFrom(
        this.httpService.get<ApiResponse<TemplateData>>(`${this.baseUrl}/api/v1/templates/${templateCode}`)
      );

      // Handle different response formats
      if (response.data.success && response.data.data) {
        return response.data.data;
      }

      throw new Error(`Template service error: ${response.data.error || 'Unknown error'}`);
    } catch (error) {
      this.logger.error(`Failed to fetch template ${templateCode}`, error);
      
      // TODO: Implement circuit breaker and fallback (use cached template)
      if (error instanceof Error) {
        throw new Error(`Template service unavailable: ${error.message}`);
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
      this.logger.warn('Template service health check failed', error);
      return false;
    }
  }
}
