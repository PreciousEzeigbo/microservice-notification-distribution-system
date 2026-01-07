import {
  ExceptionFilter,
  Catch,
  ArgumentsHost,
  HttpException,
  Logger,
} from '@nestjs/common';
import { Request, Response } from 'express';

/**
 * HTTP Exception Filter
 * Specifically handles HttpException instances
 * Provides detailed error responses for HTTP errors
 */
@Catch(HttpException)
export class HttpExceptionFilter implements ExceptionFilter {
  private readonly logger = new Logger(HttpExceptionFilter.name);

  catch(exception: HttpException, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();
    const status = exception.getStatus();
    const exceptionResponse = exception.getResponse();

    const errorResponse = {
      success: false,
      statusCode: status,
      timestamp: new Date().toISOString(),
      path: request.url,
      method: request.method,
      message: exception.message,
      error:
        typeof exceptionResponse === 'object'
          ? exceptionResponse
          : { message: exceptionResponse },
    };

    // Log the error
    this.logger.warn(
      `HTTP Exception: ${request.method} ${request.url} - Status ${status}`,
      {
        ...errorResponse,
        stack: exception.stack,
      },
    );

    response.status(status).json(errorResponse);
  }
}
