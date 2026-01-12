import { registerAs } from '@nestjs/config';

export default registerAs('app', () => ({
  // RabbitMQ Configuration
  rabbitmq: {
    url: process.env.RABBITMQ_URL,
    host: process.env.RABBITMQ_HOST,
    port: parseInt(process.env.RABBITMQ_PORT!, 10),
    user: process.env.RABBITMQ_USER,
    password: process.env.RABBITMQ_PASSWORD,
    vhost: process.env.RABBITMQ_VHOST,
  },

  // External Services
  services: {
    userService: process.env.USER_SERVICE_URL,
    templateService: process.env.TEMPLATE_SERVICE_URL,
    apiGateway: process.env.API_GATEWAY_URL,
  },

  // SMTP Configuration
  smtp: {
    host: process.env.SMTP_HOST,
    port: parseInt(process.env.SMTP_PORT!, 10),
    secure: process.env.SMTP_SECURE === 'true',
    user: process.env.SMTP_USER,
    password: process.env.SMTP_PASSWORD,
    from: process.env.SMTP_FROM_EMAIL,
  },
}));
