/**
 * Token cleanup and maintenance utilities for password reset system
 * Note: This is frontend-focused cleanup for client-side token management
 */

export interface TokenCleanupConfig {
  maxTokenAge: number; // in milliseconds
  cleanupInterval: number; // in milliseconds
  maxStoredTokens: number;
}

export interface StoredTokenInfo {
  token: string;
  timestamp: number;
  used: boolean;
  email?: string;
}

/**
 * Default configuration for token cleanup
 */
  maxTokenAge: 60 * 60 * 1000, // 1 hour
  cleanupInterval: 15 * 60 * 1000, // 15 minutes
  maxStoredTokens: 100, // Maximum tokens to keep in local storage
};

/**
 * Local storage key for storing token information
 */
const TOKEN_STORAGE_KEY = 'password_reset_tokens';

/**
 * Token cleanup manager for client-side token management
 */
export class TokenCleanupManager {
  private config: TokenCleanupConfig;
  private cleanupTimer: NodeJS.Timeout | null = null;

  constructor(config: TokenCleanupConfig = DEFAULT_CLEANUP_CONFIG) {
    this.config = config;
  }

  /**
   * Start automatic token cleanup
   */
  startCleanup(): void {
    if (this.cleanupTimer) {
      this.stopCleanup();
    }

    this.cleanupTimer = setInterval(() => {
      this.performCleanup();
    }, this.config.cleanupInterval);

    // Perform initial cleanup
    this.performCleanup();
  }

  /**
   * Stop automatic token cleanup
   */
  stopCleanup(): void {
    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer);
      this.cleanupTimer = null;
    }
  }

  /**
   * Perform token cleanup
   */
  performCleanup(): void {
    try {
      const tokens = this.getStoredTokens();
      const now = Date.now();
      
      // Filter out expired and used tokens
      const validTokens = tokens.filter(tokenInfo => {
        const age = now - tokenInfo.timestamp;
        return age < this.config.maxTokenAge && !tokenInfo.used;
      });

      // Limit the number of stored tokens
      const limitedTokens = validTokens
        .sort((a, b) => b.timestamp - a.timestamp) // Sort by newest first
        .slice(0, this.config.maxStoredTokens);

      // Update storage
      this.setStoredTokens(limitedTokens);

      // Log cleanup results
      const removedCount = tokens.length - limitedTokens.length;
      if (removedCount > 0) {
        console.log(`Token cleanup: Removed ${removedCount} expired/used tokens`);
      }

    } catch (error) {
      console.error(&apos;Error during token cleanup:&apos;, error);
    }
  }

  /**
   * Store token information
   */
  storeToken(token: string, email?: string): void {
    try {
      const tokens = this.getStoredTokens();
      
      // Remove any existing entry for this token
      const filteredTokens = tokens.filter(t => t.token !== token);
      
      // Add new token info
        token,
        timestamp: Date.now(),
        used: false,
        email
      };
      
      filteredTokens.push(tokenInfo);
      
      // Limit storage size
      const limitedTokens = filteredTokens
        .sort((a, b) => b.timestamp - a.timestamp)
        .slice(0, this.config.maxStoredTokens);
      
      this.setStoredTokens(limitedTokens);
      
    } catch (error) {
      console.error(&apos;Error storing token:&apos;, error);
    }
  }

  /**
   * Mark token as used
   */
  markTokenAsUsed(token: string): void {
    try {
      const tokens = this.getStoredTokens();
      const tokenInfo = tokens.find(t => t.token === token);
      
      if (tokenInfo) {
        tokenInfo.used = true;
        this.setStoredTokens(tokens);
      }
      
    } catch (error) {
      console.error(&apos;Error marking token as used:&apos;, error);
    }
  }

  /**
   * Check if token is valid (not expired or used)
   */
  isTokenValid(token: string): boolean {
    try {
      const tokens = this.getStoredTokens();
      const tokenInfo = tokens.find(t => t.token === token);
      
      if (!tokenInfo) {
        return false; // Token not found
      }
      
      if (tokenInfo.used) {
        return false; // Token already used
      }
      
      const age = Date.now() - tokenInfo.timestamp;
      return age < this.config.maxTokenAge;
      
    } catch (error) {
      console.error('Error checking token validity:', error);
      return false;
    }
  }

  /**
   * Get token information
   */
  getTokenInfo(token: string): StoredTokenInfo | null {
    try {
      const tokens = this.getStoredTokens();
      return tokens.find(t => t.token === token) || null;
    } catch (error) {
      console.error(&apos;Error getting token info:&apos;, error);
      return null;
    }
  }

  /**
   * Get cleanup statistics
   */
  getCleanupStats(): {
    totalTokens: number;
    validTokens: number;
    expiredTokens: number;
    usedTokens: number;
    oldestToken: number | null;
    newestToken: number | null;
  } {
    try {
      const tokens = this.getStoredTokens();
      const now = Date.now();
      
      let validCount = 0;
      let expiredCount = 0;
      let usedCount = 0;
      let oldestTimestamp: number | null = null;
      let newestTimestamp: number | null = null;
      
      tokens.forEach(tokenInfo => {
        const age = now - tokenInfo.timestamp;
        
        if (tokenInfo.used) {
          usedCount++;
        } else if (age >= this.config.maxTokenAge) {
          expiredCount++;
        } else {
          validCount++;
        }
        
        if (oldestTimestamp === null || tokenInfo.timestamp < oldestTimestamp) {
          oldestTimestamp = tokenInfo.timestamp;
        }
        
        if (newestTimestamp === null || tokenInfo.timestamp > newestTimestamp) {
          newestTimestamp = tokenInfo.timestamp;
        }
      });
      
      return {
        totalTokens: tokens.length,
        validTokens: validCount,
        expiredTokens: expiredCount,
        usedTokens: usedCount,
        oldestToken: oldestTimestamp,
        newestToken: newestTimestamp
      };
      
    } catch (error) {
      console.error(&apos;Error getting cleanup stats:&apos;, error);
      return {
        totalTokens: 0,
        validTokens: 0,
        expiredTokens: 0,
        usedTokens: 0,
        oldestToken: null,
        newestToken: null
      };
    }
  }

  /**
   * Force cleanup of all tokens
   */
  clearAllTokens(): void {
    try {
      this.setStoredTokens([]);
      console.log(&apos;All password reset tokens cleared&apos;);
    } catch (error) {
      console.error(&apos;Error clearing all tokens:&apos;, error);
    }
  }

  /**
   * Get stored tokens from local storage
   */
  private getStoredTokens(): StoredTokenInfo[] {
    if (typeof window === &apos;undefined&apos;) {
      return [];
    }
    
    try {
      const stored = localStorage.getItem(TOKEN_STORAGE_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch (error) {
      console.error(&apos;Error reading stored tokens:&apos;, error);
      return [];
    }
  }

  /**
   * Set stored tokens in local storage
   */
  private setStoredTokens(tokens: StoredTokenInfo[]): void {
    if (typeof window === &apos;undefined&apos;) {
      return;
    }
    
    try {
      localStorage.setItem(TOKEN_STORAGE_KEY, JSON.stringify(tokens));
    } catch (error) {
      console.error(&apos;Error storing tokens:&apos;, error);
    }
  }
}

/**
 * Global token cleanup manager instance
 */
export const tokenCleanupManager = new TokenCleanupManager();

/**
 * Initialize token cleanup on app start
 */
  if (config) {
    const mergedConfig = { ...DEFAULT_CLEANUP_CONFIG, ...config };
    tokenCleanupManager.stopCleanup();
    Object.assign(tokenCleanupManager, { config: mergedConfig });
  }
  
  tokenCleanupManager.startCleanup();
  
  // Cleanup on page unload
  if (typeof window !== &apos;undefined&apos;) {
    window.addEventListener(&apos;beforeunload&apos;, () => {
      tokenCleanupManager.performCleanup();
    });
  }
};

