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

  describe(&apos;logSecurityEvent&apos;, () => {
    it(&apos;logs security events with correct structure&apos;, () => {
      const consoleSpy = jest.spyOn(console, &apos;log&apos;).mockImplementation();
      
      logSecurityEvent(
        &apos;password_reset&apos;,
        &apos;test_event&apos;,
        &apos;medium&apos;,
        { testData: &apos;value&apos; },
        { ipAddress: &apos;192.168.1.1&apos;, userAgent: &apos;test-agent&apos; }
      );

      expect(consoleSpy).toHaveBeenCalledWith(
        &apos;[SECURITY] password_reset:test_event&apos;,
        expect.objectContaining({
          type: &apos;password_reset&apos;,
          event: &apos;test_event&apos;,
          severity: &apos;medium&apos;,
          details: expect.objectContaining({ testData: &apos;value&apos; }),
          ipAddress: &apos;192.168.1.1&apos;,
          userAgent: &apos;test-agent&apos;,
          timestamp: expect.any(String)
        })
      );

      consoleSpy.mockRestore();
    });

    it(&apos;sanitizes sensitive data from logs&apos;, () => {
      const consoleSpy = jest.spyOn(console, &apos;log&apos;).mockImplementation();
      
      logSecurityEvent(
        &apos;password_reset&apos;,
        &apos;test_event&apos;,
        &apos;low&apos;,
        { 
          email: &apos;user@example.com&apos;,
          token: &apos;abcd1234567890abcd1234567890abcd&apos;,
          password: &apos;secret123&apos;
        }
      );

      const loggedEvent = consoleSpy.mock.calls[0][1];
      expect(loggedEvent.details.email).toBe(&apos;us***@example.com&apos;);
      expect(loggedEvent.details.token).toBe(&apos;abcd1234...&apos;);
      expect(loggedEvent.details.password).toBeUndefined();

      consoleSpy.mockRestore();
    });
  });

  describe(&apos;getSecurityMetrics&apos;, () => {
    it(&apos;returns metrics for recent events&apos;, () => {
      // Log some test events
      logSecurityEvent(&apos;password_reset&apos;, &apos;request&apos;, &apos;low&apos;, {}, { ipAddress: &apos;192.168.1.1&apos; });
      logSecurityEvent(&apos;password_reset&apos;, &apos;validate&apos;, &apos;medium&apos;, {}, { ipAddress: &apos;192.168.1.2&apos; });
      logSecurityEvent(&apos;suspicious_activity&apos;, &apos;pattern_detected&apos;, &apos;high&apos;, {});

      const metrics = getSecurityMetrics();

      expect(metrics.totalEvents).toBeGreaterThan(0);
      expect(metrics.eventsByType).toBeDefined();
      expect(metrics.eventsBySeverity).toBeDefined();
      expect(metrics.topIPs).toBeDefined();
      expect(metrics.recentAlerts).toBeDefined();
    });

    it(&apos;counts events by type and severity correctly&apos;, () => {
      logSecurityEvent(&apos;password_reset&apos;, &apos;request&apos;, &apos;low&apos;);
      logSecurityEvent(&apos;password_reset&apos;, &apos;request&apos;, &apos;medium&apos;);
      logSecurityEvent(&apos;password_reset&apos;, &apos;validate&apos;, &apos;high&apos;);

      const metrics = getSecurityMetrics();

      expect(metrics.eventsByType.request).toBe(2);
      expect(metrics.eventsByType.validate).toBe(1);
      expect(metrics.eventsBySeverity.low).toBe(1);
      expect(metrics.eventsBySeverity.medium).toBe(1);
      expect(metrics.eventsBySeverity.high).toBe(1);
    });
  });

  describe(&apos;shouldBlockIP&apos;, () => {
    it(&apos;blocks IP with recent high-severity events&apos;, () => {
      const testIP = &apos;192.168.1.100&apos;;
      
      logSecurityEvent(&apos;suspicious_activity&apos;, &apos;pattern_detected&apos;, &apos;high&apos;, {}, { ipAddress: testIP });
      
      expect(shouldBlockIP(testIP)).toBe(true);
    });

    it(&apos;does not block IP with only low-severity events&apos;, () => {
      const testIP = &apos;192.168.1.101&apos;;
      
      logSecurityEvent(&apos;password_reset&apos;, &apos;request&apos;, &apos;low&apos;, {}, { ipAddress: testIP });
      
      expect(shouldBlockIP(testIP)).toBe(false);
    });
  });

  describe(&apos;recordPerformanceMetric&apos;, () => {
    it(&apos;records performance metrics correctly&apos;, () => {
      const startTime = Date.now() - 1000; // 1 second ago
      
      recordPerformanceMetric(&apos;test_operation&apos;, startTime, true, { extra: &apos;data&apos; });
      
      const metrics = getPerformanceMetrics();
      expect(metrics).toBeDefined();
    });

    it(&apos;logs slow operations as security events&apos;, () => {
      const consoleSpy = jest.spyOn(console, &apos;log&apos;).mockImplementation();
      const startTime = Date.now() - 6000; // 6 seconds ago (slow)
      
      recordPerformanceMetric(&apos;slow_operation&apos;, startTime, true);
      
      // Should log a security event for slow operation
      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining(&apos;[SECURITY]&apos;),
        expect.objectContaining({
          event: &apos;slow_operation&apos;,
          details: expect.objectContaining({
            operation: &apos;slow_operation&apos;,
            duration: expect.any(Number)
          })
        })
      );

      consoleSpy.mockRestore();
    });
  });

  describe(&apos;getPerformanceMetrics&apos;, () => {
    it(&apos;returns performance metrics for tracked operations&apos;, () => {
      const startTime = Date.now() - 100;
      
      recordPerformanceMetric(&apos;email_send&apos;, startTime, true);
      recordPerformanceMetric(&apos;token_validation&apos;, startTime, false);
      
      const metrics = getPerformanceMetrics();
      
      expect(metrics.email_send).toBeDefined();
      expect(metrics.email_send.averageResponseTime).toBeGreaterThan(0);
      expect(metrics.email_send.successRate).toBe(100);
      
      expect(metrics.token_validation).toBeDefined();
      expect(metrics.token_validation.successRate).toBe(0);
    });
  });

  describe(&apos;withPerformanceMonitoring&apos;, () => {
    it(&apos;wraps async operations with performance monitoring&apos;, async () => {
      const mockOperation = jest.fn().mockResolvedValue(&apos;success&apos;);
      
      const result = await withPerformanceMonitoring(
        &apos;test_operation&apos;,
        mockOperation,
        { context: &apos;test&apos; }
      );
      
      expect(result).toBe(&apos;success&apos;);
      expect(mockOperation).toHaveBeenCalled();
    });

    it(&apos;records performance metrics for successful operations&apos;, async () => {
      const mockOperation = jest.fn().mockResolvedValue(&apos;success&apos;);
      
      await withPerformanceMonitoring(&apos;test_success&apos;, mockOperation);
      
      const metrics = getPerformanceMetrics();
      expect(metrics.test_success).toBeDefined();
    });

    it(&apos;records performance metrics for failed operations&apos;, async () => {
      const mockOperation = jest.fn().mockRejectedValue(new Error(&apos;Test error&apos;));
      
      await expect(
        withPerformanceMonitoring(&apos;test_failure&apos;, mockOperation)
      ).rejects.toThrow(&apos;Test error&apos;);
      
      const metrics = getPerformanceMetrics();
      expect(metrics.test_failure).toBeDefined();
    });
  });

  describe(&apos;SUSPICIOUS_PATTERNS&apos;, () => {
    it(&apos;defines expected suspicious activity patterns&apos;, () => {
      expect(SUSPICIOUS_PATTERNS.RAPID_RESET_REQUESTS).toBeDefined();
      expect(SUSPICIOUS_PATTERNS.RAPID_RESET_REQUESTS.type).toBe(&apos;rapid_requests&apos;);
      expect(SUSPICIOUS_PATTERNS.RAPID_RESET_REQUESTS.threshold).toBeGreaterThan(0);
      expect(SUSPICIOUS_PATTERNS.RAPID_RESET_REQUESTS.timeWindow).toBeGreaterThan(0);

      expect(SUSPICIOUS_PATTERNS.INVALID_TOKEN_ATTEMPTS).toBeDefined();
      expect(SUSPICIOUS_PATTERNS.EMAIL_ENUMERATION).toBeDefined();
      expect(SUSPICIOUS_PATTERNS.BRUTE_FORCE_TOKENS).toBeDefined();
    });
  });

  describe(&apos;suspicious activity detection&apos;, () => {
    it(&apos;detects rapid password reset requests&apos;, () => {
      const consoleSpy = jest.spyOn(console, &apos;warn&apos;).mockImplementation();
      const testIP = &apos;192.168.1.200&apos;;
      
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
      const consoleSpy = jest.spyOn(console, &apos;warn&apos;).mockImplementation();
      const testIP = &apos;192.168.1.201&apos;;
      
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