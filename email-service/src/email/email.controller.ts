import { Controller, Get, HttpCode } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse } from '@nestjs/swagger';
import { EmailService } from './email.service';

@Controller({ path: 'email', version: '1' })
@ApiTags('Email')
export class EmailController {
  constructor(private readonly emailService: EmailService) {}

  @Get('health')
  @HttpCode(200)
  @ApiOperation({ summary: 'Check email service health' })
  @ApiResponse({ status: 200, description: 'Service is healthy' })
  async checkHealth() {
    const health = await this.emailService.getHealth();
    
    return {
      ...health,
      timestamp: new Date().toISOString(),
    };
  }
}
