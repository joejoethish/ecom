'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useAppSelector, useAppDispatch } from '@/store';
import { logoutUser } from '@/store/slices/authSlice';
import { adminAuthApi, AdminSessionInfo } from '@/services/adminAuthApi';
import { User } from '@/types';
import toast from 'react-hot-toast';

interface AdminAuthContextType {
  isAdmin: boolean;
  isElevatedAdmin: boolean;
  adminUser: User | null;
  sessions: AdminSessionInfo[];
  sessionTimeout: number | null;
  loading: boolean;
  validateSession: () => Promise<boolean>;
  refreshSessions: () => Promise<void>;
  terminateSession: (sessionId: string) => Promise<void>;
  logoutAll: () => Promise<void>;
  extendSession: () => Promise<void>;
}

const AdminAuthContext = createContext<AdminAuthContextType | undefined>(undefined);

interface AdminAuthProviderProps {
  children: ReactNode;
}

export function AdminAuthProvider({ children }: AdminAuthProviderProps) {
  const dispatch = useAppDispatch();
  const { user, isAuthenticated } = useAppSelector((state) => state.auth);
  
  const [sessions, setSessions] = useState<AdminSessionInfo[]>([]);
  const [sessionTimeout, setSessionTimeout] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  // Check if user is admin
  const isAdmin = Boolean(isAuthenticated && user && ['admin'].includes(user.user_type));
  const isElevatedAdmin = Boolean(isAuthenticated && user && user.user_type === 'admin' && user.is_superuser);
  const adminUser = isAdmin ? user : null;

  // Session validation interval
  useEffect(() => {
    if (!isAdmin) return;

    const validateInterval = setInterval(async () => {
      const isValid = await validateSession();
      if (!isValid) {
        toast.error('Admin session expired. Please login again.');
        dispatch(logoutUser());
      }
    }, 5 * 60 * 1000); // Check every 5 minutes

    return () => clearInterval(validateInterval);
  }, [isAdmin, dispatch]);

  // Session timeout warning
  useEffect(() => {
    if (!sessionTimeout) return;

    const warningTime = sessionTimeout - (5 * 60 * 1000); // 5 minutes before expiry
    const timeUntilWarning = warningTime - Date.now();

    if (timeUntilWarning > 0) {
      const warningTimeout = setTimeout(() => {
        toast((t) => (
          <div className="flex flex-col space-y-2">
            <span className="font-medium">Session Expiring Soon</span>
            <span className="text-sm text-gray-600">
              Your admin session will expire in 5 minutes. Click to extend.
            </span>
            <button
              onClick={() => {
                extendSession();
                toast.dismiss(t.id);
              }}
              className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
            >
              Extend Session
            </button>
          </div>
        ), {
          duration: 300000, // Show for 5 minutes
          icon: '⚠️',
        });
      }, timeUntilWarning);

      return () => clearTimeout(warningTimeout);
    }
  }, [sessionTimeout]);

  const validateSession = async (): Promise<boolean> => {
    if (!isAdmin) return false;

    try {
      const response = await adminAuthApi.validateSession();
      if (response.success && response.data) {
        if (response.data.valid) {
          setSessionTimeout(new Date(response.data.expiresAt).getTime());
          return true;
        }
      }
      return false;
    } catch (error) {
      console.error('Session validation failed:', error);
      return false;
    }
  };

  const refreshSessions = async (): Promise<void> => {
    if (!isAdmin) return;

    setLoading(true);
    try {
      const response = await adminAuthApi.getSessions();
      if (response.success && response.data) {
        setSessions(response.data);
      }
    } catch (error) {
      console.error('Failed to refresh sessions:', error);
      toast.error('Failed to refresh session data');
    } finally {
      setLoading(false);
    }
  };

  const terminateSession = async (sessionId: string): Promise<void> => {
    try {
      const response = await adminAuthApi.terminateSession(sessionId);
      if (response.success) {
        setSessions(prev => prev.filter(session => session.id !== sessionId));
        toast.success('Session terminated successfully');
      } else {
        toast.error('Failed to terminate session');
      }
    } catch (error) {
      console.error('Failed to terminate session:', error);
      toast.error('Failed to terminate session');
    }
  };

  const logoutAll = async (): Promise<void> => {
    try {
      const response = await adminAuthApi.logoutAll();
      if (response.success) {
        toast.success(`Logged out from ${response.data?.clearedSessions || 0} sessions`);
        await refreshSessions();
      } else {
        toast.error('Failed to logout from all sessions');
      }
    } catch (error) {
      console.error('Failed to logout from all sessions:', error);
      toast.error('Failed to logout from all sessions');
    }
  };

  const extendSession = async (): Promise<void> => {
    if (!isAdmin) return;

    try {
      // Refresh the token to extend session
      const tokens = JSON.parse(localStorage.getItem('tokens') || '{}');
      if (tokens.refresh) {
        const response = await adminAuthApi.refreshToken(tokens.refresh);
        if (response.success && response.data) {
          // Update stored tokens
          localStorage.setItem('tokens', JSON.stringify(response.data.tokens));
          setSessionTimeout(new Date(response.data.expiresAt).getTime());
          toast.success('Session extended successfully');
        }
      }
    } catch (error) {
      console.error('Failed to extend session:', error);
      toast.error('Failed to extend session');
    }
  };

  // Load sessions on mount
  useEffect(() => {
    if (isAdmin) {
      refreshSessions();
      validateSession();
    }
  }, [isAdmin]);

  const value: AdminAuthContextType = {
    isAdmin,
    isElevatedAdmin,
    adminUser,
    sessions,
    sessionTimeout,
    loading,
    validateSession,
    refreshSessions,
    terminateSession,
    logoutAll,
    extendSession,
  };

  return (
    <AdminAuthContext.Provider value={value}>
      {children}
    </AdminAuthContext.Provider>
  );
}

export function useAdminAuth() {
  const context = useContext(AdminAuthContext);
  if (context === undefined) {
    throw new Error('useAdminAuth must be used within an AdminAuthProvider');
  }
  return context;
}