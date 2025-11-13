/**
 * Workspace Form Component
 * 
 * This component handles workspace creation and editing with form validation.
 */

import { useState, useEffect } from 'react';

interface WorkspaceFormData {
  name: string;
  description: string;
}

interface WorkspaceFormProps {
  workspace?: {
    name: string;
    description: string | null;
  };
  onSubmit: (data: { name: string; description?: string }) => Promise<void>;
  onCancel: () => void;
  isSubmitting: boolean;
  submitButtonText?: string;
}

export function WorkspaceForm({
  workspace,
  onSubmit,
  onCancel,
  isSubmitting,
  submitButtonText = 'Create Workspace',
}: WorkspaceFormProps) {
  const [formData, setFormData] = useState<WorkspaceFormData>({
    name: '',
    description: '',
  });
  const [formErrors, setFormErrors] = useState<Partial<WorkspaceFormData>>({});

  // Initialize form with workspace data if editing
  useEffect(() => {
    if (workspace) {
      setFormData({
        name: workspace.name,
        description: workspace.description || '',
      });
    }
  }, [workspace]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Clear errors when user starts typing
    if (formErrors[name as keyof WorkspaceFormData]) {
      setFormErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateForm = (): boolean => {
    const errors: Partial<WorkspaceFormData> = {};

    if (!formData.name) {
      errors.name = 'Workspace name is required';
    } else if (formData.name.trim().length < 2) {
      errors.name = 'Workspace name must be at least 2 characters long';
    } else if (formData.name.trim().length > 100) {
      errors.name = 'Workspace name must be less than 100 characters long';
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
      await onSubmit({
        name: formData.name.trim(),
        description: formData.description.trim() || undefined,
      });
    } catch (error) {
      // Error is handled by the parent component
      console.error('Form submission failed:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label htmlFor="name" className="block text-sm font-medium text-gray-700">
          Workspace Name *
        </label>
        <div className="mt-1">
          <input
            id="name"
            name="name"
            type="text"
            required
            value={formData.name}
            onChange={handleChange}
            className={`block w-full appearance-none rounded-md border px-3 py-2 placeholder-gray-400 shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm ${
              formErrors.name
                ? 'border-red-300 text-red-900 placeholder-red-300 focus:border-red-500 focus:ring-red-500'
                : 'border-gray-300 focus:ring-primary'
            }`}
            placeholder="Enter workspace name"
            disabled={isSubmitting}
          />
          {formErrors.name && (
            <p className="mt-2 text-sm text-red-600">{formErrors.name}</p>
          )}
        </div>
      </div>

      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700">
          Description
        </label>
        <div className="mt-1">
          <textarea
            id="description"
            name="description"
            rows={4}
            value={formData.description}
            onChange={handleChange}
            className={`block w-full appearance-none rounded-md border px-3 py-2 placeholder-gray-400 shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm ${
              formErrors.description
                ? 'border-red-300 text-red-900 placeholder-red-300 focus:border-red-500 focus:ring-red-500'
                : 'border-gray-300 focus:ring-primary'
            }`}
            placeholder="Describe what this workspace is for (optional)"
            disabled={isSubmitting}
          />
          {formErrors.description && (
            <p className="mt-2 text-sm text-red-600">{formErrors.description}</p>
          )}
        </div>
        <p className="mt-2 text-sm text-gray-500">
          Brief description to help team members understand the purpose of this workspace.
        </p>
      </div>

      <div className="flex gap-3 justify-end pt-4 border-t border-gray-200">
        <button
          type="button"
          onClick={onCancel}
          disabled={isSubmitting}
          className="px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isSubmitting}
          className="px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting ? (
            <div className="flex items-center gap-2">
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
              {workspace ? 'Updating...' : 'Creating...'}
            </div>
          ) : (
            submitButtonText
          )}
        </button>
      </div>
    </form>
  );
}