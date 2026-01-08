import { Injectable, Logger, HttpStatus } from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { ConfigService } from '@nestjs/config';
import { firstValueFrom, catchError, of } from 'rxjs';
import { NotificationStatusUpdate, ApiResponse } from '../../shared/interfaces/notification-message.interface';
import { formatHttpError, formatHttpErrorMessage } from '../../common/utils/http-error.util';
import { CircuitBreaker } from '../../common/utils/circuit-breaker.util';
import { CIRCUIT_BREAKER_CONFIG } from '../../shared/constants/queue.constants';
import * as MSG from '../../constants/system.messages';

@Injectable()
export class ApiGatewayClient {
  private readonly logger = new Logger(ApiGatewayClient.name);
  private readonly baseUrl: string;
  private readonly circuitBreaker: CircuitBreaker;

  constructor(
    private readonly httpService: HttpService,
    private readonly configService: ConfigService,
  ) {
    this.baseUrl = this.configService.get<string>('API_GATEWAY_URL', 'http://localhost:3000');
    this.circuitBreaker = new CircuitBreaker('ApiGateway', {
      timeout: CIRCUIT_BREAKER_CONFIG.TIMEOUT,
      error_threshold: CIRCUIT_BREAKER_CONFIG.ERROR_THRESHOLD,
      reset_timeout: CIRCUIT_BREAKER_CONFIG.RESET_TIMEOUT,
    });
  }

  async updateStatus(statusUpdate: NotificationStatusUpdate): Promise<void> {
    this.logger.log(MSG.API_GATEWAY_STATUS_UPDATING(statusUpdate.notification_id, statusUpdate.status));

    try {
      await this.circuitBreaker.execute(async () => {
        await firstValueFrom(
          this.httpService.post<ApiResponse>(
            `${this.baseUrl}/api/v1/notifications/${statusUpdate.notification_id}/status`,
            statusUpdate
          ).pipe(
            catchError((error) => {
              const errorInfo = formatHttpError(error);
              this.logger.error(
                `${MSG.API_GATEWAY_STATUS_UPDATE_FAILED(statusUpdate.notification_id)}: ${formatHttpErrorMessage(errorInfo)}`
              );
              this.logger.warn(MSG.API_GATEWAY_STATUS_UPDATE_CONTINUING);
              // Don't throw - return empty observable to prevent message reprocessing
              return of(null);
            }),
          ),
        );
      });
    } catch (error) {
      // Circuit breaker is open or operation failed
      this.logger.warn(MSG.API_GATEWAY_STATUS_UPDATE_CONTINUING);
    }

    this.logger.log(MSG.API_GATEWAY_STATUS_UPDATED(statusUpdate.notification_id));
  }

  async isHealthy(): Promise<boolean> {
    try {
      const response = await firstValueFrom(
        this.httpService.get(`${this.baseUrl}/api/v1/health`, { timeout: 3000 })
      );
      return response.status === HttpStatus.OK;
    } catch (error) {
      const errorInfo = formatHttpError(error);
      this.logger.warn(`${MSG.API_GATEWAY_HEALTH_CHECK_FAILED}: ${formatHttpErrorMessage(errorInfo)}`);
      return false;
    }
  }
}
