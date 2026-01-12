import {
  ExceptionFilter,
  Catch,
  ArgumentsHost,
  HttpException,
  HttpStatus,
  Logger,
} from '@nestjs/common';
import { Request, Response } from 'express';

/**
 * Global Exception Filter
 * Catches all unhandled exceptions across the application
 * Provides consistent error response format and logging
 */
@Catch()
export class AllExceptionsFilter implements ExceptionFilter {
  private readonly logger = new Logger(AllExceptionsFilter.name);

  catch(exception: unknown, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();

    const status =
      exception instanceof HttpException
        ? exception.getStatus()
        : HttpStatus.INTERNAL_SERVER_ERROR;

    const message =
      exception instanceof HttpException
        ? exception.message
        : 'Internal server error';

    const errorResponse =
      exception instanceof HttpException ? exception.getResponse() : null;

    // Log the error with full details

    this.logger.error(
      `HTTP ${status} Error - ${request.method} ${request.url}`,
      {
        message,
        status_code: status,
        timestamp: new Date().toISOString(),
        path: request.url,
        method: request.method,
        exception: exception instanceof Error ? exception.stack : exception,
      },
    );

    // Send consistent error response
    response.status(status).json({
      status_code: status,
      message,
      error:
        typeof errorResponse === 'object' && errorResponse !== null
          ? errorResponse
          : { message },
      timestamp: new Date().toISOString(),
      path: request.url,
    });
  }
}
