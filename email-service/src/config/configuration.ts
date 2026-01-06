import { registerAs } from '@nestjs/config';

export default registerAs('app', () => ({
  // RabbitMQ Configuration
  rabbitmq: {
    url: process.env.RABBITMQ_URL || 'amqp://guest:guest@localhost:5672',
    host: process.env.RABBITMQ_HOST || 'localhost',
    port: parseInt(process.env.RABBITMQ_PORT || '5672', 10),
    user: process.env.RABBITMQ_USER || 'guest',
    password: process.env.RABBITMQ_PASSWORD || 'guest',
    vhost: process.env.RABBITMQ_VHOST || '/',
  },

  // External Services
  services: {
    userService: process.env.USER_SERVICE_URL || 'http://localhost:3001',
    templateService: process.env.TEMPLATE_SERVICE_URL || 'http://localhost:3002',
    apiGateway: process.env.API_GATEWAY_URL || 'http://localhost:3000',
  },

  // SMTP Configuration
  smtp: {
    host: process.env.SMTP_HOST || 'smtp.gmail.com',
    port: parseInt(process.env.SMTP_PORT || '587', 10),
    secure: process.env.SMTP_SECURE === 'true',
    user: process.env.SMTP_USER,
    password: process.env.SMTP_PASSWORD,
    from: process.env.SMTP_FROM_EMAIL || 'noreply@example.com',
  },

  // Optional: Alternative Email Providers
  sendgrid: {
    apiKey: process.env.SENDGRID_API_KEY,
  },

  mailgun: {
    apiKey: process.env.MAILGUN_API_KEY,
    domain: process.env.MAILGUN_DOMAIN,
  },
}));
