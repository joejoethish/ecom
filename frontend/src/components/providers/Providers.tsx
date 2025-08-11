'use client';

import { Provider } from 'react-redux';
import { Toaster } from 'react-hot-toast';
import { store } from '@/store';
import { AuthProvider } from './AuthProvider';
import { AccessibilityProvider } from './AccessibilityProvider';
import { AccessibilityMenu } from '../common/AccessibilityMenu';
import { Suspense, lazy } from 'react';
import { observeLongTasks } from '@/utils/performance';
import { useEffect } from 'react';

// Lazy load the AccessibilityMenu to improve initial load performance
const LazyAccessibilityMenu = lazy(() => import('../common/AccessibilityMenu').then(
  module => ({ default: module.AccessibilityMenu })
));

interface ProvidersProps {
  children: React.ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  // Set up performance monitoring
  useEffect(() => {
    const cleanup = observeLongTasks();
    return cleanup;
  }, []);

  return (
    <Provider store={store}>
      <AuthProvider>
        <AccessibilityProvider>
          {children}
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
              },
              success: {
                duration: 3000,
                iconTheme: {
                  primary: '#4ade80',
                  secondary: '#fff',
                },
              },
              error: {
                duration: 4000,
                iconTheme: {
                  primary: '#ef4444',
                  secondary: '#fff',
                },
              },
            }}
          />
          <Suspense fallback={null}>
            <LazyAccessibilityMenu />
          </Suspense>
        </AccessibilityProvider>
      </AuthProvider>
    </Provider>
  );
}