export const QUEUE_CONFIG = {
  EXCHANGE: 'notifications.direct',
  EMAIL_QUEUE: 'email.queue',
  EMAIL_ROUTING_KEY: 'notification.email',
  DLX_EXCHANGE: 'notifications.dlx',
  DLX_ROUTING_KEY: 'failed.email',
  FAILED_QUEUE: 'failed.queue',
} as const;

export const RETRY_CONFIG = {
  MAX_RETRIES: 3,
  INITIAL_DELAY: 1000,        // 1 second
  MAX_DELAY: 60000,           // 1 minute
  BACKOFF_MULTIPLIER: 2,      // Exponential backoff
} as const;

export const CIRCUIT_BREAKER_CONFIG = {
  TIMEOUT: 5000,              // 5 seconds
  ERROR_THRESHOLD: 5,         // Open after 5 errors
  RESET_TIMEOUT: 30000,       // Try again after 30 seconds
} as const;
