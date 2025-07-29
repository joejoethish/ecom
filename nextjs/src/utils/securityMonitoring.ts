/**
 * Security monitoring and logging utilities for password reset system
 */

export interface SecurityEvent {
  type: 'password_reset' | 'suspicious_activity' | 'rate_limit' | 'token_validation';
  event: string;
  timestamp: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  details: Record<string, any>;
  userAgent?: string;
  ipAddress?: string;
  sessionId?: string;
}

export interface SuspiciousActivityPattern {
  type: 'rapid_requests' | 'invalid_tokens' | 'email_enumeration' | 'brute_force';
  threshold: number;
  timeWindow: number; // in milliseconds
  description: string;
}

/**
 * Suspicious activity patterns to monitor
 */
export const SUSPICIOUS_PATTERNS: Record<string, SuspiciousActivityPattern> = {
  RAPID_RESET_REQUESTS: {
    type: 'rapid_requests',
    threshold: 5,
    timeWindow: 5 * 60 * 1000, // 5 minutes
    description: 'Multiple password reset requests in short time'
  },
  INVALID_TOKEN_ATTEMPTS: {
    type: 'invalid_tokens',
    threshold: 10,
    timeWindow: 10 * 60 * 1000, // 10 minutes
    description: 'Multiple invalid token validation attempts'
  },
  EMAIL_ENUMERATION: {
    type: 'email_enumeration',
    threshold: 20,
    timeWindow: 15 * 60 * 1000, // 15 minutes
    description: 'Potential email enumeration attack'
  },
  BRUTE_FORCE_TOKENS: {
    type: 'brute_force',
    threshold: 50,
    timeWindow: 30 * 60 * 1000, // 30 minutes
    description: 'Potential brute force token attack'
  }
} as const;

/**
 * In-memory storage for tracking security events (in production, use Redis or database)
 */
class SecurityEventTracker {
  private events: SecurityEvent[] = [];
  private readonly maxEvents = 10000; // Keep last 10k events in memory

  addEvent(event: SecurityEvent): void {
    this.events.push(event);
    
    // Keep only recent events to prevent memory issues
    if (this.events.length > this.maxEvents) {
      this.events = this.events.slice(-this.maxEvents);
    }
    
    // Check for suspicious patterns
    this.checkSuspiciousActivity(event);
  }

  getRecentEvents(timeWindow: number = 60 * 60 * 1000): SecurityEvent[] {
    const cutoff = Date.now() - timeWindow;
    return this.events.filter(event => 
      new Date(event.timestamp).getTime() > cutoff
    );
  }

  getEventsByType(type: string, timeWindow: number = 60 * 60 * 1000): SecurityEvent[] {
    return this.getRecentEvents(timeWindow).filter(event => 
      event.event === type
    );
  }

  getEventsByIP(ipAddress: string, timeWindow: number = 60 * 60 * 1000): SecurityEvent[] {
    return this.getRecentEvents(timeWindow).filter(event => 
      event.ipAddress === ipAddress
    );
  }

  private checkSuspiciousActivity(newEvent: SecurityEvent): void {
    const ipAddress = newEvent.ipAddress;
    if (!ipAddress) return;

    // Check each suspicious pattern
    Object.entries(SUSPICIOUS_PATTERNS).forEach(([patternName, pattern]) => {
      const recentEvents = this.getEventsByIP(ipAddress, pattern.timeWindow);
      const relevantEvents = this.filterEventsByPattern(recentEvents, pattern);
      
      if (relevantEvents.length >= pattern.threshold) {
        this.triggerSuspiciousActivityAlert(patternName, pattern, ipAddress, relevantEvents);
      }
    });
  }

  private filterEventsByPattern(events: SecurityEvent[], pattern: SuspiciousActivityPattern): SecurityEvent[] {
    switch (pattern.type) {
      case 'rapid_requests':
        return events.filter(e => e.event === 'password_reset_request');
      case 'invalid_tokens':
        return events.filter(e => 
          e.event === 'token_validation' && 
          e.details.success === false
        );
      case 'email_enumeration':
        return events.filter(e => e.event === 'password_reset_request');
      case 'brute_force':
        return events.filter(e => 
          e.event === 'token_validation' && 
          e.details.success === false
        );
      default:
        return [];
    }
  }

