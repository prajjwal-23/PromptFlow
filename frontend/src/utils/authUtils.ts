/**
 * Authentication Utilities
 *
 * Helper functions for authentication token management and validation
 */

// Manual JWT decode function (no external dependencies)
const base64UrlDecode = (str: string): string => {
  try {
    // Replace URL-safe characters
    const base64 = str.replace(/-/g, '+').replace(/_/g, '/');
    const decoded = atob(base64);
    return decoded;
  } catch (error) {
      console.error('Base64 decode error:', error);
      return '';
    }
  };

const jwtDecode = (token: string): any => {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) {
      throw new Error('Invalid JWT token format');
    }
    
    const header = JSON.parse(base64UrlDecode(parts[0]));
    const payload = JSON.parse(base64UrlDecode(parts[1]));
    
    return {
      ...header,
      ...payload,
      header,
      payload
    };
  } catch (error) {
    console.error('JWT decode error:', error);
    throw new Error('Invalid JWT token');
  }
};

// Token validation utilities
export const isTokenExpired = (token: string | null): boolean => {
  if (!token) return true;

  try {
    const decoded = jwtDecode(token);
    const currentTime = Date.now() / 1000;
    return decoded.exp < currentTime;
  } catch (error) {
    console.error('Token validation error:', error);
    return true;
  }
};

export const getTokenPayload = (token: string) => {
  try {
    return jwtDecode(token);
  } catch (error) {
    console.error('Token decode error:', error);
    return null;
  }
};

export const getTokenRemainingTime = (token: string): number => {
  const payload = getTokenPayload(token);
  if (!payload || !payload.exp) return 0;
  
  const currentTime = Date.now() / 1000;
  return Math.max(0, payload.exp - currentTime);
};

// Local storage utilities
export const storage = {
  get: (key: string): string | null => {
    if (typeof window === 'undefined') return null;
    try {
      return localStorage.getItem(key);
    } catch (error) {
      console.error('LocalStorage get error:', error);
      return null;
    }
  },

  set: (key: string, value: string): void => {
    if (typeof window === 'undefined') return;
    try {
      localStorage.setItem(key, value);
    } catch (error) {
      console.error('LocalStorage set error:', error);
    }
  },

  remove: (key: string): void => {
    if (typeof window === 'undefined') return;
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.error('LocalStorage remove error:', error);
    }
  },

  clear: (): void => {
    if (typeof window === 'undefined') return;
    try {
      localStorage.clear();
    } catch (error) {
      console.error('LocalStorage clear error:', error);
    }
  }
};

// Authentication state utilities
export const getStoredAuthState = () => {
  const accessToken = storage.get('accessToken');
  const refreshToken = storage.get('refreshToken');
  const userStr = storage.get('user');
  
  return {
    accessToken,
    refreshToken,
    user: userStr ? JSON.parse(userStr) : null,
    isAuthenticated: !!(isTokenExpired(accessToken) || !accessToken || !refreshToken)
  };
};

export const clearAuthState = (): void => {
  storage.remove('accessToken');
  storage.remove('refreshToken');
  storage.remove('user');
};

export const saveAuthState = (accessToken: string, refreshToken: string, user: any): void => {
  storage.set('accessToken', accessToken);
  storage.set('refreshToken', refreshToken);
  storage.set('user', JSON.stringify(user));
};

// API utilities
export const createAuthHeaders = (accessToken: string): Record<string, string> => ({
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${accessToken}`,
});

// Refresh token utility
export const refreshAccessToken = async (refreshToken: string): Promise<string> => {
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
  
  try {
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        refresh_token: refreshToken,
      }),
    });

    if (!response.ok) {
      throw new Error('Token refresh failed');
    }

    const data = await response.json();
    return data.access_token;
  } catch (error) {
    console.error('Token refresh error:', error);
    throw error;
  }
};

// Validation utilities
export const validateAuthState = (): boolean => {
  const { accessToken, refreshToken, user, isAuthenticated } = getStoredAuthState();
  
  // Check if all required auth data exists
  if (!accessToken || !refreshToken || !user) {
    return false;
  }
  
  // Check if token is not expired
  if (isTokenExpired(accessToken)) {
    return false;
  }
  
  // Check if user has required fields
  if (!user.id || !user.email) {
    return false;
  }
  
  return true;
};

// Debug utilities
export const debugAuthState = (): void => {
  const state = getStoredAuthState();
  console.group('🔐 Authentication State Debug');
  console.log('Access Token:', state.accessToken ? `${state.accessToken.substring(0, 20)}...` : 'None');
  console.log('Refresh Token:', state.refreshToken ? `${state.refreshToken.substring(0, 20)}...` : 'None');
  console.log('User:', state.user ? `${state.user.email} (${state.user.id})` : 'None');
  console.log('Is Authenticated:', state.isAuthenticated);
  
  if (state.accessToken) {
    const remainingTime = getTokenRemainingTime(state.accessToken);
    console.log('Token expires in:', remainingTime > 0 ? `${Math.floor(remainingTime / 60)}m ${Math.floor(remainingTime % 60)}s` : 'Expired');
  }
  
  console.groupEnd();
};