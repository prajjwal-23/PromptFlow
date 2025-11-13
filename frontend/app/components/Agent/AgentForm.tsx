/**
 * Agent Form Component
 * 
 * This component handles agent creation and editing with form validation.
 */

import { useState, useEffect } from 'react';

interface AgentFormData {
  name: string;
  description: string;
}

interface AgentFormProps {
  agent?: {
    name: string;
    description: string | null;
  };
  onSubmit: (data: { name: string; description?: string; workspace_id?: string }) => Promise<void>;
  onCancel: () => void;
  isSubmitting: boolean;
  submitButtonText?: string;
  workspaceId?: string;
}

export function AgentForm({
  agent,
  onSubmit,
  onCancel,
  isSubmitting,
  submitButtonText = 'Create Agent',
  workspaceId,
}: AgentFormProps) {
  const [formData, setFormData] = useState<AgentFormData>({
    name: '',
    description: '',
  });
  const [formErrors, setFormErrors] = useState<Partial<AgentFormData>>({});

  // Initialize form with agent data if editing
  useEffect(() => {
    if (agent) {
      setFormData({
        name: agent.name,
        description: agent.description || '',
      });
    }
  }, [agent]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Clear errors when user starts typing
    if (formErrors[name as keyof AgentFormData]) {
      setFormErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateForm = (): boolean => {
    const errors: Partial<AgentFormData> = {};

    if (!formData.name) {
      errors.name = 'Agent name is required';
    } else if (formData.name.trim().length < 2) {
      errors.name = 'Agent name must be at least 2 characters long';
    } else if (formData.name.trim().length > 100) {
      errors.name = 'Agent name must be less than 100 characters long';
    }

    if (formData.description && formData.description.trim().length > 1000) {
      errors.description = 'Description must be less than 1000 characters long';
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
        workspace_id: workspaceId,
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
          Agent Name *
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
            placeholder="Enter agent name"
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
            placeholder="Describe what this agent does and how it should behave (optional)"
            disabled={isSubmitting}
          />
          {formErrors.description && (
            <p className="mt-2 text-sm text-red-600">{formErrors.description}</p>
          )}
        </div>
        <p className="mt-2 text-sm text-gray-500">
          Brief description to help team members understand the purpose and functionality of this agent.
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
              {agent ? 'Updating...' : 'Creating...'}
            </div>
          ) : (
            submitButtonText
          )}
        </button>
      </div>
    </form>
  );
}