/**
 * Authentication state management using Zustand.
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import axios from 'axios';

// Types
export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

export interface AuthState {
  // State
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, full_name: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshAccessToken: () => Promise<void>;
  updateProfile: (data: { full_name: string; email: string }) => Promise<void>;
  clearError: () => void;
  setLoading: (loading: boolean) => void;
}

// API base URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refreshToken');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token } = response.data;
          localStorage.setItem('accessToken', access_token);

          // Retry the original request
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // If refresh fails, logout user
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Create the auth store
export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // Actions
      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.post('/auth/login', {
            email,
            password,
          });

          const { access_token, refresh_token, user } = response.data;

          // Store tokens securely
          localStorage.setItem('accessToken', access_token);
          localStorage.setItem('refreshToken', refresh_token);

          set({
            user,
            accessToken: access_token,
            refreshToken: refresh_token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Login failed';
          set({
            isLoading: false,
            error: errorMessage,
            isAuthenticated: false,
            user: null,
            accessToken: null,
            refreshToken: null,
          });
          throw error;
        }
      },

      register: async (email: string, password: string, full_name: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.post('/auth/register', {
            email,
            password,
            full_name,
          });

          // After successful registration, automatically log in
          await get().login(email, password);
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Registration failed';
          set({
            isLoading: false,
            error: errorMessage,
          });
          throw error;
        }
      },

      logout: async () => {
        try {
          // Call logout endpoint
          await api.post('/auth/logout');
        } catch (error) {
          // Even if logout endpoint fails, clear local state
          console.error('Logout error:', error);
        } finally {
          // Clear all auth data
          localStorage.removeItem('accessToken');
          localStorage.removeItem('refreshToken');

          set({
            user: null,
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
        }
      },

      refreshAccessToken: async () => {
        const { refreshToken } = get();
        if (!refreshToken) {
          throw new Error('No refresh token available');
        }

        try {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token } = response.data;
          localStorage.setItem('accessToken', access_token);

          set({ accessToken: access_token });
        } catch (error) {
          // If refresh fails, logout user
          await get().logout();
          throw error;
        }
      },

      updateProfile: async (data: { full_name: string; email: string }) => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.put('/users/me', data);
          const updatedUser = response.data.user;

          set({
            user: updatedUser,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Profile update failed';
          set({
            isLoading: false,
            error: errorMessage,
          });
          throw error;
        }
      },

      clearError: () => {
        set({ error: null });
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// Export the API instance for use in other stores
export { api };

// Helper function to check if token is expired
export const isTokenExpired = (token: string | null): boolean => {
  if (!token) return true;

  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const now = Date.now() / 1000;
    return payload.exp < now;
  } catch {
    return true;
  }
};

// Initialize auth state from persisted storage
export const initializeAuth = async () => {
  const accessToken = localStorage.getItem('accessToken');
  const refreshToken = localStorage.getItem('refreshToken');
  const store = useAuthStore.getState();

  // Set loading state
  store.setLoading(true);

  if (accessToken && refreshToken) {
    if (isTokenExpired(accessToken)) {
      // Token expired, try to refresh
      try {
        await store.refreshAccessToken();
        // Refresh successful, user is authenticated
        store.setLoading(false);
      } catch (error) {
        // Refresh failed, clear auth state
        await store.logout();
        store.setLoading(false);
      }
    } else {
      // Token is valid, set authenticated state
      store.setLoading(false);
      // The persisted state should already have isAuthenticated: true
    }
  } else {
    // No tokens, set loading to false
    store.setLoading(false);
  }
};