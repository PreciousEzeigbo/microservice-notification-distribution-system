import { AxiosError } from 'axios';

/**
 * Extracts clean, relevant error information from Axios errors
 * for production-ready logging
 */
export interface HttpErrorInfo {
  code: string;
  message: string;
  url?: string;
  method?: string;
  status?: number;
  status_text?: string;
}

/**
 * Formats Axios errors into clean, structured error information
 * without exposing internal Node.js/Axios details
 */
export function formatHttpError(error: unknown): HttpErrorInfo {
  if (!error) {
    return {
      code: 'UNKNOWN_ERROR',
      message: 'An unknown error occurred',
    };
  }

  // Handle Axios errors
  if (isAxiosError(error)) {
    return {
      code: error.code || 'HTTP_ERROR',
      message: error.message,
      url: error.config?.url,
      method: error.config?.method?.toUpperCase(),
      status: error.response?.status,
      status_text: error.response?.statusText,
    };
  }

  // Handle standard errors
  if (error instanceof Error) {
    return {
      code: 'ERROR',
      message: error.message,
    };
  }

  // Handle unknown error types
  return {
    code: 'UNKNOWN_ERROR',
    message: error instanceof Error ? error.message : JSON.stringify(error),
  };
}

/**
 * Type guard to check if an error is an Axios error
 */
function isAxiosError(error: unknown): error is AxiosError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'isAxiosError' in error &&
    (error as AxiosError).isAxiosError === true
  );
}

/**
 * Formats HTTP error info into a clean, readable log message
 */
export function formatHttpErrorMessage(errorInfo: HttpErrorInfo): string {
  const parts: string[] = [errorInfo.message];

  if (errorInfo.method && errorInfo.url) {
    parts.push(`(${errorInfo.method} ${errorInfo.url})`);
  } else if (errorInfo.url) {
    parts.push(`(${errorInfo.url})`);
  }

  if (errorInfo.status) {
    parts.push(`[${errorInfo.status} ${errorInfo.status_text || ''}]`.trim());
  }

  if (errorInfo.code && errorInfo.code !== 'HTTP_ERROR') {
    parts.push(`Code: ${errorInfo.code}`);
  }

  return parts.join(' ');
}
