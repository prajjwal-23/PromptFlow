/**
 * Profile Form Component
 * 
 * This component handles the user profile update functionality with form validation.
 */

import { useState, useEffect } from 'react';
import { useAuthStore } from '../../store/authStore';

interface ProfileFormData {
  full_name: string;
  email: string;
}

export function ProfileForm() {
  const { user, updateProfile, isLoading, error, clearError } = useAuthStore();
  const [formData, setFormData] = useState<ProfileFormData>({
    full_name: '',
    email: '',
  });
  const [formErrors, setFormErrors] = useState<Partial<ProfileFormData>>({});
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Initialize form with user data
  useEffect(() => {
    if (user) {
      setFormData({
        full_name: user.full_name,
        email: user.email,
      });
    }
  }, [user]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Clear errors and success message when user starts typing
    if (formErrors[name as keyof ProfileFormData]) {
      setFormErrors(prev => ({ ...prev, [name]: '' }));
    }
    if (error) {
      clearError();
    }
    if (successMessage) {
      setSuccessMessage(null);
    }
  };

  const validateForm = (): boolean => {
    const errors: Partial<ProfileFormData> = {};

    if (!formData.email) {
      errors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      errors.email = 'Email is invalid';
    }

    if (!formData.full_name) {
      errors.full_name = 'Full name is required';
    } else if (formData.full_name.trim().length < 2) {
      errors.full_name = 'Full name must be at least 2 characters';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      await updateProfile({
        full_name: formData.full_name.trim(),
        email: formData.email.toLowerCase().trim(),
      });
      
      setSuccessMessage('Profile updated successfully!');
    } catch (error) {
      // Error is handled by the store
      console.error('Profile update failed:', error);
    }
  };

  if (!user) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg
                className="h-5 w-5 text-red-400"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                {error}
              </h3>
            </div>
          </div>
        </div>
      )}

      {successMessage && (
        <div className="rounded-md bg-green-50 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg
                className="h-5 w-5 text-green-400"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-green-800">
                {successMessage}
              </h3>
            </div>
          </div>
        </div>
      )}

      <div>
        <label htmlFor="full_name" className="block text-sm font-medium text-gray-700">
          Full name
        </label>
        <div className="mt-1">
          <input
            id="full_name"
            name="full_name"
            type="text"
            autoComplete="name"
            required
            value={formData.full_name}
            onChange={handleChange}
            className={`block w-full appearance-none rounded-md border px-3 py-2 placeholder-gray-400 shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm ${
              formErrors.full_name
                ? 'border-red-300 text-red-900 placeholder-red-300 focus:border-red-500 focus:ring-red-500'
                : 'border-gray-300 focus:ring-primary'
            }`}
            placeholder="Enter your full name"
          />
          {formErrors.full_name && (
            <p className="mt-2 text-sm text-red-600">{formErrors.full_name}</p>
          )}
        </div>
      </div>

      <div>
        <label htmlFor="email" className="block text-sm font-medium text-gray-700">
          Email address
        </label>
        <div className="mt-1">
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            value={formData.email}
            onChange={handleChange}
            className={`block w-full appearance-none rounded-md border px-3 py-2 placeholder-gray-400 shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm ${
              formErrors.email
                ? 'border-red-300 text-red-900 placeholder-red-300 focus:border-red-500 focus:ring-red-500'
                : 'border-gray-300 focus:ring-primary'
            }`}
            placeholder="Enter your email"
          />
          {formErrors.email && (
            <p className="mt-2 text-sm text-red-600">{formErrors.email}</p>
          )}
        </div>
      </div>

      <div className="pt-4">
        <div className="block text-sm font-medium text-gray-700 mb-4">
          Account Information
        </div>
        <div className="bg-gray-50 rounded-lg p-4 space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Account Status:</span>
            <span className={`font-medium ${user.is_active ? 'text-green-600' : 'text-red-600'}`}>
              {user.is_active ? 'Active' : 'Inactive'}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Member Since:</span>
            <span className="font-medium text-gray-900">
              {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'Unknown'}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">User ID:</span>
            <span className="font-medium text-gray-900 text-xs">
              {user.id}
            </span>
          </div>
        </div>
      </div>

      <div className="flex gap-3">
        <button
          type="submit"
          disabled={isLoading}
          className="flex-1 justify-center rounded-md border border-transparent bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <div className="flex items-center justify-center gap-2">
              <svg
                className="h-4 w-4 animate-spin"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                  fill="none"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              Updating...
            </div>
          ) : (
            'Update Profile'
          )}
        </button>
      </div>
    </form>
  );
}