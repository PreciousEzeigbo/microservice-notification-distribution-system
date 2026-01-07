/**
 * System Messages Constants
 * Centralized repository for all system messages used across the email service
 */

// ==================== GENERAL MESSAGES ====================
export const INTERNAL_SERVER_ERROR =
  'An unexpected error occurred. Please try again later.';
export const VALIDATION_ERROR = 'Validation failed. Please check your input.';
export const OPERATION_SUCCESSFUL = 'Operation completed successfully.';
export const UNKNOWN_ERROR = 'Unknown error';

// ==================== EMAIL SERVICE MESSAGES ====================
export const EMAIL_SERVICE_INITIALIZED = 'Email service initialized and consuming messages';
export const EMAIL_SERVICE_INITIALIZING = 'Initializing Email Service...';
export const EMAIL_SENT_SUCCESSFULLY = 'Email sent successfully';
export const EMAIL_SENDING_FAILED = 'Email sending failed';
export const EMAIL_PROCESSING_STARTED = 'Processing email notification';
export const EMAIL_PROCESSING_COMPLETED = 'Email notification processed successfully';
export const EMAIL_PROCESSING_FAILED = 'Failed to process email notification';

// ==================== RABBITMQ/QUEUE MESSAGES ====================
export const RABBITMQ_CONNECTING = (url: string) => `Connecting to RabbitMQ at ${url}`;
export const RABBITMQ_CONNECTED = 'RabbitMQ connection established successfully';
export const RABBITMQ_CONNECTION_FAILED = 'Failed to connect to RabbitMQ';
export const RABBITMQ_CHANNEL_CLOSED = 'Channel closed';
export const RABBITMQ_CONNECTION_CLOSED = 'RabbitMQ connection closed';
export const RABBITMQ_DISCONNECT_ERROR = 'Error during disconnect';
export const QUEUE_CONSUMING_STARTED = (queueName: string) => `Starting to consume from ${queueName}`;
export const QUEUE_CONSUMER_STARTED = 'Email consumer started successfully';
export const QUEUE_MESSAGE_RECEIVED = (content: string) => `Received message: ${content.substring(0, 100)}...`;
export const QUEUE_MESSAGE_PROCESSED = (messageId: string) => `Message processed successfully: ${messageId}`;
export const QUEUE_MESSAGE_PROCESSING_ERROR = 'Error processing message';
export const QUEUE_MESSAGE_NULL = 'Received null message';
export const QUEUE_CHANNEL_NOT_INITIALIZED = 'Channel not initialized';
export const QUEUE_HANDLER_NOT_SET = 'Message handler not set. Call setMessageHandler first.';

// ==================== EXTERNAL SERVICE MESSAGES ====================
export const USER_SERVICE_FETCHING = (userId: string) => `Fetching user details for: ${userId}`;
export const USER_SERVICE_FETCH_FAILED = (userId: string) => `Failed to fetch user ${userId}`;
export const USER_SERVICE_UNAVAILABLE = (message: string) => `User service unavailable: ${message}`;
export const USER_SERVICE_ERROR = (error: string) => `User service error: ${error}`;
export const USER_SERVICE_HEALTH_CHECK_FAILED = 'User service health check failed';

export const TEMPLATE_SERVICE_FETCHING = (templateCode: string) => `Fetching template: ${templateCode}`;
export const TEMPLATE_SERVICE_FETCH_FAILED = (templateCode: string) => `Failed to fetch template ${templateCode}`;
export const TEMPLATE_SERVICE_UNAVAILABLE = (message: string) => `Template service unavailable: ${message}`;
export const TEMPLATE_SERVICE_ERROR = (error: string) => `Template service error: ${error}`;
export const TEMPLATE_SERVICE_HEALTH_CHECK_FAILED = 'Template service health check failed';

export const API_GATEWAY_STATUS_UPDATING = (notificationId: string, status: string) => 
  `Updating notification status: ${notificationId} -> ${status}`;
export const API_GATEWAY_STATUS_UPDATED = (notificationId: string) => `Status updated successfully for: ${notificationId}`;
export const API_GATEWAY_STATUS_UPDATE_FAILED = (notificationId: string) => `Failed to update status for ${notificationId}`;
export const API_GATEWAY_STATUS_UPDATE_CONTINUING = 'Status update failed but continuing...';
export const API_GATEWAY_ERROR = (error: string) => `API Gateway error: ${error}`;
export const API_GATEWAY_HEALTH_CHECK_FAILED = 'API Gateway health check failed';

// ==================== SMTP/EMAIL PROVIDER MESSAGES ====================
export const SMTP_SENDING_EMAIL = (to: string) => `Sending email to ${to} via SMTP`;
export const SMTP_EMAIL_SENT = (messageId: string) => `Email sent successfully: ${messageId}`;
export const SMTP_SEND_FAILED = 'Failed to send email via SMTP';
export const SMTP_TRANSPORTER_INIT_FAILED = 'Failed to initialize SMTP transporter';
export const SMTP_CONNECTION_VERIFIED = 'SMTP connection verified successfully';
export const SMTP_CONNECTION_VERIFICATION_FAILED = 'SMTP connection verification failed';

// ==================== VALIDATION MESSAGES ====================
export const MISSING_REQUIRED_FIELDS = (fields: string[]) => `Missing required fields: ${fields.join(', ')}`;
export const INVALID_MESSAGE_FORMAT = 'Invalid message format';
export const USER_DISABLED_EMAIL_NOTIFICATIONS = (userId: string) => 
  `User ${userId} has disabled email notifications`;

// ==================== TEMPLATE PROCESSING MESSAGES ====================
export const TEMPLATE_COMPILING = 'Compiling template with variables';
export const TEMPLATE_COMPILATION_FAILED = 'Template compilation failed';
export const TEMPLATE_COMPILATION_ERROR = (message: string) => `Template compilation error: ${message}`;

// ==================== CORRELATION/TRACING MESSAGES ====================
export const CORRELATION_PREFIX = (correlationId: string) => `[${correlationId}]`;
