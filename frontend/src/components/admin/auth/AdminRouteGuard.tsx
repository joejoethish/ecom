'use client';

import { useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { useAdminAuth } from '@/contexts/AdminAuthContext';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { Shield, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { ADMIN_ROUTES } from '@/constants';

interface AdminRouteGuardProps {
  children: ReactNode;
  requireElevated?: boolean;
  fallbackPath?: string;
}

export function AdminRouteGuard({ 
  children, 
  requireElevated = false,
  fallbackPath = '/admin/login'
}: AdminRouteGuardProps) {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const { isAdmin, isElevatedAdmin, loading: adminLoading, validateSession } = useAdminAuth();

  useEffect(() => {
    const checkAccess = async () => {
      // Wait for auth to initialize
      if (authLoading || adminLoading) return;

      // Not authenticated at all
      if (!isAuthenticated) {
        router.push(fallbackPath);
        return;
      }

      // Not an admin user
      if (!isAdmin) {
        router.push('/auth/login?error=admin_access_required');
        return;
      }

      // Requires elevated admin but user is not elevated
      if (requireElevated && !isElevatedAdmin) {
        router.push(ADMIN_ROUTES.DASHBOARD + '?error=elevated_access_required');
        return;
      }

      // Validate session is still active
      const sessionValid = await validateSession();
      if (!sessionValid) {
        router.push(fallbackPath + '?error=session_expired');
        return;
      }
    };

    checkAccess();
  }, [
    isAuthenticated, 
    isAdmin, 
    isElevatedAdmin, 
    authLoading, 
    adminLoading, 
    requireElevated, 
    router, 
    fallbackPath, 
    validateSession
  ]);

  // Show loading while checking authentication
  if (authLoading || adminLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <LoadingSpinner size="lg" />
          <p className="mt-4 text-gray-600">Verifying admin access...</p>
        </div>
      </div>
    );
  }

  // Not authenticated
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center max-w-md">
          <Shield className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Authentication Required</h2>
          <p className="text-gray-600 mb-6">Please sign in to access the admin portal.</p>
          <Button onClick={() => router.push(fallbackPath)}>
            Go to Admin Login
          </Button>
        </div>
      </div>
    );
  }

  // Not an admin
  if (!isAdmin) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center max-w-md">
          <AlertTriangle className="h-16 w-16 text-red-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
          <p className="text-gray-600 mb-6">
            You don't have administrative privileges to access this area.
          </p>
          <div className="space-x-4">
            <Button 
              variant="outline" 
              onClick={() => router.push('/')}
            >
              Go Home
            </Button>
            <Button onClick={() => router.push('/auth/login')}>
              Sign In as Admin
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // Requires elevated admin but user is not elevated
  if (requireElevated && !isElevatedAdmin) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center max-w-md">
          <Shield className="h-16 w-16 text-yellow-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Elevated Access Required</h2>
          <p className="text-gray-600 mb-6">
            This area requires super admin privileges. Contact your system administrator if you need access.
          </p>
          <Button onClick={() => router.push(ADMIN_ROUTES.DASHBOARD)}>
            Back to Admin Dashboard
          </Button>
        </div>
      </div>
    );
  }

  // All checks passed, render children
  return <>{children}</>;
}