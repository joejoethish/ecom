/**
 * Next.js Middleware for Correlation ID Management
 * 
 * This middleware ensures correlation IDs are properly handled
 * in Next.js server-side operations and API routes.
 */

import { NextRequest, NextResponse } from 'next/server';
import { v4 as uuidv4 } from 'uuid';

export const CORRELATION_ID_HEADER = 'X-Correlation-ID';
export const CORRELATION_ID_COOKIE = 'correlation_id';

/**
 * Validate correlation ID format
 */
function isValidCorrelationId(correlationId: string): boolean {
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
 * Extract correlation ID from request
 */
function extractCorrelationId(request: NextRequest): string | null {
  // Try to get from headers first
  let correlationId = request.headers.get(CORRELATION_ID_HEADER);
  
  // Try to get from cookies if not in headers
  if (!correlationId) {
    correlationId = request.cookies.get(CORRELATION_ID_COOKIE)?.value;
  }
  
  // Validate the correlation ID
  if (correlationId && isValidCorrelationId(correlationId)) {
    return correlationId;
  }
  
  return null;
}

/**
 * Generate a new correlation ID
 */
function generateCorrelationId(): string {
  return uuidv4();
}

/**
 * Correlation ID middleware for Next.js
 */
export function correlationIdMiddleware(request: NextRequest): NextResponse {
  // Extract or generate correlation ID
  let correlationId = extractCorrelationId(request);
  
  if (!correlationId) {
    correlationId = generateCorrelationId();
    console.debug(`Generated new correlation ID: ${correlationId} for ${request.url}`);
  } else {
    console.debug(`Using existing correlation ID: ${correlationId} for ${request.url}`);
  }
  
  // Create response
  const response = NextResponse.next();
  
  // Add correlation ID to response headers
  response.headers.set(CORRELATION_ID_HEADER, correlationId);
  
  // Set correlation ID in cookie for client-side access
  response.cookies.set(CORRELATION_ID_COOKIE, correlationId, {
    httpOnly: false, // Allow client-side access
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: 60 * 60 * 24, // 24 hours
  });
  
  // Add correlation ID to request headers for downstream processing
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set(CORRELATION_ID_HEADER, correlationId);
  
  // Log the request with correlation ID
  console.info(
    `[${correlationId}] ${request.method} ${request.url} - User-Agent: ${request.headers.get('user-agent')?.substring(0, 100) || 'Unknown'}`
  );
  
  return response;
}

/**
 * Check if correlation ID middleware should process the request
 */
export function shouldProcessCorrelationId(pathname: string): boolean {
  // Skip static files and Next.js internal routes
  const skipPatterns = [
    '/_next/',
    '/favicon.ico',
    '/robots.txt',
    '/sitemap.xml',
    '/manifest.json',
    '/sw.js',
    '/workbox-',
  ];
  
  return !skipPatterns.some(pattern => pathname.startsWith(pattern));
}

/**
 * API route helper to extract correlation ID
 */
export function getCorrelationIdFromRequest(request: NextRequest): string {
  let correlationId = extractCorrelationId(request);
  
  if (!correlationId) {
    correlationId = generateCorrelationId();
  }
  
  return correlationId;
}

/**
 * API route helper to add correlation ID to response
 */
export function addCorrelationIdToResponse(response: NextResponse, correlationId: string): NextResponse {
  response.headers.set(CORRELATION_ID_HEADER, correlationId);
  return response;
}

/**
 * Server-side utility to get correlation ID from headers
 */
export function getServerSideCorrelationId(headers: Headers): string | null {
  const correlationId = headers.get(CORRELATION_ID_HEADER);
  
  if (correlationId && isValidCorrelationId(correlationId)) {
    return correlationId;
  }
  
  return null;
}

/**
 * Utility to create correlation ID context for server-side operations
 */
export interface CorrelationContext {
  correlationId: string;
  timestamp: string;
  userAgent?: string;
  ip?: string;
}

export function createCorrelationContext(request: NextRequest): CorrelationContext {
  const correlationId = getCorrelationIdFromRequest(request);
  
  return {
    correlationId,
    timestamp: new Date().toISOString(),
    userAgent: request.headers.get('user-agent') || undefined,
    ip: request.ip || request.headers.get('x-forwarded-for') || undefined,
  };
}

/**
 * Utility to log server-side operations with correlation ID
 */
export function logWithCorrelationId(
  correlationId: string,
  level: 'debug' | 'info' | 'warn' | 'error',
  message: string,
  data?: any
): void {
  const logMessage = `[${correlationId}] ${message}`;
  
  switch (level) {
    case 'debug':
      console.debug(logMessage, data);
      break;
    case 'info':
      console.info(logMessage, data);
      break;
    case 'warn':
      console.warn(logMessage, data);
      break;
    case 'error':
      console.error(logMessage, data);
      break;
  }
}