import { HttpException, HttpStatus } from '@nestjs/common';

/**
 * Custom exception for message validation failures
 * Use when RabbitMQ message format is invalid
 */
export class MessageValidationException extends HttpException {
  constructor(missingFields: string[]) {
    super(
      {
        status_code: HttpStatus.BAD_REQUEST,
        message: 'Invalid message format',
        error: 'Validation Error',
        missing_fields: missingFields,
      },
      HttpStatus.BAD_REQUEST,
    );
  }
}