/**
 * Utility functions for token management
 */
export const tokenUtils = {
  /**
   * Store a password reset token
   */
  storeResetToken: (token: string, email?: string) => {
    tokenCleanupManager.storeToken(token, email);
  },

  /**
   * Mark a token as used after successful password reset
   */
  markTokenUsed: (token: string) => {
    tokenCleanupManager.markTokenAsUsed(token);
  },

  /**
   * Check if a token is still valid
   */
  isTokenValid: (token: string) => {
    return tokenCleanupManager.isTokenValid(token);
  },

  /**
   * Get token information
   */
  getTokenInfo: (token: string) => {
    return tokenCleanupManager.getTokenInfo(token);
  },

  /**
   * Get cleanup statistics for monitoring
   */
  getStats: () => {
    return tokenCleanupManager.getCleanupStats();
  },

  /**
   * Force cleanup of expired tokens
   */
  forceCleanup: () => {
    tokenCleanupManager.performCleanup();
  },

  /**
   * Clear all stored tokens
   */
  clearAll: () => {
    tokenCleanupManager.clearAllTokens();
  }
};

/**
 * Hook for React components to use token cleanup
 */
  return {
    storeToken: tokenUtils.storeResetToken,
    markTokenUsed: tokenUtils.markTokenUsed,
    isTokenValid: tokenUtils.isTokenValid,
    getTokenInfo: tokenUtils.getTokenInfo,
    getStats: tokenUtils.getStats,
    forceCleanup: tokenUtils.forceCleanup
  };
};

/**
 * Admin utilities for token management
 */
  /**
   * Get detailed token information for admin dashboard
   */
  getDetailedStats: () => {
    const stats = tokenCleanupManager.getCleanupStats();
    const config = tokenCleanupManager[&apos;config&apos;];
    
    return {
      ...stats,
      config: {
        maxTokenAge: config.maxTokenAge,
        cleanupInterval: config.cleanupInterval,
        maxStoredTokens: config.maxStoredTokens
      },
      nextCleanup: tokenCleanupManager[&apos;cleanupTimer&apos;] ? 
        Date.now() + config.cleanupInterval : null
    };
  },

  /**
   * Update cleanup configuration
   */
  updateConfig: (newConfig: Partial<TokenCleanupConfig>) => {
    const currentConfig = tokenCleanupManager['config'];
    const mergedConfig = { ...currentConfig, ...newConfig };
    
    tokenCleanupManager.stopCleanup();
    tokenCleanupManager['config'] = mergedConfig;
    tokenCleanupManager.startCleanup();
    
    console.log('Token cleanup configuration updated:', mergedConfig);
  },

  /**
   * Export token data for analysis
   */
  exportTokenData: () => {
    const tokens = tokenCleanupManager['getStoredTokens']();
    return tokens.map(token => ({
      ...token,
      token: `${token.token.substring(0, 8)}...`, // Mask token for security
      age: Date.now() - token.timestamp
    }));
  }
};