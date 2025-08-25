/**
 * Frontend Workflow Tracing Library
 * 
 * This module provides client-side workflow tracing capabilities that integrate
 * with the backend E2E debugging system using correlation IDs.
 */
import * as React from 'react';
import { v4 as uuidv4 } from 'uuid';

export interface TraceStep {
    layer: 'frontend';
    component: string;
    operation: string;
    startTime: number;
    endTime?: number;
    duration?: number;
    status: 'started' | 'completed' | 'failed';
    metadata?: Record<string, any>;
}

export interface WorkflowTrace {
    correlationId: string;
    workflowType: string;
    startTime: number;
    endTime?: number;
    status: 'in_progress' | 'completed' | 'failed';
    steps: TraceStep[];
    errors: Array<{
        timestamp: number;
        component: string;
        error: string;
        stack?: string;
    }>;
    metadata?: Record<string, any>;
}

export interface PerformanceMetric {
    correlationId: string;
    timestamp: number;
    layer: 'frontend';
    component: string;
    metricName: string;
    metricValue: number;
    metadata?: Record<string, any>;
}

class FrontendWorkflowTracer {
    private activeTraces: Map<string, WorkflowTrace> = new Map();
    private activeSteps: Map<string, TraceStep> = new Map();
    private performanceObserver?: PerformanceObserver;
    private apiEndpoint: string;
    private enabledFeatures: {
        apiTracing: boolean;
        performanceMonitoring: boolean;
        errorTracking: boolean;
        userInteractionTracking: boolean;
    };

    constructor(apiEndpoint: string = '/api/v1/debugging') {
        this.apiEndpoint = apiEndpoint;
        this.enabledFeatures = {
            apiTracing: true,
            performanceMonitoring: true,
            errorTracking: true,
            userInteractionTracking: true,
        };

        this.initializePerformanceMonitoring();
        this.initializeErrorTracking();
        this.initializeApiInterception();
    }

    /**
     * Start a new workflow trace
     */
    startWorkflow(workflowType: string, metadata?: Record<string, any>): string {
        const correlationId = uuidv4();

        const trace: WorkflowTrace = {
            correlationId,
            workflowType,
            startTime: performance.now(),
            status: 'in_progress',
            steps: [],
            errors: [],
            metadata: metadata || {}
        };

        this.activeTraces.set(correlationId, trace);

        // Send to backend
        this.sendTraceEvent('workflow_started', {
            correlation_id: correlationId,
            workflow_type: workflowType,
            metadata
        });

        return correlationId;
    }

    /**
     * Start tracing a step within a workflow
     */
    startStep(correlationId: string, component: string, operation: string, metadata?: Record<string, any>): string {
        const stepKey = `${correlationId}_${component}_${operation}_${Date.now()}`;

        const step: TraceStep = {
            layer: 'frontend',
            component,
            operation,
            startTime: performance.now(),
            status: 'started',
            metadata: metadata || {}
        };

        this.activeSteps.set(stepKey, step);

        // Add to workflow trace
        const trace = this.activeTraces.get(correlationId);
        if (trace) {
            trace.steps.push(step);
        }

        return stepKey;
    }

    /**
     * Complete a trace step
     */
    completeStep(stepKey: string, metadata?: Record<string, any>): void {
        const step = this.activeSteps.get(stepKey);
        if (!step) return;

        step.endTime = performance.now();
        step.duration = step.endTime - step.startTime;
        step.status = 'completed';

        if (metadata) {
            step.metadata = { ...step.metadata, ...metadata };
        }

        this.activeSteps.delete(stepKey);

        // Send performance metric if step took significant time
        if (step.duration > 10) { // More than 10ms
            this.recordPerformanceMetric(
                this.getCorrelationIdFromStepKey(stepKey),
                step.component,
                'operation_time',
                step.duration,
                { operation: step.operation }
            );
        }
    }

    /**
     * Fail a trace step
     */
    failStep(stepKey: string, error: string, metadata?: Record<string, any>): void {
        const step = this.activeSteps.get(stepKey);
        if (!step) return;

        step.endTime = performance.now();
        step.duration = step.endTime - step.startTime;
        step.status = 'failed';
        step.metadata = {
            ...step.metadata,
            error,
            ...metadata
        };

        this.activeSteps.delete(stepKey);

        // Add error to workflow trace
        const correlationId = this.getCorrelationIdFromStepKey(stepKey);
        const trace = this.activeTraces.get(correlationId);
        if (trace) {
            trace.errors.push({
                timestamp: performance.now(),
                component: step.component,
                error
            });
        }

        // Send error to backend
        this.sendErrorEvent(correlationId, step.component, error, metadata);
    }

    /**
     * Complete a workflow
     */
    completeWorkflow(correlationId: string, metadata?: Record<string, any>): WorkflowTrace | null {
        const trace = this.activeTraces.get(correlationId);
        if (!trace) return null;

        trace.endTime = performance.now();
        trace.status = 'completed';

        if (metadata) {
            trace.metadata = { ...trace.metadata, ...metadata };
        }

        // Send completion to backend
        this.sendTraceEvent('workflow_completed', {
            correlation_id: correlationId,
            total_duration: trace.endTime - trace.startTime,
            step_count: trace.steps.length,
            error_count: trace.errors.length,
            metadata: trace.metadata
        });

        this.activeTraces.delete(correlationId);
        return trace;
    }

