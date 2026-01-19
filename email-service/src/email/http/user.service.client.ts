import { Injectable, Logger } from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { ConfigService } from '@nestjs/config';
import { firstValueFrom, catchError } from 'rxjs';
import {
  UserData,
  ApiResponse,
} from '../../shared/interfaces/notification-message.interface';
import { ServiceUnavailableException } from '../../common/exceptions/service-unavailable.exception';
import {
  formatHttpError,
  formatHttpErrorMessage,
} from '../../common/utils/http-error.util';
import { CircuitBreaker } from '../../common/utils/circuit-breaker.util';
import { CIRCUIT_BREAKER_CONFIG } from '../../shared/constants/queue.constants';
import * as MSG from '../../constants/system.messages';

@Injectable()
export class UserServiceClient {
  private readonly logger = new Logger(UserServiceClient.name);
  private readonly baseUrl: string;
  private readonly circuitBreaker: CircuitBreaker;

  constructor(
    private readonly httpService: HttpService,
    private readonly configService: ConfigService,
  ) {
    this.baseUrl = this.configService.get<string>(
      'USER_SERVICE_URL',
      'http://localhost:3001',
    );
    this.circuitBreaker = new CircuitBreaker('UserService', {
      timeout: CIRCUIT_BREAKER_CONFIG.TIMEOUT,
      error_threshold: CIRCUIT_BREAKER_CONFIG.ERROR_THRESHOLD,
      reset_timeout: CIRCUIT_BREAKER_CONFIG.RESET_TIMEOUT,
    });
  }

  async getUser(userId: string): Promise<UserData> {
    this.logger.log(MSG.USER_SERVICE_FETCHING(userId));

    return this.circuitBreaker.execute(async () => {
      const response = await firstValueFrom(
        this.httpService
          .get<ApiResponse<UserData>>(`${this.baseUrl}/api/v1/users/${userId}`)
          .pipe(
            catchError((error) => {
              const errorInfo = formatHttpError(error);
              this.logger.error(
                `${MSG.USER_SERVICE_FETCH_FAILED(userId)}: ${formatHttpErrorMessage(errorInfo)}`,
              );
              throw new ServiceUnavailableException(
                'User Service',
                errorInfo.message,
              );
            }),
          ),
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      }

      throw new ServiceUnavailableException(
        'User Service',
        response.data.error || MSG.UNKNOWN_ERROR,
      );
    });
  }

  async isHealthy(): Promise<boolean> {
    try {
      const response = await firstValueFrom(
        this.httpService.get(`${this.baseUrl}/api/v1/health`, {
          timeout: 3000,
        }),
      );
      return response.status === 200;
    } catch (error) {
      const errorInfo = formatHttpError(error);
      this.logger.warn(
        `${MSG.USER_SERVICE_HEALTH_CHECK_FAILED}: ${formatHttpErrorMessage(errorInfo)}`,
      );
      return false;
    }
  }

  async checkHealth(): Promise<boolean> {
    return this.isHealthy();
  }
}
