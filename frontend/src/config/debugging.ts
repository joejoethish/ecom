/**
 * Configuration for the E2E Workflow Debugging System frontend
 */

export interface DebuggingConfig {
  enabled: boolean;
  apiBaseUrl: string;
  websocketUrl: string;
  dashboardPath: string;
  realTimeUpdates: boolean;
  updateInterval: number;
  maxRetries: number;
  retryDelay: number;
  correlationIdHeader: string;
  features: {
    performanceMonitoring: boolean;
    workflowTracing: boolean;
    errorTracking: boolean;
    routeDiscovery: boolean;
    apiValidation: boolean;
    databaseMonitoring: boolean;
    realTimeDashboard: boolean;
    websocketConnection: boolean;
  };
  dashboard: {
    theme: 'light' | 'dark' | 'auto';
    autoRefresh: boolean;
    refreshInterval: number;
    maxDataPoints: number;
    chartAnimations: boolean;
    compactMode: boolean;
  };
  performance: {
    thresholds: {
      apiResponseTimeWarning: number;
      apiResponseTimeCritical: number;
      frontendRenderTimeWarning: number;
      frontendRenderTimeCritical: number;
      memoryUsageWarning: number;
      memoryUsageCritical: number;
      errorRateWarning: number;
      errorRateCritical: number;
    };
    monitoring: {
      enabled: boolean;
      sampleRate: number;
      batchSize: number;
      flushInterval: number;
    };
  };
  security: {
    apiKeyRequired: boolean;
    corsEnabled: boolean;
    rateLimitingEnabled: boolean;
    sensitiveDataMasking: boolean;
  };
}

// Default configuration
const defaultConfig: DebuggingConfig = {
  enabled: process.env.NEXT_PUBLIC_DEBUGGING_ENABLED === 'true',
  apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
  websocketUrl: process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'ws://localhost:8000/ws',
  dashboardPath: process.env.NEXT_PUBLIC_DEBUGGING_DASHBOARD_PATH || '/debug',
  realTimeUpdates: true,
  updateInterval: 5000, // 5 seconds
  maxRetries: 3,
  retryDelay: 1000, // 1 second
  correlationIdHeader: 'X-Correlation-ID',
  features: {
    performanceMonitoring: true,
    workflowTracing: true,
    errorTracking: true,
    routeDiscovery: true,
    apiValidation: true,
    databaseMonitoring: true,
    realTimeDashboard: true,
    websocketConnection: true,
  },
  dashboard: {
    theme: 'auto',
    autoRefresh: true,
    refreshInterval: 5000, // 5 seconds
    maxDataPoints: 100,
    chartAnimations: true,
    compactMode: false,
  },
  performance: {
    thresholds: {
      apiResponseTimeWarning: 500, // ms
      apiResponseTimeCritical: 2000, // ms
      frontendRenderTimeWarning: 100, // ms
      frontendRenderTimeCritical: 500, // ms
      memoryUsageWarning: 80, // percentage
      memoryUsageCritical: 95, // percentage
      errorRateWarning: 5, // percentage
      errorRateCritical: 10, // percentage
    },
    monitoring: {
      enabled: true,
      sampleRate: 1.0, // 100% sampling in development
      batchSize: 10,
      flushInterval: 10000, // 10 seconds
    },
  },
  security: {
    apiKeyRequired: false,
    corsEnabled: true,
    rateLimitingEnabled: false,
    sensitiveDataMasking: true,
  },
};

// Environment-specific configurations
const environmentConfigs: Record<string, Partial<DebuggingConfig>> = {
  development: {
    enabled: true,
    realTimeUpdates: true,
    features: {
      performanceMonitoring: true,
      workflowTracing: true,
      errorTracking: true,
      routeDiscovery: true,
      apiValidation: true,
      databaseMonitoring: true,
      realTimeDashboard: true,
      websocketConnection: true,
    },
    dashboard: {
      theme: 'auto' as const,
      autoRefresh: true,
      refreshInterval: 2000, // 2 seconds for faster development feedback
      maxDataPoints: 100,
      chartAnimations: true,
      compactMode: false,
    },
    performance: {
      thresholds: {
        apiResponseTimeWarning: 500,
        apiResponseTimeCritical: 2000,
        frontendRenderTimeWarning: 100,
        frontendRenderTimeCritical: 500,
        memoryUsageWarning: 80,
        memoryUsageCritical: 95,
        errorRateWarning: 5,
        errorRateCritical: 10,
      },
      monitoring: {
        enabled: true,
        sampleRate: 1.0, // 100% sampling
        batchSize: 50,
        flushInterval: 5000, // 5 seconds
      },
    },
    security: {
      apiKeyRequired: false,
      corsEnabled: true,
      rateLimitingEnabled: false,
      sensitiveDataMasking: false,
    },
  },
  production: {
    enabled: false, // Disabled by default in production
    realTimeUpdates: false,
    features: {
      performanceMonitoring: true,
      workflowTracing: false, // Disabled for performance
      errorTracking: true,
      routeDiscovery: false, // Disabled in production
      apiValidation: false, // Disabled in production
      databaseMonitoring: true,
      realTimeDashboard: false,
      websocketConnection: false,
    },
    dashboard: {
      theme: 'light' as const,
      autoRefresh: false,
      refreshInterval: 30000, // 30 seconds
      maxDataPoints: 50,
      chartAnimations: false, // Disabled for performance
      compactMode: true,
    },
    performance: {
      thresholds: {
        apiResponseTimeWarning: 1000,
        apiResponseTimeCritical: 5000,
        frontendRenderTimeWarning: 200,
        frontendRenderTimeCritical: 1000,
        memoryUsageWarning: 85,
        memoryUsageCritical: 95,
        errorRateWarning: 2,
        errorRateCritical: 5,
      },
      monitoring: {
        enabled: true,
        sampleRate: 0.1, // 10% sampling
        batchSize: 100,
        flushInterval: 30000, // 30 seconds
      },
    },
    security: {
      apiKeyRequired: true,
      corsEnabled: false,
      rateLimitingEnabled: true,
      sensitiveDataMasking: true,
    },
  },
  testing: {
    enabled: false,
    realTimeUpdates: false,
    features: {
      performanceMonitoring: false,
      workflowTracing: false,
      errorTracking: false,
      routeDiscovery: false,
      apiValidation: false,
      databaseMonitoring: false,
      realTimeDashboard: false,
      websocketConnection: false,
    },
    performance: {
      thresholds: {
        apiResponseTimeWarning: 1000,
        apiResponseTimeCritical: 5000,
        frontendRenderTimeWarning: 200,
        frontendRenderTimeCritical: 1000,
        memoryUsageWarning: 85,
        memoryUsageCritical: 95,
        errorRateWarning: 2,
        errorRateCritical: 5,
      },
      monitoring: {
        enabled: false,
        sampleRate: 0,
        batchSize: 10,
        flushInterval: 1000,
      },
    },
  },
};

