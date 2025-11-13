/**
 * Create Workspace Page
 * 
 * This page provides a dedicated interface for creating new workspaces.
 */
'use client';

import { useRouter } from 'next/navigation';
import { useWorkspaceStore } from '../../store/workspaceStore';
import { ProtectedRoute } from '../../components/ProtectedRoute';
import { WorkspaceForm } from '../../components/Workspace/WorkspaceForm';

export default function CreateWorkspacePage() {
  const router = useRouter();
  const { createWorkspace, isCreating } = useWorkspaceStore();

  const handleCreateWorkspace = async (data: { name: string; description?: string }) => {
    try {
      const newWorkspace = await createWorkspace(data);
      // Navigate to the new workspace
      router.push(`/workspaces/${newWorkspace.id}`);
    } catch (error) {
      console.error('Failed to create workspace:', error);
    }
  };

  const handleCancel = () => {
    router.push('/workspaces');
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Create New Workspace</h1>
            <p className="mt-2 text-gray-600">
              Set up a new workspace to organize your projects and collaborate with your team
            </p>
          </div>

          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center">
                    <svg
                      className="h-5 w-5 text-white"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 4v16m8-8H4"
                      />
                    </svg>
                  </div>
                </div>
                <div className="ml-4">
                  <h2 className="text-lg font-medium text-gray-900">Workspace Details</h2>
                  <p className="text-sm text-gray-500">
                    Provide the basic information for your new workspace
                  </p>
                </div>
              </div>
            </div>
            
            <div className="px-6 py-6">
              <WorkspaceForm
                onSubmit={handleCreateWorkspace}
                onCancel={handleCancel}
                isSubmitting={isCreating}
                submitButtonText="Create Workspace"
              />
            </div>
          </div>

          <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg
                  className="h-5 w-5 text-blue-400"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-blue-800">
                  Workspace Tips
                </h3>
                <div className="mt-2 text-sm text-blue-700">
                  <ul className="list-disc list-inside space-y-1">
                    <li>Choose a descriptive name that clearly identifies the workspace</li>
                    <li>Add a brief description to help team members understand the workspace purpose</li>
                    <li>You'll be the owner of this workspace and can invite team members later</li>
                    <li>Workspaces help you organize projects and manage access control</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}