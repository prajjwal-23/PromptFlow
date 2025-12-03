/**
 * Authentication Provider Component
 *
 * This component handles authentication initialization and provides
 * auth context to the entire application.
 */

'use client';

import { useEffect, useState, ReactNode } from 'react';
import { useAuthStore } from '../store/authStore';
import { useAuthInit, useAuthPersistence, useAutoLogout } from '../hooks/useAuthInit';

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [isInitialized, setIsInitialized] = useState(false);
  const { isAuthenticated, isLoading } = useAuthStore();

  // Initialize authentication on app startup
  const { isAuthenticated: authStatus, isLoading: loadingStatus } = useAuthInit();
  
  // Handle auth state persistence
  useAuthPersistence();
  
  // Handle automatic logout on token expiry
  useAutoLogout();

  useEffect(() => {
    // Mark as initialized after first render
    setIsInitialized(true);
  }, []);

  // Show loading state during initialization
  if (!isInitialized || loadingStatus) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-white border-t-transparent rounded-full animate-spin mb-4"></div>
          <p className="text-white text-lg">Initializing Authentication...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}