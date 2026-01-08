import { Injectable, Logger, HttpStatus } from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { ConfigService } from '@nestjs/config';
import { firstValueFrom, catchError } from 'rxjs';
import {
  TemplateData,
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
export class TemplateServiceClient {
  private readonly logger = new Logger(TemplateServiceClient.name);
  private readonly baseUrl: string;
  private readonly circuitBreaker: CircuitBreaker;

  constructor(
    private readonly httpService: HttpService,
    private readonly configService: ConfigService,
  ) {
    this.baseUrl = this.configService.get<string>(
      'TEMPLATE_SERVICE_URL',
      'http://localhost:3002',
    );
    this.circuitBreaker = new CircuitBreaker('TemplateService', {
      timeout: CIRCUIT_BREAKER_CONFIG.TIMEOUT,
      error_threshold: CIRCUIT_BREAKER_CONFIG.ERROR_THRESHOLD,
      reset_timeout: CIRCUIT_BREAKER_CONFIG.RESET_TIMEOUT,
    });
  }

  async getTemplate(templateCode: string): Promise<TemplateData> {
    this.logger.log(MSG.TEMPLATE_SERVICE_FETCHING(templateCode));

    return this.circuitBreaker.execute(async () => {
      const response = await firstValueFrom(
        this.httpService
          .get<
            ApiResponse<TemplateData>
          >(`${this.baseUrl}/api/v1/templates/${templateCode}`)
          .pipe(
            catchError((error) => {
              const errorInfo = formatHttpError(error);
              this.logger.error(
                `${MSG.TEMPLATE_SERVICE_FETCH_FAILED(templateCode)}: ${formatHttpErrorMessage(errorInfo)}`,
              );
              throw new ServiceUnavailableException(
                'Template Service',
                errorInfo.message,
              );
            }),
          ),
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      }

      throw new ServiceUnavailableException(
        'Template Service',
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
      return response.status === HttpStatus.OK;
    } catch (error) {
      const errorInfo = formatHttpError(error);
      this.logger.warn(
        `${MSG.TEMPLATE_SERVICE_HEALTH_CHECK_FAILED}: ${formatHttpErrorMessage(errorInfo)}`,
      );
      return false;
    }
  }

  async checkHealth(): Promise<boolean> {
    return this.isHealthy();
  }
}
