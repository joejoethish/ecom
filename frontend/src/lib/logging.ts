/**
 * Frontend Logging Service
 * Provides structured logging for user interactions and API calls with correlation ID support
 */

export interface LogEntry {
  timestamp: string;
  level: 'debug' | 'info' | 'warn' | 'error';
  message: string;
  correlationId?: string;
  userId?: string;
  sessionId?: string;
  context?: Record<string, any>;
  stack?: string;
}

export interface APILogEntry extends LogEntry {
  method: string;
  url: string;
  requestBody?: any;
  responseStatus?: number;
  responseTime?: number;
  responseBody?: any;
}

export interface UserInteractionLogEntry extends LogEntry {
  action: string;
  component: string;
  elementId?: string;
  pageUrl: string;
  userAgent: string;
}

class LoggingService {
  private correlationId: string | null = null;
  private userId: string | null = null;
  private sessionId: string | null = null;
  private logBuffer: LogEntry[] = [];
  private maxBufferSize = 100;
  private flushInterval = 5000; // 5 seconds
  private flushTimer: NodeJS.Timeout | null = null;

  constructor() {
    this.initializeSession();
    this.startPeriodicFlush();
  }

  private initializeSession(): void {
    // Generate session ID if not exists
    this.sessionId = sessionStorage.getItem('sessionId') || this.generateId();
    sessionStorage.setItem('sessionId', this.sessionId);

    // Get correlation ID from current request context
    this.correlationId = this.getCorrelationIdFromHeaders();
  }

  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private getCorrelationIdFromHeaders(): string | null {
    // Try to get correlation ID from meta tag set by server
    const metaTag = document.querySelector('meta[name="correlation-id"]');
    return metaTag?.getAttribute('content') || null;
  }

  setCorrelationId(correlationId: string): void {
    this.correlationId = correlationId;
  }

  setUserId(userId: string): void {
    this.userId = userId;
  }

  private createBaseLogEntry(level: LogEntry['level'], message: string, context?: Record<string, any>): LogEntry {
    return {
      timestamp: new Date().toISOString(),
      level,
      message,
      correlationId: this.correlationId || undefined,
      userId: this.userId || undefined,
      sessionId: this.sessionId || undefined,
      context
    };
  }

  debug(message: string, context?: Record<string, any>): void {
    const entry = this.createBaseLogEntry('debug', message, context);
    this.addToBuffer(entry);
    console.debug('[DEBUG]', message, context);
  }

  info(message: string, context?: Record<string, any>): void {
    const entry = this.createBaseLogEntry('info', message, context);
    this.addToBuffer(entry);
    console.info('[INFO]', message, context);
  }

  warn(message: string, context?: Record<string, any>): void {
    const entry = this.createBaseLogEntry('warn', message, context);
    this.addToBuffer(entry);
    console.warn('[WARN]', message, context);
  }

  error(message: string, error?: Error, context?: Record<string, any>): void {
    const entry = this.createBaseLogEntry('error', message, context);
    if (error) {
      entry.stack = error.stack;
    }
    this.addToBuffer(entry);
    console.error('[ERROR]', message, error, context);
  }

  logAPICall(
    method: string,
    url: string,
    requestBody?: any,
    responseStatus?: number,
    responseTime?: number,
    responseBody?: any
  ): void {
    const entry: APILogEntry = {
      ...this.createBaseLogEntry('info', `API Call: ${method} ${url}`),
      method,
      url,
      requestBody,
      responseStatus,
      responseTime,
      responseBody
    };
    this.addToBuffer(entry);
  }

  logUserInteraction(
    action: string,
    component: string,
    elementId?: string,
    context?: Record<string, any>
  ): void {
    const entry: UserInteractionLogEntry = {
      ...this.createBaseLogEntry('info', `User Interaction: ${action} on ${component}`),
      action,
      component,
      elementId,
      pageUrl: window.location.href,
      userAgent: navigator.userAgent,
      context
    };
    this.addToBuffer(entry);
  }

  private addToBuffer(entry: LogEntry): void {
    this.logBuffer.push(entry);
    
    if (this.logBuffer.length >= this.maxBufferSize) {
      this.flush();
    }
  }

  private startPeriodicFlush(): void {
    this.flushTimer = setInterval(() => {
      if (this.logBuffer.length > 0) {
        this.flush();
      }
    }, this.flushInterval);
  }

  private async flush(): Promise<void> {
    if (this.logBuffer.length === 0) return;

    const logsToSend = [...this.logBuffer];
    this.logBuffer = [];

    try {
      await fetch('/api/logs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(this.correlationId && { 'X-Correlation-ID': this.correlationId })
        },
        body: JSON.stringify({ logs: logsToSend })
      });
    } catch (error) {
      console.error('Failed to send logs to server:', error);
      // Re-add logs to buffer for retry
      this.logBuffer.unshift(...logsToSend);
    }
  }

  destroy(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
      this.flushTimer = null;
    }
    this.flush(); // Final flush
  }
}

// Create singleton instance
export const logger = new LoggingService();

// API call interceptor for automatic logging
export const createAPILogger = () => {
  const originalFetch = window.fetch;
  
  window.fetch = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const startTime = Date.now();
    const url = typeof input === 'string' ? input : input.toString();
    const method = init?.method || 'GET';
    
    try {
      const response = await originalFetch(input, init);
      const responseTime = Date.now() - startTime;
      
      logger.logAPICall(
        method,
        url,
        init?.body,
        response.status,
        responseTime
      );
      
      return response;
    } catch (error) {
      const responseTime = Date.now() - startTime;
      logger.logAPICall(method, url, init?.body, 0, responseTime);
      logger.error(`API call failed: ${method} ${url}`, error as Error);
      throw error;
    }
  };
};

// React hook for component logging
export const useLogger = () => {
  return {
    debug: logger.debug.bind(logger),
    info: logger.info.bind(logger),
    warn: logger.warn.bind(logger),
    error: logger.error.bind(logger),
    logUserInteraction: logger.logUserInteraction.bind(logger)
  };
};