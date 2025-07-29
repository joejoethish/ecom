import { NextRequest } from 'next/server';
import { authMiddleware, shouldProcessAuth } from './middleware/auth';

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  
  // Skip processing for certain paths
  if (!shouldProcessAuth(pathname)) {
    return;
  }
  
  // Apply authentication middleware
  return authMiddleware(request);
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