/**
 * Correlation ID Service for Frontend
 * 
 * This service manages correlation IDs for API calls and user interactions,
 * ensuring traceability across the entire application stack.
 */

import { v4 as uuidv4 } from 'uuid';

export interface CorrelationIdConfig {
  headerName: string;
  storageKey: string;
  generateOnPageLoad: boolean;
  persistInSession: boolean;
}

export class CorrelationIdService {
  private static instance: CorrelationIdService;
  private currentCorrelationId: string | null = null;
  private config: CorrelationIdConfig;

  private constructor(config?: Partial<CorrelationIdConfig>) {
    this.config = {
      headerName: 'X-Correlation-ID',
      storageKey: 'correlation_id',
      generateOnPageLoad: true,
      persistInSession: true,
      ...config,
    };

    if (this.config.generateOnPageLoad) {
      this.initializeCorrelationId();
    }
  }

  /**
   * Get the singleton instance of CorrelationIdService
   */
  public static getInstance(config?: Partial<CorrelationIdConfig>): CorrelationIdService {
    if (!CorrelationIdService.instance) {
      CorrelationIdService.instance = new CorrelationIdService(config);
    }
    return CorrelationIdService.instance;
  }

  /**
   * Initialize correlation ID on service creation
   */
  private initializeCorrelationId(): void {
    // Try to get existing correlation ID from session storage
    if (this.config.persistInSession && typeof window !== 'undefined') {
      const stored = sessionStorage.getItem(this.config.storageKey);
      if (stored && this.isValidCorrelationId(stored)) {
        this.currentCorrelationId = stored;
        return;
      }
    }

    // Generate new correlation ID if none exists
    this.generateNewCorrelationId();
  }

  /**
   * Generate a new correlation ID
   */
  public generateNewCorrelationId(): string {
    const correlationId = uuidv4();
    this.setCorrelationId(correlationId);
    return correlationId;
  }

  /**
   * Set the current correlation ID
   */
  public setCorrelationId(correlationId: string): void {
    if (!this.isValidCorrelationId(correlationId)) {
      console.warn(`Invalid correlation ID format: ${correlationId}. Generating new one.`);
      correlationId = uuidv4();
    }

    this.currentCorrelationId = correlationId;

    // Persist in session storage if enabled
    if (this.config.persistInSession && typeof window !== 'undefined') {
      sessionStorage.setItem(this.config.storageKey, correlationId);
    }

    // Log correlation ID change for debugging
    console.debug(`Correlation ID set: ${correlationId}`);
  }

  /**
   * Get the current correlation ID
   */
  public getCorrelationId(): string {
    if (!this.currentCorrelationId) {
      this.generateNewCorrelationId();
    }
    return this.currentCorrelationId!;
  }

  /**
   * Create a child correlation ID for sub-operations
   */
  public createChildCorrelationId(parentId?: string): string {
    const parent = parentId || this.getCorrelationId();
    const childId = uuidv4();
    
    console.debug(`Created child correlation ID: ${childId} for parent: ${parent}`);
    return childId;
  }

  /**
   * Get headers object with correlation ID
   */
  public getHeaders(): Record<string, string> {
    return {
      [this.config.headerName]: this.getCorrelationId(),
    };
  }

  /**
   * Add correlation ID to existing headers
   */
  public addToHeaders(headers: Record<string, string> = {}): Record<string, string> {
    return {
      ...headers,
      [this.config.headerName]: this.getCorrelationId(),
    };
  }

  /**
   * Validate correlation ID format
   */
  private isValidCorrelationId(correlationId: string): boolean {
    if (!correlationId || typeof correlationId !== 'string') {
      return false;
    }

    // Check length constraints
    if (correlationId.length < 8 || correlationId.length > 64) {
      return false;
    }

    // Check for UUID format (optional - can be any reasonable string)
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    if (uuidRegex.test(correlationId)) {
      return true;
    }

    // Allow alphanumeric with hyphens and underscores
    const alphanumericRegex = /^[a-zA-Z0-9_-]+$/;
    return alphanumericRegex.test(correlationId);
  }

  /**
   * Clear the current correlation ID
   */
  public clearCorrelationId(): void {
    this.currentCorrelationId = null;
    
    if (this.config.persistInSession && typeof window !== 'undefined') {
      sessionStorage.removeItem(this.config.storageKey);
    }
  }

  /**
   * Log an event with correlation ID context
   */
  public logWithCorrelationId(level: 'debug' | 'info' | 'warn' | 'error', message: string, data?: any): void {
    const correlationId = this.getCorrelationId();
    const logMessage = `[${correlationId}] ${message}`;
    
    console[level](logMessage, data);
  }
}

// Export singleton instance
export const correlationIdService = CorrelationIdService.getInstance();

// Export utility functions
export const getCorrelationId = () => correlationIdService.getCorrelationId();
export const setCorrelationId = (id: string) => correlationIdService.setCorrelationId(id);
export const getCorrelationHeaders = () => correlationIdService.getHeaders();
export const addCorrelationToHeaders = (headers?: Record<string, string>) => 
  correlationIdService.addToHeaders(headers);
export const createChildCorrelationId = (parentId?: string) => 
  correlationIdService.createChildCorrelationId(parentId);
export const logWithCorrelationId = (level: 'debug' | 'info' | 'warn' | 'error', message: string, data?: any) =>
  correlationIdService.logWithCorrelationId(level, message, data);