import { AUTH_ROUTES } from '@/constants';

export interface DeepLinkConfig {
  baseUrl?: string;
  utm?: {
    source?: string;
    medium?: string;
    campaign?: string;
  };
}

/**
 * Generate deep link for email verification
 */
export function generateEmailVerificationDeepLink(
  token: string, 
  config: DeepLinkConfig = {}
): string {
  const { baseUrl, utm } = config;
  const base = baseUrl || (typeof window !== 'undefined' ? window.location.origin : '');
  
  const url = new URL(`${base}/auth/verify-email/${token}`);
  
  // Add UTM parameters if provided
  if (utm) {
    if (utm.source) url.searchParams.set('utm_source', utm.source);
    if (utm.medium) url.searchParams.set('utm_medium', utm.medium);
    if (utm.campaign) url.searchParams.set('utm_campaign', utm.campaign);
  }
  
  return url.toString();
}

/**
 * Generate deep link for password reset
 */
export function generatePasswordResetDeepLink(
  token: string, 
  config: DeepLinkConfig = {}
): string {
  const { baseUrl, utm } = config;
  const base = baseUrl || (typeof window !== 'undefined' ? window.location.origin : '');
  
  const url = new URL(`${base}/auth/reset-password/${token}`);
  
  // Add UTM parameters if provided
  if (utm) {
    if (utm.source) url.searchParams.set('utm_source', utm.source);
    if (utm.medium) url.searchParams.set('utm_medium', utm.medium);
    if (utm.campaign) url.searchParams.set('utm_campaign', utm.campaign);
  }
  
  return url.toString();
}

/**
 * Generate authentication deep link with redirect
 */
export function generateAuthDeepLink(
  authType: 'login' | 'register',
  redirectTo?: string,
  config: DeepLinkConfig = {}
): string {
  const { baseUrl, utm } = config;
  const base = baseUrl || (typeof window !== 'undefined' ? window.location.origin : '');
  
  const authPath = authType === 'login' ? AUTH_ROUTES.LOGIN : AUTH_ROUTES.REGISTER;
  const url = new URL(`${base}${authPath}`);
  
  // Add redirect parameter
  if (redirectTo) {
    url.searchParams.set('redirect', redirectTo);
  }
  
  // Add UTM parameters if provided
  if (utm) {
    if (utm.source) url.searchParams.set('utm_source', utm.source);
    if (utm.medium) url.searchParams.set('utm_medium', utm.medium);
    if (utm.campaign) url.searchParams.set('utm_campaign', utm.campaign);
  }
  
  return url.toString();
}

/**
 * Parse deep link parameters from URL
 */
export function parseDeepLinkParams(url: string): {
  token?: string;
  redirect?: string;
  utm?: {
    source?: string;
    medium?: string;
    campaign?: string;
  };
} {
  const urlObj = new URL(url);
  const pathname = urlObj.pathname;
  const searchParams = urlObj.searchParams;
  
  // Extract token from path
  let token: string | undefined;
  if (pathname.includes('/verify-email/')) {
    const segments = pathname.split('/');
    const tokenIndex = segments.indexOf('verify-email') + 1;
    token = segments[tokenIndex];
  } else if (pathname.includes('/reset-password/')) {
    const segments = pathname.split('/');
    const tokenIndex = segments.indexOf('reset-password') + 1;
    token = segments[tokenIndex];
  }
  
  // Extract query parameters
  const redirect = searchParams.get('redirect') || undefined;
  const utm = {
    source: searchParams.get('utm_source') || undefined,
    medium: searchParams.get('utm_medium') || undefined,
    campaign: searchParams.get('utm_campaign') || undefined,
  };
  
  // Only include utm if at least one parameter is present
  const hasUtm = utm.source || utm.medium || utm.campaign;
  
  return {
    token,
    redirect,
    utm: hasUtm ? utm : undefined,
  };
}

/**
 * Validate token format (basic validation)
 */
export function isValidToken(token: string): boolean {
  // Basic validation - token should be a non-empty string with reasonable length
  return typeof token === 'string' && 
         token.length > 0 && 
         token.length <= 255 && 
         /^[a-zA-Z0-9\-_]+$/.test(token);
}

/**
 * Generate shareable authentication link
 */
export function generateShareableAuthLink(
  type: 'email-verification' | 'password-reset' | 'login' | 'register',
  token?: string,
  redirectTo?: string,
  config: DeepLinkConfig = {}
): string {
  switch (type) {
    case 'email-verification':
      if (!token) throw new Error('Token is required for email verification link');
      return generateEmailVerificationDeepLink(token, config);
      
    case 'password-reset':
      if (!token) throw new Error('Token is required for password reset link');
      return generatePasswordResetDeepLink(token, config);
      
    case 'login':
      return generateAuthDeepLink('login', redirectTo, config);
      
    case 'register':
      return generateAuthDeepLink('register', redirectTo, config);
      
    default:
      throw new Error(`Unsupported link type: ${type}`);
  }
}

/**
 * Copy link to clipboard with fallback
 */
export async function copyLinkToClipboard(link: string): Promise<boolean> {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(link);
      return true;
    } else {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = link;
      textArea.style.position = 'fixed';
      textArea.style.left = '-999999px';
      textArea.style.top = '-999999px';
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      const success = document.execCommand('copy');
      textArea.remove();
      return success;
    }
  } catch (error) {
    console.error('Failed to copy link to clipboard:', error);
    return false;
  }
}