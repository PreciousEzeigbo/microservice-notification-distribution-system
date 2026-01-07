import { HttpException, HttpStatus } from '@nestjs/common';

/**
 * Custom exception for external service unavailability
 * Use when external services (User, Template, API Gateway) are unreachable
 */
export class ServiceUnavailableException extends HttpException {
  constructor(service: string, originalError?: string) {
    super(
      {
        status_code: HttpStatus.SERVICE_UNAVAILABLE,
        message: `${service} is currently unavailable`,
        error: 'Service Unavailable',
        details: originalError,
      },
      HttpStatus.SERVICE_UNAVAILABLE,
    );
  }
}
