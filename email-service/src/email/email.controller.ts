import { Controller, Get, HttpStatus, Res } from '@nestjs/common';
import type { Response } from 'express';
import { ApiTags, ApiOperation, ApiResponse } from '@nestjs/swagger';
import { EmailService } from './email.service';
import * as MSG from '../constants/system.messages';

@Controller({ path: 'email', version: '1' })
@ApiTags('Email')
export class EmailController {
  constructor(private readonly emailService: EmailService) {}

  @Get('health')
  @ApiOperation({ summary: 'Check email service health' })
  @ApiResponse({ status: HttpStatus.OK, description: 'Service is healthy' })
  @ApiResponse({
    status: HttpStatus.SERVICE_UNAVAILABLE,
    description: 'Service is unhealthy',
  })
  async checkHealth(@Res() res: Response) {
    const health = await this.emailService.getHealth();

    // Service is completely down (critical dependencies failed)
    if (!health.healthy) {
      return res.status(HttpStatus.SERVICE_UNAVAILABLE).json({
        status_code: HttpStatus.SERVICE_UNAVAILABLE,
        message: MSG.EMAIL_SERVICE_UNHEALTHY,
        error: `Unhealthy dependencies: ${(health.unhealthy_dependencies || []).join(', ')}`,
        data: health.details,
      });
    }

    // Service is functional but some external services are down
    if (health.degraded) {
      return res.status(HttpStatus.OK).json({
        status_code: HttpStatus.OK,
        message: MSG.EMAIL_SERVICE_DEGRADED,
        data: {
          ...health.details,
          warning: `Some external services unavailable: ${(health.unhealthy_dependencies || []).join(', ')}`,
        },
      });
    }

    // All services healthy
    return res.status(HttpStatus.OK).json({
      status_code: HttpStatus.OK,
      message: MSG.EMAIL_SERVICE_HEALTHY,
      data: health.details,
    });
  }
}