  private triggerSuspiciousActivityAlert(
    patternName: string, 
    pattern: SuspiciousActivityPattern, 
    ipAddress: string, 
    events: SecurityEvent[]
  ): void {
    const alertEvent: SecurityEvent = {
      type: 'suspicious_activity',
      event: 'pattern_detected',
      timestamp: new Date().toISOString(),
      severity: 'high',
      details: {
        pattern: patternName,
        description: pattern.description,
        threshold: pattern.threshold,
        actualCount: events.length,
        timeWindow: pattern.timeWindow,
        affectedIP: ipAddress,
        eventSample: events.slice(0, 5) // Include sample of events
      },
      ipAddress
    };

    this.addEvent(alertEvent);
    this.notifyAdministrators(alertEvent);
  }

  private notifyAdministrators(alertEvent: SecurityEvent): void {
    if (process.env.NODE_ENV === 'development') {
      console.warn('🚨 SECURITY ALERT:', alertEvent);
    }
    
    // In production, send to monitoring service, email admins, etc.
    // this.sendToMonitoringService(alertEvent);
    // this.emailSecurityTeam(alertEvent);
  }
}

// Singleton instance
const securityTracker = new SecurityEventTracker();

/**
 * Log a security event
 */
export const logSecurityEvent = (
  type: SecurityEvent['type'],
  event: string,
  severity: SecurityEvent['severity'] = 'low',
  details: Record<string, any> = {},
  context?: {
    userAgent?: string;
    ipAddress?: string;
    sessionId?: string;
  }
): void => {
  const securityEvent: SecurityEvent = {
    type,
    event,
    timestamp: new Date().toISOString(),
    severity,
    details: {
      ...details,
      // Remove or mask sensitive data
      ...sanitizeDetails(details)
    },
    userAgent: context?.userAgent,
    ipAddress: context?.ipAddress,
    sessionId: context?.sessionId
  };

  securityTracker.addEvent(securityEvent);

  // Log to console in development
  if (process.env.NODE_ENV === 'development') {
    const logLevel = severity === 'critical' || severity === 'high' ? 'error' : 'log';
    console[logLevel](`[SECURITY] ${type}:${event}`, securityEvent);
  }
};

/**
 * Sanitize sensitive details from security logs
 */
const sanitizeDetails = (details: Record<string, any>): Record<string, any> => {
  const sanitized = { ...details };
  
  // Mask email addresses
  if (sanitized.email && typeof sanitized.email === 'string') {
    const [local, domain] = sanitized.email.split('@');
    sanitized.email = `${local.substring(0, 2)}***@${domain}`;
  }
  
  // Mask tokens
  if (sanitized.token && typeof sanitized.token === 'string') {
    sanitized.token = `${sanitized.token.substring(0, 8)}...`;
  }
  
  // Remove passwords completely
  delete sanitized.password;
  delete sanitized.newPassword;
  delete sanitized.confirmPassword;
  
  return sanitized;
};

/**
 * Get security metrics for monitoring dashboard
 */
