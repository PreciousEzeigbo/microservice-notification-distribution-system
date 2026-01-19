import { Test, TestingModule } from '@nestjs/testing';
import { HttpExceptionFilter } from './http-exception.filter';
import { HttpException, HttpStatus } from '@nestjs/common';
import { ArgumentsHost } from '@nestjs/common';

describe('HttpExceptionFilter', () => {
  let filter: HttpExceptionFilter;
  let mockResponse: any;
  let mockRequest: any;
  let mockArgumentsHost: ArgumentsHost;

  beforeEach(() => {
    filter = new HttpExceptionFilter();

    mockResponse = {
      status: jest.fn().mockReturnThis(),
      json: jest.fn(),
    };

    mockRequest = {
      url: '/test-endpoint',
      method: 'POST',
    };

    mockArgumentsHost = {
      switchToHttp: jest.fn().mockReturnValue({
        getResponse: () => mockResponse,
        getRequest: () => mockRequest,
      }),
    } as any;
  });

  it('should format error response in snake_case', () => {
    const exception = new HttpException(
      'Test error message',
      HttpStatus.BAD_REQUEST,
    );

    filter.catch(exception, mockArgumentsHost);

    expect(mockResponse.status).toHaveBeenCalledWith(HttpStatus.BAD_REQUEST);
    expect(mockResponse.json).toHaveBeenCalledWith(
      expect.objectContaining({
        status_code: HttpStatus.BAD_REQUEST,
        message: 'Test error message',
        error: { message: 'Test error message' },
        timestamp: expect.any(String),
        path: '/test-endpoint',
        method: 'POST',
      }),
    );
  });

  it('should handle HttpException with detailed response', () => {
    const exception = new HttpException(
      {
        message: 'Validation failed',
        errors: ['Field is required'],
      },
      HttpStatus.UNPROCESSABLE_ENTITY,
    );

    filter.catch(exception, mockArgumentsHost);

    expect(mockResponse.status).toHaveBeenCalledWith(
      HttpStatus.UNPROCESSABLE_ENTITY,
    );
    expect(mockResponse.json).toHaveBeenCalledWith(
      expect.objectContaining({
        status_code: HttpStatus.UNPROCESSABLE_ENTITY,
        message: 'Validation failed',
        error: {
          message: 'Validation failed',
          errors: ['Field is required'],
        },
        method: 'POST',
      }),
    );
  });

  it('should format 404 Not Found error', () => {
    const exception = new HttpException(
      'Resource not found',
      HttpStatus.NOT_FOUND,
    );

    filter.catch(exception, mockArgumentsHost);

    expect(mockResponse.status).toHaveBeenCalledWith(HttpStatus.NOT_FOUND);
    expect(mockResponse.json).toHaveBeenCalledWith(
      expect.objectContaining({
        status_code: HttpStatus.NOT_FOUND,
        message: 'Resource not found',
        error: { message: 'Resource not found' },
        method: 'POST',
      }),
    );
  });

  it('should format 500 Internal Server Error', () => {
    const exception = new HttpException(
      'Internal server error',
      HttpStatus.INTERNAL_SERVER_ERROR,
    );

    filter.catch(exception, mockArgumentsHost);

    expect(mockResponse.status).toHaveBeenCalledWith(
      HttpStatus.INTERNAL_SERVER_ERROR,
    );
    expect(mockResponse.json).toHaveBeenCalledWith(
      expect.objectContaining({
        status_code: HttpStatus.INTERNAL_SERVER_ERROR,
        message: 'Internal server error',
        error: { message: 'Internal server error' },
        method: 'POST',
      }),
    );
  });

  it('should include timestamp in ISO format', () => {
    const exception = new HttpException('Test error', HttpStatus.BAD_REQUEST);

    filter.catch(exception, mockArgumentsHost);

    const callArgs = mockResponse.json.mock.calls[0][0];
    const timestamp = new Date(callArgs.timestamp);

    expect(timestamp).toBeInstanceOf(Date);
    expect(timestamp.toISOString()).toBe(callArgs.timestamp);
  });

  it('should include request path', () => {
    mockRequest.url = '/api/v1/email/send';
    const exception = new HttpException('Test error', HttpStatus.BAD_REQUEST);

    filter.catch(exception, mockArgumentsHost);

    expect(mockResponse.json).toHaveBeenCalledWith(
      expect.objectContaining({
        path: '/api/v1/email/send',
      }),
    );
  });
});
