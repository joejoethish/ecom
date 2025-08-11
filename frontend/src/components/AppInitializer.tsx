'use client';

import { useEffect } from 'react';
import { initializeApp } from '@/utils/appInitialization';

interface AppInitializerProps {
  children: React.ReactNode;
}

/**
 * Component that initializes app-level services and utilities
 */
  useEffect(() => {
    // Initialize the password reset system and other app services
    initializeApp();

    // Cleanup function
    return () => {
      // Cleanup is handled by the individual services
      // through their own event listeners
    };
  }, []);

  return <>{children}</>;
};