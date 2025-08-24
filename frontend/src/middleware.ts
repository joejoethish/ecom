import { NextRequest, NextResponse } from 'next/server';
import { authMiddleware, shouldProcessAuth } from './middleware/auth';
import { correlationIdMiddleware, shouldProcessCorrelationId } from './middleware/correlationId';

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  
  // Always process correlation ID first (for all requests)
  let response: NextResponse | undefined;
  
  if (shouldProcessCorrelationId(pathname)) {
    response = correlationIdMiddleware(request);
  }
  
  // Skip auth processing for certain paths
  if (!shouldProcessAuth(pathname)) {
    return response;
  }
  
  // Apply authentication middleware
  const authResponse = authMiddleware(request);
  
  // If we have both responses, merge headers from correlation ID middleware
  if (response && authResponse) {
    const correlationId = response.headers.get('X-Correlation-ID');
    if (correlationId) {
      authResponse.headers.set('X-Correlation-ID', correlationId);
      // Copy correlation ID cookie
      const correlationCookie = response.cookies.get('correlation_id');
      if (correlationCookie) {
        authResponse.cookies.set('correlation_id', correlationCookie.value, {
          httpOnly: false,
          secure: process.env.NODE_ENV === 'production',
          sameSite: 'lax',
          maxAge: 60 * 60 * 24, // 24 hours
        });
      }
    }
    return authResponse;
  }
  
  return authResponse || response;
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};