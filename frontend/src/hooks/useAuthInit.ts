/**
 * Authentication Initialization Hook
 * 
 * This hook ensures authentication state is properly initialized
 * and handles token refresh on app startup.
 */

'use client';

import { useEffect } from 'react';
import { useAuthStore } from '../store/authStore';
import { isTokenExpired, getStoredAuthState, saveAuthState, clearAuthState } from '../utils/authUtils';

export function useAuthInit() {
  const { 
    isAuthenticated, 
    accessToken, 
    refreshToken, 
    user, 
    setLoading,
    logout 
  } = useAuthStore();

  useEffect(() => {
    // Initialize authentication on app startup
    const initAuth = async () => {
      console.log('🔐 Initializing authentication...');
      
      // Check if tokens exist in localStorage
      const storedAccessToken = localStorage.getItem('accessToken');
      const storedRefreshToken = localStorage.getItem('refreshToken');
      const storedUser = localStorage.getItem('user');
      
      if (storedAccessToken && storedRefreshToken) {
        try {
          // Validate stored access token
          if (isTokenExpired(storedAccessToken)) {
            console.log('⚠️ Access token expired, attempting refresh...');
            
            // Try to refresh the token
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/auth/refresh`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                refresh_token: storedRefreshToken,
              }),
            });

            if (response.ok) {
              const data = await response.json();
              const newAccessToken = data.access_token;
              
              // Update tokens in localStorage using utility function
              saveAuthState(newAccessToken, storedRefreshToken, storedUser);
              
              // Update Zustand store
              useAuthStore.setState({
                user: storedUser ? JSON.parse(storedUser) : null,
                accessToken: newAccessToken,
                refreshToken: storedRefreshToken,
                isAuthenticated: true,
                isLoading: false,
                error: null,
              });
              
              console.log('✅ Token refresh successful');
            } else {
              // Refresh failed, clear tokens and logout
              console.log('❌ Token refresh failed, logging out...');
              localStorage.removeItem('accessToken');
              localStorage.removeItem('refreshToken');
              localStorage.removeItem('user');
              logout();
            }
          } else {
            // Token is valid, restore auth state
            console.log('✅ Valid token found, restoring auth state');
            setLoading(true);
            useAuthStore.setState({
              user: storedUser ? JSON.parse(storedUser) : null,
              accessToken: storedAccessToken,
              refreshToken: storedRefreshToken,
              isAuthenticated: true,
              isLoading: false,
              error: null,
            });
          }
        } catch (error) {
          console.error('❌ Auth initialization error:', error);
          // Clear invalid tokens using utility function
          clearAuthState();
          logout();
        }
      } else {
        console.log('ℹ️ No tokens found, user not authenticated');
        // Ensure store is in clean state
        useAuthStore.setState({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
        });
      }
    };

    initAuth();
  }, []);

  // Set up periodic token refresh check
  useEffect(() => {
    if (!isAuthenticated || !accessToken) return;

    const checkTokenExpiry = () => {
      if (isTokenExpired(accessToken)) {
        console.log('⚠️ Token expired during session, attempting refresh...');
        // The AuthProvider will handle this, but we can add additional logic here if needed
      }
    };

    // Check token expiry every 5 minutes
    const interval = setInterval(checkTokenExpiry, 5 * 60 * 1000);

    return () => clearInterval(interval);
  }, [isAuthenticated, accessToken]);

  return { isAuthenticated, isLoading: useAuthStore.getState().isLoading, user };
}

/**
 * Hook to handle authentication state persistence
 */
export function useAuthPersistence() {
  const { isAuthenticated, user, accessToken, refreshToken } = useAuthStore();

  useEffect(() => {
    // Save user data to localStorage when it changes
    if (user && isAuthenticated) {
      localStorage.setItem('user', JSON.stringify(user));
    }
  }, [user, isAuthenticated]);

  useEffect(() => {
    // Save tokens to localStorage when they change
    if (accessToken) {
      localStorage.setItem('accessToken', accessToken);
    }
  }, [accessToken]);

  useEffect(() => {
    // Save refresh token to localStorage when it changes
    if (refreshToken) {
      localStorage.setItem('refreshToken', refreshToken);
    }
  }, [refreshToken]);

  // Clear localStorage on logout
  useEffect(() => {
    if (!isAuthenticated) {
      // Don't immediately clear on logout - let the logout function handle this
      // This prevents clearing during normal app flow
    }
  }, [isAuthenticated]);
}

/**
 * Hook to handle automatic logout on token expiry
 */
export function useAutoLogout() {
  const { isAuthenticated, accessToken, logout } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated || !accessToken) return;

    const checkAndLogout = () => {
      if (isTokenExpired(accessToken)) {
        console.log('🚪 Auto-logging out due to token expiry');
        logout();
      }
    };

    // Check every minute
    const interval = setInterval(checkAndLogout, 60 * 1000);

    return () => clearInterval(interval);
  }, [isAuthenticated, accessToken, logout]);
}