export const getSecurityMetrics = (timeWindow: number = 60 * 60 * 1000) => {
  const recentEvents = securityTracker.getRecentEvents(timeWindow);
  
  const metrics = {
    totalEvents: recentEvents.length,
    eventsByType: {} as Record<string, number>,
    eventsBySeverity: {} as Record<string, number>,
    suspiciousActivityCount: 0,
    topIPs: {} as Record<string, number>,
    recentAlerts: [] as SecurityEvent[]
  };
  
  recentEvents.forEach(event => {
    // Count by type
    metrics.eventsByType[event.event] = (metrics.eventsByType[event.event] || 0) + 1;
    
    // Count by severity
    metrics.eventsBySeverity[event.severity] = (metrics.eventsBySeverity[event.severity] || 0) + 1;
    
    // Count suspicious activity
    if (event.type === 'suspicious_activity') {
      metrics.suspiciousActivityCount++;
      metrics.recentAlerts.push(event);
    }
    
    // Count by IP
    if (event.ipAddress) {
      metrics.topIPs[event.ipAddress] = (metrics.topIPs[event.ipAddress] || 0) + 1;
    }
  });
  
  // Sort recent alerts by timestamp (newest first)
  metrics.recentAlerts.sort((a, b) => 
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
  
  return metrics;
};

/**
 * Check if an IP address should be blocked based on recent activity
 */
export const shouldBlockIP = (ipAddress: string): boolean => {
  const recentEvents = securityTracker.getEventsByIP(ipAddress, 30 * 60 * 1000); // 30 minutes
  
  // Block if there are recent high-severity alerts for this IP
  const highSeverityEvents = recentEvents.filter(event => 
    event.severity === 'high' || event.severity === 'critical'
  );
  
  return highSeverityEvents.length > 0;
};

/**
 * Performance monitoring for password reset operations
 */
export interface PerformanceMetric {
  operation: string;
  duration: number;
  timestamp: string;
  success: boolean;
  details?: Record<string, any>;
}

class PerformanceMonitor {
  private metrics: PerformanceMetric[] = [];
  private readonly maxMetrics = 5000;

  recordMetric(metric: PerformanceMetric): void {
    this.metrics.push(metric);
    
    if (this.metrics.length > this.maxMetrics) {
      this.metrics = this.metrics.slice(-this.maxMetrics);
    }
  }

  getAverageResponseTime(operation: string, timeWindow: number = 60 * 60 * 1000): number {
    const cutoff = Date.now() - timeWindow;
    const relevantMetrics = this.metrics.filter(metric => 
      metric.operation === operation &&
      new Date(metric.timestamp).getTime() > cutoff
    );
    
    if (relevantMetrics.length === 0) return 0;
    
    const totalDuration = relevantMetrics.reduce((sum, metric) => sum + metric.duration, 0);
    return totalDuration / relevantMetrics.length;
  }

  getSuccessRate(operation: string, timeWindow: number = 60 * 60 * 1000): number {
    const cutoff = Date.now() - timeWindow;
    const relevantMetrics = this.metrics.filter(metric => 
      metric.operation === operation &&
      new Date(metric.timestamp).getTime() > cutoff
    );
    
    if (relevantMetrics.length === 0) return 0;
    
    const successCount = relevantMetrics.filter(metric => metric.success).length;
    return (successCount / relevantMetrics.length) * 100;
  }
}

const performanceMonitor = new PerformanceMonitor();

/**
 * Record performance metric for password reset operations
 */
export const recordPerformanceMetric = (
  operation: string,
  startTime: number,
  success: boolean,
  details?: Record<string, any>
): void => {
  const duration = Date.now() - startTime;
  
  performanceMonitor.recordMetric({
    operation,
    duration,
    timestamp: new Date().toISOString(),
    success,
    details
  });
  
  // Log slow operations
  if (duration > 5000) { // 5 seconds
    logSecurityEvent(
      'password_reset',
      'slow_operation',
      'medium',
      { operation, duration, success, ...details }
    );
  }
};

/**
 * Get performance metrics
 */
export const getPerformanceMetrics = () => {
  const operations = ['email_send', 'token_validation', 'password_reset'];
  
  return operations.reduce((metrics, operation) => {
    metrics[operation] = {
      averageResponseTime: performanceMonitor.getAverageResponseTime(operation),
      successRate: performanceMonitor.getSuccessRate(operation)
    };
    return metrics;
  }, {} as Record<string, { averageResponseTime: number; successRate: number }>);
};

/**
 * Utility to wrap async operations with performance monitoring
 */
export const withPerformanceMonitoring = async <T>(
  operation: string,
  asyncFn: () => Promise<T>,
  details?: Record<string, any>
): Promise<T> => {
  const startTime = Date.now();
  let success = false;
  
  try {
    const result = await asyncFn();
    success = true;
    return result;
  } catch (error) {
    success = false;
    throw error;
  } finally {
    recordPerformanceMetric(operation, startTime, success, details);
  }
};