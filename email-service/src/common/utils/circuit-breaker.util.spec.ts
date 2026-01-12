import { CircuitBreaker, CircuitState } from './circuit-breaker.util';

describe('CircuitBreaker', () => {
  let circuitBreaker: CircuitBreaker;

  beforeEach(() => {
    circuitBreaker = new CircuitBreaker('TestService', {
      timeout: 1000,
      error_threshold: 3,
      reset_timeout: 5000,
    });
  });

  describe('CLOSED state', () => {
    it('should execute function successfully in CLOSED state', async () => {
      const mockFn = jest.fn().mockResolvedValue('success');

      const result = await circuitBreaker.execute(mockFn);

      expect(result).toBe('success');
      expect(mockFn).toHaveBeenCalled();
      expect(circuitBreaker.get_state()).toBe(CircuitState.CLOSED);
    });

    it('should transition to OPEN after error threshold', async () => {
      const mockFn = jest.fn().mockRejectedValue(new Error('Service error'));

      // Trigger errors to reach threshold (3)
      await expect(circuitBreaker.execute(mockFn)).rejects.toThrow(
        'Service error',
      );
      await expect(circuitBreaker.execute(mockFn)).rejects.toThrow(
        'Service error',
      );
      await expect(circuitBreaker.execute(mockFn)).rejects.toThrow(
        'Service error',
      );

      expect(circuitBreaker.get_state()).toBe(CircuitState.OPEN);
    });

    it('should handle timeout and count as failure', async () => {
      const mockFn = jest
        .fn()
        .mockImplementation(
          () => new Promise((resolve) => setTimeout(resolve, 2000)),
        );

      await expect(circuitBreaker.execute(mockFn)).rejects.toThrow(
        'Operation timeout after 1000ms',
      );
    });
  });

  describe('OPEN state', () => {
    beforeEach(async () => {
      const mockFn = jest.fn().mockRejectedValue(new Error('Service error'));

      // Trigger errors to open circuit
      for (let i = 0; i < 3; i++) {
        try {
          await circuitBreaker.execute(mockFn);
        } catch (error) {
          // Expected
        }
      }
    });

    it('should reject immediately in OPEN state', async () => {
      const mockFn = jest.fn().mockResolvedValue('success');

      await expect(circuitBreaker.execute(mockFn)).rejects.toThrow(
        'Circuit breaker is OPEN for TestService',
      );

      expect(mockFn).not.toHaveBeenCalled();
    });

    it('should transition to HALF_OPEN after reset timeout', async () => {
      jest.useFakeTimers();

      // Advance time past reset timeout
      jest.advanceTimersByTime(5100);

      const mockFn = jest.fn().mockResolvedValue('success');
      await circuitBreaker.execute(mockFn);

      expect(circuitBreaker.get_state()).toBe(CircuitState.HALF_OPEN);

      jest.useRealTimers();
    });
  });

  describe('HALF_OPEN state', () => {
    beforeEach(async () => {
      const mockFn = jest.fn().mockRejectedValue(new Error('Service error'));

      // Open the circuit
      for (let i = 0; i < 3; i++) {
        try {
          await circuitBreaker.execute(mockFn);
        } catch (error) {
          // Expected
        }
      }
    });

    it('should transition to CLOSED on successful execution', async () => {
      // Wait for reset timeout
      await new Promise((resolve) => setTimeout(resolve, 5100));

      const mockFn = jest.fn().mockResolvedValue('success');

      // Circuit breaker requires 2 successful executions to transition from HALF_OPEN to CLOSED
      const result1 = await circuitBreaker.execute(mockFn);
      expect(result1).toBe('success');
      expect(circuitBreaker.get_state()).toBe(CircuitState.HALF_OPEN);

      const result2 = await circuitBreaker.execute(mockFn);
      expect(result2).toBe('success');
      expect(circuitBreaker.get_state()).toBe(CircuitState.CLOSED);
    }, 10000);

    it('should transition back to OPEN on failure', async () => {
      // Wait for reset timeout
      await new Promise((resolve) => setTimeout(resolve, 5100));

      const mockFn = jest.fn().mockRejectedValue(new Error('Still failing'));

      await expect(circuitBreaker.execute(mockFn)).rejects.toThrow(
        'Still failing',
      );

      expect(circuitBreaker.get_state()).toBe(CircuitState.OPEN);
    }, 10000);
  });

  describe('success and failure tracking', () => {
    it('should reset failure count on success', async () => {
      const mockFailFn = jest.fn().mockRejectedValue(new Error('Error'));
      const mockSuccessFn = jest.fn().mockResolvedValue('success');

      // Cause some failures
      try {
        await circuitBreaker.execute(mockFailFn);
      } catch (error) {
        // Expected
      }

      // Success should reset count
      await circuitBreaker.execute(mockSuccessFn);

      // Should still be CLOSED
      expect(circuitBreaker.get_state()).toBe(CircuitState.CLOSED);
    });
  });
});