    /**
     * Fail a workflow
     */
    failWorkflow(correlationId: string, error: string, metadata?: Record<string, any>): WorkflowTrace | null {
        const trace = this.activeTraces.get(correlationId);
        if (!trace) return null;

        trace.endTime = performance.now();
        trace.status = 'failed';
        trace.metadata = {
            ...trace.metadata,
            error,
            ...metadata
        };

        // Send failure to backend
        this.sendTraceEvent('workflow_failed', {
            correlation_id: correlationId,
            error,
            total_duration: trace.endTime - trace.startTime,
            step_count: trace.steps.length,
            error_count: trace.errors.length,
            metadata: trace.metadata
        });

        this.activeTraces.delete(correlationId);
        return trace;
    }

    /**
     * Trace an API call
     */
    traceApiCall(correlationId: string, method: string, url: string, options?: RequestInit): Promise<Response> {
        const stepKey = this.startStep(correlationId, 'api-client', `${method} ${url}`, {
            method,
            url,
            headers: options?.headers
        });

        // Add correlation ID to headers
        const headers = new Headers(options?.headers);
        headers.set('X-Correlation-ID', correlationId);

        const startTime = performance.now();

        return fetch(url, { ...options, headers })
            .then(response => {
                const duration = performance.now() - startTime;

                this.completeStep(stepKey, {
                    status_code: response.status,
                    response_size: response.headers.get('content-length'),
                    duration
                });

                // Record API response time metric
                this.recordPerformanceMetric(
                    correlationId,
                    'api-client',
                    'response_time',
                    duration,
                    { method, url, status_code: response.status }
                );

                return response;
            })
            .catch(error => {
                const duration = performance.now() - startTime;

                this.failStep(stepKey, error.message, {
                    error_type: error.name,
                    duration
                });

                throw error;
            });
    }

    /**
     * Trace a user interaction
     */
    traceUserInteraction(correlationId: string, interactionType: string, element: string, metadata?: Record<string, any>): string {
        if (!this.enabledFeatures.userInteractionTracking) return '';

        return this.startStep(correlationId, 'user-interaction', interactionType, {
            element,
            timestamp: Date.now(),
            ...metadata
        });
    }

    /**
     * Record a performance metric
     */
    recordPerformanceMetric(correlationId: string, component: string, metricName: string, value: number, metadata?: Record<string, any>): void {
        if (!this.enabledFeatures.performanceMonitoring) return;

        const metric: PerformanceMetric = {
            correlationId,
            timestamp: Date.now(),
            layer: 'frontend',
            component,
            metricName,
            metricValue: value,
            metadata
        };

        // Send to backend
        this.sendMetricEvent(metric);
    }

    /**
     * Get current correlation ID from URL or generate new one
     */
    getCurrentCorrelationId(): string {
        // Try to get from URL params first
        const urlParams = new URLSearchParams(window.location.search);
        const correlationId = urlParams.get('correlation_id');

        if (correlationId) {
            return correlationId;
        }

        // Try to get from session storage
        const sessionCorrelationId = sessionStorage.getItem('workflow_correlation_id');
        if (sessionCorrelationId) {
            return sessionCorrelationId;
        }

        // Generate new one
        const newCorrelationId = uuidv4();
        sessionStorage.setItem('workflow_correlation_id', newCorrelationId);
        return newCorrelationId;
    }

    /**
     * Initialize performance monitoring
     */
    private initializePerformanceMonitoring(): void {
        if (!this.enabledFeatures.performanceMonitoring || !window.PerformanceObserver) return;

        try {
            this.performanceObserver = new PerformanceObserver((list) => {
                const correlationId = this.getCurrentCorrelationId();

                for (const entry of list.getEntries()) {
                    if (entry.entryType === 'navigation') {
                        const navEntry = entry as PerformanceNavigationTiming;
                        this.recordPerformanceMetric(correlationId, 'navigation', 'page_load_time', navEntry.loadEventEnd - navEntry.startTime);
                        this.recordPerformanceMetric(correlationId, 'navigation', 'dom_content_loaded', navEntry.domContentLoadedEventEnd - navEntry.startTime);
                    } else if (entry.entryType === 'paint') {
                        this.recordPerformanceMetric(correlationId, 'rendering', entry.name.replace('-', '_'), entry.startTime);
                    } else if (entry.entryType === 'largest-contentful-paint') {
                        this.recordPerformanceMetric(correlationId, 'rendering', 'largest_contentful_paint', entry.startTime);
                    }
                }
            });

            this.performanceObserver.observe({ entryTypes: ['navigation', 'paint', 'largest-contentful-paint'] });
        } catch (error) {
            console.warn('Failed to initialize performance monitoring:', error);
        }
    }

