import { Injectable } from '@nestjs/common';
import * as packageJson from '../package.json';

@Injectable()
export class AppService {
  getHello(): string {
    return `Email Service API - v${packageJson.version}`;
  }
}
