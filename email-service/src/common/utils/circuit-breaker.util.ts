import { Logger } from '@nestjs/common';

export enum CircuitState {
  CLOSED = 'CLOSED',
  OPEN = 'OPEN',
  HALF_OPEN = 'HALF_OPEN',
}

export interface CircuitBreakerConfig {
  timeout: number;
  error_threshold: number;
  reset_timeout: number;
}

export class CircuitBreaker {
  private state: CircuitState = CircuitState.CLOSED;
  private failure_count = 0;
  private next_attempt_time = 0;
  private success_count = 0;
  private readonly logger: Logger;

  constructor(
    private readonly name: string,
    private readonly config: CircuitBreakerConfig,
  ) {
    this.logger = new Logger(`CircuitBreaker[${name}]`);
  }

  async execute<T>(operation: () => Promise<T>): Promise<T> {
    if (this.state === CircuitState.OPEN) {
      if (Date.now() < this.next_attempt_time) {
        this.logger.warn(`Circuit is OPEN for ${this.name}. Request rejected.`);
        throw new Error(`Circuit breaker is OPEN for ${this.name}`);
      }
      // Transition to HALF_OPEN to test if service has recovered
      this.state = CircuitState.HALF_OPEN;
      this.logger.log(`Circuit transitioning to HALF_OPEN for ${this.name}`);
    }

    try {
      const result = await Promise.race([operation(), this.timeout()]);

      this.on_success();
      return result as T;
    } catch (error) {
      this.on_failure();
      throw error;
    }
  }

  private async timeout(): Promise<never> {
    return new Promise((_, reject) => {
      setTimeout(() => {
        reject(new Error(`Operation timeout after ${this.config.timeout}ms`));
      }, this.config.timeout);
    });
  }

  private on_success(): void {
    this.failure_count = 0;

    if (this.state === CircuitState.HALF_OPEN) {
      this.success_count++;
      // Require a few successful requests before closing
      if (this.success_count >= 2) {
        this.state = CircuitState.CLOSED;
        this.success_count = 0;
        this.logger.log(`Circuit is now CLOSED for ${this.name}`);
      }
    }
  }

  private on_failure(): void {
    this.failure_count++;
    this.success_count = 0;

    if (this.failure_count >= this.config.error_threshold) {
      this.state = CircuitState.OPEN;
      this.next_attempt_time = Date.now() + this.config.reset_timeout;
      this.logger.error(
        `Circuit is now OPEN for ${this.name}. Will retry after ${this.config.reset_timeout}ms`,
      );
    }
  }

  get_state(): string {
    return this.state;
  }

  reset(): void {
    this.state = CircuitState.CLOSED;
    this.failure_count = 0;
    this.success_count = 0;
    this.next_attempt_time = 0;
    this.logger.log(`Circuit manually reset for ${this.name}`);
  }
}
