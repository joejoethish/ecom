/**
 * Application initialization utilities
 */
import { initializeTokenCleanup } from './tokenCleanup';
import { logSecurityEvent } from './securityMonitoring';

/**
 * Initialize all app-level utilities and services
 */
  try {
    // Initialize token cleanup with custom config if needed
    initializeTokenCleanup({
      maxTokenAge: 60 * 60 * 1000, // 1 hour
      cleanupInterval: 15 * 60 * 1000, // 15 minutes
      maxStoredTokens: 50 // Reduced for better performance
    });

    // Log app initialization
    logSecurityEvent(
      'password_reset',
      'app_initialized',
      'low',
      {
        timestamp: new Date().toISOString(),
        userAgent: typeof window !== 'undefined' ? window.navigator.userAgent : 'unknown'
      }
    );

    console.log('Password reset system initialized successfully');

  } catch (error) {
    console.error('Error initializing password reset system:', error);
    
    // Log initialization error
    logSecurityEvent(
      'password_reset',
      'initialization_error',
      'high',
      {
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString()
      }
    );
  }
};

/**
 * Cleanup function to call on app shutdown
 */
  try {
    // The token cleanup manager will handle its own cleanup
    // through the beforeunload event listener
    
    logSecurityEvent(
      'password_reset',
      'app_cleanup',
      'low',
      {
        timestamp: new Date().toISOString()
      }
    );

    console.log('Password reset system cleanup completed');

  } catch (error) {
    console.error('Error during app cleanup:', error);
  }
};