// Get current environment
function getCurrentEnvironment(): string {
  if (process.env.NODE_ENV === 'test') return 'testing';
  if (process.env.NODE_ENV === 'production') return 'production';
  return 'development';
}

// Merge configurations
function mergeConfigs(base: DebuggingConfig, override: Partial<DebuggingConfig>): DebuggingConfig {
  return {
    ...base,
    ...override,
    features: {
      ...base.features,
      ...override.features,
    },
    dashboard: {
      ...base.dashboard,
      ...override.dashboard,
    },
    performance: {
      ...base.performance,
      ...override.performance,
      thresholds: {
        ...base.performance.thresholds,
        ...override.performance?.thresholds,
      },
      monitoring: {
        ...base.performance.monitoring,
        ...override.performance?.monitoring,
      },
    },
    security: {
      ...base.security,
      ...override.security,
    },
  };
}

// Create final configuration
const environment = getCurrentEnvironment();
const environmentConfig = environmentConfigs[environment] || {};
export const debuggingConfig = mergeConfigs(defaultConfig, environmentConfig);

// Configuration utilities
export class DebuggingConfigManager {
  private static instance: DebuggingConfigManager;
  private config: DebuggingConfig;
  private listeners: Array<(config: DebuggingConfig) => void> = [];

  private constructor() {
    this.config = debuggingConfig;
  }

  static getInstance(): DebuggingConfigManager {
    if (!DebuggingConfigManager.instance) {
      DebuggingConfigManager.instance = new DebuggingConfigManager();
    }
    return DebuggingConfigManager.instance;
  }

  getConfig(): DebuggingConfig {
    return this.config;
  }

  updateConfig(updates: Partial<DebuggingConfig>): void {
    this.config = mergeConfigs(this.config, updates);
    this.notifyListeners();
  }

  isFeatureEnabled(feature: keyof DebuggingConfig['features']): boolean {
    return this.config.enabled && this.config.features[feature];
  }

  getApiUrl(endpoint: string): string {
    return `${this.config.apiBaseUrl}${endpoint}`;
  }

  getWebSocketUrl(path: string = ''): string {
    return `${this.config.websocketUrl}${path}`;
  }

  getDashboardUrl(path: string = ''): string {
    return `${this.config.dashboardPath}${path}`;
  }

  getPerformanceThreshold(metric: string, level: 'warning' | 'critical'): number {
    const key = `${metric}${level.charAt(0).toUpperCase() + level.slice(1)}` as keyof DebuggingConfig['performance']['thresholds'];
    return this.config.performance.thresholds[key] || 0;
  }

  subscribe(listener: (config: DebuggingConfig) => void): () => void {
    this.listeners.push(listener);
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  private notifyListeners(): void {
    this.listeners.forEach(listener => listener(this.config));
  }
}

// Export singleton instance
export const configManager = DebuggingConfigManager.getInstance();

// Export configuration validation
export function validateConfig(config: DebuggingConfig): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  // Validate URLs
  try {
    new URL(config.apiBaseUrl);
  } catch {
    errors.push('Invalid API base URL');
  }

  // Validate thresholds
  const { thresholds } = config.performance;
  if (thresholds.apiResponseTimeWarning >= thresholds.apiResponseTimeCritical) {
    errors.push('API response time warning threshold must be less than critical threshold');
  }
  if (thresholds.frontendRenderTimeWarning >= thresholds.frontendRenderTimeCritical) {
    errors.push('Frontend render time warning threshold must be less than critical threshold');
  }
  if (thresholds.memoryUsageWarning >= thresholds.memoryUsageCritical) {
    errors.push('Memory usage warning threshold must be less than critical threshold');
  }
  if (thresholds.errorRateWarning >= thresholds.errorRateCritical) {
    errors.push('Error rate warning threshold must be less than critical threshold');
  }

  // Validate intervals
  if (config.updateInterval < 1000) {
    errors.push('Update interval must be at least 1000ms');
  }
  if (config.dashboard.refreshInterval < 1000) {
    errors.push('Dashboard refresh interval must be at least 1000ms');
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}