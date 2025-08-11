import {
  logSecurityEvent,
  getSecurityMetrics,
  shouldBlockIP,
  recordPerformanceMetric,
  getPerformanceMetrics,
  withPerformanceMonitoring,
  SUSPICIOUS_PATTERNS,
} from '../securityMonitoring';

describe('securityMonitoring', () => {
  beforeEach(() => {
    // Clear any existing events
    jest.clearAllMocks();
  });

  describe('logSecurityEvent', () => {
    it('logs security events with correct structure', () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
      
      logSecurityEvent(
        'password_reset',
        'test_event',
        'medium',
        { testData: 'value' },
        { ipAddress: '192.168.1.1', userAgent: 'test-agent' }
      );

      expect(consoleSpy).toHaveBeenCalledWith(
        '[SECURITY] password_reset:test_event',
        expect.objectContaining({
          type: 'password_reset',
          event: 'test_event',
          severity: 'medium',
          details: expect.objectContaining({ testData: 'value' }),
          ipAddress: '192.168.1.1',
          userAgent: 'test-agent',
          timestamp: expect.any(String)
        })
      );

      consoleSpy.mockRestore();
    });

    it('sanitizes sensitive data from logs', () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
      
      logSecurityEvent(
        'password_reset',
        'test_event',
        'low',
        { 
          email: 'user@example.com',
          token: 'abcd1234567890abcd1234567890abcd',
          password: 'secret123'
        }
      );

      const loggedEvent = consoleSpy.mock.calls[0][1];
      expect(loggedEvent.details.email).toBe('us***@example.com');
      expect(loggedEvent.details.token).toBe('abcd1234...');
      expect(loggedEvent.details.password).toBeUndefined();

      consoleSpy.mockRestore();
    });
  });

  describe('getSecurityMetrics', () => {
    it('returns metrics for recent events', () => {
      // Log some test events
      logSecurityEvent('password_reset', 'request', 'low', {}, { ipAddress: '192.168.1.1' });
      logSecurityEvent('password_reset', 'validate', 'medium', {}, { ipAddress: '192.168.1.2' });
      logSecurityEvent('suspicious_activity', 'pattern_detected', 'high', {});

      const metrics = getSecurityMetrics();

      expect(metrics.totalEvents).toBeGreaterThan(0);
      expect(metrics.eventsByType).toBeDefined();
      expect(metrics.eventsBySeverity).toBeDefined();
      expect(metrics.topIPs).toBeDefined();
      expect(metrics.recentAlerts).toBeDefined();
    });

    it('counts events by type and severity correctly', () => {
      logSecurityEvent('password_reset', 'request', 'low');
      logSecurityEvent('password_reset', 'request', 'medium');
      logSecurityEvent('password_reset', 'validate', 'high');

      const metrics = getSecurityMetrics();

      expect(metrics.eventsByType.request).toBe(2);
      expect(metrics.eventsByType.validate).toBe(1);
      expect(metrics.eventsBySeverity.low).toBe(1);
      expect(metrics.eventsBySeverity.medium).toBe(1);
      expect(metrics.eventsBySeverity.high).toBe(1);
    });
  });

  describe('shouldBlockIP', () => {
    it('blocks IP with recent high-severity events', () => {
      const testIP = '192.168.1.100';
      
      logSecurityEvent('suspicious_activity', 'pattern_detected', 'high', {}, { ipAddress: testIP });
      
      expect(shouldBlockIP(testIP)).toBe(true);
    });

    it('does not block IP with only low-severity events', () => {
      const testIP = '192.168.1.101';
      
      logSecurityEvent('password_reset', 'request', 'low', {}, { ipAddress: testIP });
      
      expect(shouldBlockIP(testIP)).toBe(false);
    });
  });

  describe('recordPerformanceMetric', () => {
    it('records performance metrics correctly', () => {
      const startTime = Date.now() - 1000; // 1 second ago
      
      recordPerformanceMetric('test_operation', startTime, true, { extra: 'data' });
      
      const metrics = getPerformanceMetrics();
      expect(metrics).toBeDefined();
    });

    it('logs slow operations as security events', () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
      const startTime = Date.now() - 6000; // 6 seconds ago (slow)
      
      recordPerformanceMetric('slow_operation', startTime, true);
      
      // Should log a security event for slow operation
      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('[SECURITY]'),
        expect.objectContaining({
          event: 'slow_operation',
          details: expect.objectContaining({
            operation: 'slow_operation',
            duration: expect.any(Number)
          })
        })
      );

      consoleSpy.mockRestore();
    });
  });

  describe('getPerformanceMetrics', () => {
    it('returns performance metrics for tracked operations', () => {
      const startTime = Date.now() - 100;
      
      recordPerformanceMetric('email_send', startTime, true);
      recordPerformanceMetric('token_validation', startTime, false);
      
      const metrics = getPerformanceMetrics();
      
      expect(metrics.email_send).toBeDefined();
      expect(metrics.email_send.averageResponseTime).toBeGreaterThan(0);
      expect(metrics.email_send.successRate).toBe(100);
      
      expect(metrics.token_validation).toBeDefined();
      expect(metrics.token_validation.successRate).toBe(0);
    });
  });

  describe('withPerformanceMonitoring', () => {
    it('wraps async operations with performance monitoring', async () => {
      const mockOperation = jest.fn().mockResolvedValue('success');
      
      const result = await withPerformanceMonitoring(
        'test_operation',
        mockOperation,
        { context: 'test' }
      );
      
      expect(result).toBe('success');
      expect(mockOperation).toHaveBeenCalled();
    });

    it('records performance metrics for successful operations', async () => {
      const mockOperation = jest.fn().mockResolvedValue('success');
      
      await withPerformanceMonitoring('test_success', mockOperation);
      
      const metrics = getPerformanceMetrics();
      expect(metrics.test_success).toBeDefined();
    });

    it('records performance metrics for failed operations', async () => {
      const mockOperation = jest.fn().mockRejectedValue(new Error('Test error'));
      
      await expect(
        withPerformanceMonitoring('test_failure', mockOperation)
      ).rejects.toThrow('Test error');
      
      const metrics = getPerformanceMetrics();
      expect(metrics.test_failure).toBeDefined();
    });
  });

  describe('SUSPICIOUS_PATTERNS', () => {
    it('defines expected suspicious activity patterns', () => {
      expect(SUSPICIOUS_PATTERNS.RAPID_RESET_REQUESTS).toBeDefined();
      expect(SUSPICIOUS_PATTERNS.RAPID_RESET_REQUESTS.type).toBe('rapid_requests');
      expect(SUSPICIOUS_PATTERNS.RAPID_RESET_REQUESTS.threshold).toBeGreaterThan(0);
      expect(SUSPICIOUS_PATTERNS.RAPID_RESET_REQUESTS.timeWindow).toBeGreaterThan(0);

      expect(SUSPICIOUS_PATTERNS.INVALID_TOKEN_ATTEMPTS).toBeDefined();
      expect(SUSPICIOUS_PATTERNS.EMAIL_ENUMERATION).toBeDefined();
      expect(SUSPICIOUS_PATTERNS.BRUTE_FORCE_TOKENS).toBeDefined();
    });
  });

  describe('suspicious activity detection', () => {
    it('detects rapid password reset requests', () => {
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();
      const testIP = '192.168.1.200';
      
      // Simulate rapid requests exceeding threshold
      for (let i = 0; i < 6; i++) {
        logSecurityEvent(
          'password_reset',
          'password_reset_request',
          'low',
          {},
          { ipAddress: testIP }
        );
      }
      
      // Should trigger suspicious activity alert
      expect(consoleSpy).toHaveBeenCalledWith(
        '🚨 SECURITY ALERT:',
        expect.objectContaining({
          type: 'suspicious_activity',
          event: 'pattern_detected',
          severity: 'high'
        })
      );

      consoleSpy.mockRestore();
    });

    it('detects invalid token attempts', () => {
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();
      const testIP = '192.168.1.201';
      
      // Simulate multiple invalid token attempts
      for (let i = 0; i < 11; i++) {
        logSecurityEvent(
          'password_reset',
          'token_validation',
          'medium',
          { success: false },
          { ipAddress: testIP }
        );
      }
      
      // Should trigger suspicious activity alert
      expect(consoleSpy).toHaveBeenCalledWith(
        '🚨 SECURITY ALERT:',
        expect.objectContaining({
          details: expect.objectContaining({
            pattern: 'INVALID_TOKEN_ATTEMPTS'
          })
        })
      );

      consoleSpy.mockRestore();
    });
  });
});