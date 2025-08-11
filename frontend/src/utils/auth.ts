/**
 * Authentication utility functions
 */

// Get authentication token from local storage
export const getAuthToken = (): string => {
  if (typeof window !== &apos;undefined&apos;) {
    return localStorage.getItem(&apos;token&apos;) || &apos;&apos;;
  }
  return &apos;&apos;;
};

// Set authentication token in local storage
export const setAuthToken = (token: string): void => {
  if (typeof window !== &apos;undefined&apos;) {
    localStorage.setItem(&apos;token&apos;, token);
  }
};

// Remove authentication token from local storage
export const removeAuthToken = (): void => {
  if (typeof window !== &apos;undefined&apos;) {
    localStorage.removeItem(&apos;token&apos;);
  }
};

// Check if user is authenticated
export const isAuthenticated = (): boolean => {
  return !!getAuthToken();
};

// Parse JWT token to get user information
export const parseToken = (token: string): unknown => {
  try {
    const base64Url = token.split(&apos;.&apos;)[1];
    const base64 = base64Url.replace(/-/g, &apos;+&apos;).replace(/_/g, &apos;/&apos;);
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split(&apos;&apos;)
        .map((c) => &apos;%&apos; + (&apos;00&apos; + c.charCodeAt(0).toString(16)).slice(-2))
        .join(&apos;&apos;)
    );
    return JSON.parse(jsonPayload);
  } catch (error) {
    return null;
  }
};

// Check if token is expired
export const isTokenExpired = (token: string): boolean => {
  const decoded = parseToken(token);
  if (!decoded) return true;
  
  const currentTime = Date.now() / 1000;
  return decoded.exp < currentTime;
};

// Get user ID from token
export const getUserIdFromToken = (token: string): string | null => {
  const decoded = parseToken(token);
  return decoded?.user_id || null;
};

export default {
  getAuthToken,
  setAuthToken,
  removeAuthToken,
  isAuthenticated,
  parseToken,
  isTokenExpired,
  getUserIdFromToken,
};