    /**
     * Initialize error tracking
     */
    private initializeErrorTracking(): void {
        if (!this.enabledFeatures.errorTracking) return;

        window.addEventListener('error', (event) => {
            const correlationId = this.getCurrentCorrelationId();
            this.sendErrorEvent(correlationId, 'global', event.error?.message || event.message, {
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                stack: event.error?.stack
            });
        });

        window.addEventListener('unhandledrejection', (event) => {
            const correlationId = this.getCurrentCorrelationId();
            this.sendErrorEvent(correlationId, 'promise', event.reason?.message || String(event.reason), {
                stack: event.reason?.stack
            });
        });
    }

    /**
     * Initialize API call interception
     */
    private initializeApiInterception(): void {
        if (!this.enabledFeatures.apiTracing) return;

        // Intercept fetch calls
        const originalFetch = window.fetch;
        window.fetch = (input: RequestInfo | URL, init?: RequestInit) => {
            const correlationId = this.getCurrentCorrelationId();
            const url = typeof input === 'string' ? input : input.toString();
            const method = init?.method || 'GET';

            return this.traceApiCall(correlationId, method, url, init);
        };
    }

    /**
     * Send trace event to backend
     */
    private async sendTraceEvent(eventType: string, data: Record<string, any>): Promise<void> {
        try {
            await fetch(`${this.apiEndpoint}/trace-events/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Correlation-ID': data.correlation_id
                },
                body: JSON.stringify({
                    event_type: eventType,
                    timestamp: Date.now(),
                    ...data
                })
            });
        } catch (error) {
            console.warn('Failed to send trace event:', error);
        }
    }

    /**
     * Send error event to backend
     */
    private async sendErrorEvent(correlationId: string, component: string, error: string, metadata?: Record<string, any>): Promise<void> {
        try {
            await fetch(`${this.apiEndpoint}/errors/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Correlation-ID': correlationId
                },
                body: JSON.stringify({
                    layer: 'frontend',
                    component,
                    error_type: 'JavaScriptError',
                    error_message: error,
                    correlation_id: correlationId,
                    timestamp: Date.now(),
                    metadata: metadata || {}
                })
            });
        } catch (err) {
            console.warn('Failed to send error event:', err);
        }
    }

    /**
     * Send performance metric to backend
     */
    private async sendMetricEvent(metric: PerformanceMetric): Promise<void> {
        try {
            await fetch(`${this.apiEndpoint}/metrics/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Correlation-ID': metric.correlationId
                },
                body: JSON.stringify({
                    layer: metric.layer,
                    component: metric.component,
                    metric_name: metric.metricName,
                    metric_value: metric.metricValue,
                    correlation_id: metric.correlationId,
                    timestamp: metric.timestamp,
                    metadata: metric.metadata || {}
                })
            });
        } catch (error) {
            console.warn('Failed to send metric event:', error);
        }
    }

    /**
     * Extract correlation ID from step key
     */
    private getCorrelationIdFromStepKey(stepKey: string): string {
        return stepKey.split('_')[0];
    }
}

// Create global tracer instance
export const workflowTracer = new FrontendWorkflowTracer();

/**
 * React Hook for workflow tracing
 */
export function useWorkflowTracing(workflowType: string) {
    const [correlationId, setCorrelationId] = React.useState<string>('');

    React.useEffect(() => {
        const id = workflowTracer.startWorkflow(workflowType);
        setCorrelationId(id);

        return () => {
            if (id) {
                workflowTracer.completeWorkflow(id);
            }
        };
    }, [workflowType]);

    const traceStep = React.useCallback((component: string, operation: string, metadata?: Record<string, any>) => {
        if (!correlationId) return '';
        return workflowTracer.startStep(correlationId, component, operation, metadata);
    }, [correlationId]);

    const completeStep = React.useCallback((stepKey: string, metadata?: Record<string, any>) => {
        workflowTracer.completeStep(stepKey, metadata);
    }, []);

    const failStep = React.useCallback((stepKey: string, error: string, metadata?: Record<string, any>) => {
        workflowTracer.failStep(stepKey, error, metadata);
    }, []);

    const traceApiCall = React.useCallback((method: string, url: string, options?: RequestInit) => {
        if (!correlationId) return fetch(url, options);
        return workflowTracer.traceApiCall(correlationId, method, url, options);
    }, [correlationId]);

    return {
        correlationId,
        traceStep,
        completeStep,
        failStep,
        traceApiCall
    };
}

/**
 * Higher-order component for automatic workflow tracing
 */
export function withWorkflowTracing<P extends object>(
    Component: React.ComponentType<P>,
    workflowType: string
) {
    return function TracedComponent(props: P) {
        const { correlationId, traceStep, completeStep } = useWorkflowTracing(workflowType);

        React.useEffect(() => {
            const stepKey = traceStep('component', 'render', { component_name: Component.name });

            return () => {
                if (stepKey) {
                    completeStep(stepKey);
                }
            };
        }, [traceStep, completeStep]);

        return React.createElement(Component, props);
    };
}

export default workflowTracer;