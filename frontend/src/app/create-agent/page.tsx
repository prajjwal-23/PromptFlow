/**
 * Create Agent Page
 * 
 * This page provides a dedicated interface for creating new agents.
 */
'use client';

import { useRouter } from 'next/navigation';
import { useWorkspaceStore } from '../../store/workspaceStore';
import { useAgentStore } from '../../store/agentStore';
import { ProtectedRoute } from '../../components/ProtectedRoute';
import { AgentForm } from '../../components/Agent/AgentForm';

export default function CreateAgentPage() {
  const router = useRouter();
  const { currentWorkspace } = useWorkspaceStore();
  const { createAgent, isCreating } = useAgentStore();

  const handleCreateAgent = async (data: { name: string; description?: string; workspace_id?: string }) => {
    try {
      const workspaceId = data.workspace_id || currentWorkspace?.id;
      if (!workspaceId) {
        throw new Error('Workspace is required to create an agent');
      }

      const newAgent = await createAgent({
        name: data.name,
        description: data.description,
        workspace_id: workspaceId,
      });
      
      // Navigate to the agent editor
      router.push(`/agents/${newAgent.id}/edit`);
    } catch (error) {
      console.error('Failed to create agent:', error);
    }
  };

  const handleCancel = () => {
    if (currentWorkspace) {
      router.push(`/workspaces/${currentWorkspace.id}/agents`);
    } else {
      router.push('/agents');
    }
  };

  if (!currentWorkspace) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">No Workspace Selected</h1>
            <p className="text-gray-600 mb-4">Please select a workspace to create an agent.</p>
            <button
              onClick={() => router.push('/workspaces')}
              className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/90"
            >
              Go to Workspaces
            </button>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-2">
              <button
                onClick={handleCancel}
                className="text-gray-500 hover:text-gray-700"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <h1 className="text-3xl font-bold text-gray-900">Create New Agent</h1>
            </div>
            <p className="text-gray-600">
              Set up a new AI agent to automate your workflows in {currentWorkspace.name}
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
                        d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                      />
                    </svg>
                  </div>
                </div>
                <div className="ml-4">
                  <h2 className="text-lg font-medium text-gray-900">Agent Details</h2>
                  <p className="text-sm text-gray-500">
                    Provide the basic information for your new AI agent
                  </p>
                </div>
              </div>
            </div>
            
            <div className="px-6 py-6">
              <AgentForm
                onSubmit={handleCreateAgent}
                onCancel={handleCancel}
                isSubmitting={isCreating}
                workspaceId={currentWorkspace.id}
                submitButtonText="Create Agent"
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
                  Agent Creation Tips
                </h3>
                <div className="mt-2 text-sm text-blue-700">
                  <ul className="list-disc list-inside space-y-1">
                    <li>Choose a descriptive name that clearly identifies the agent's purpose</li>
                    <li>Add a brief description to help team members understand what the agent does</li>
                    <li>You'll be able to design the agent's workflow in the visual editor next</li>
                    <li>Agents can be configured to use different AI models and tools</li>
                    <li>Test your agent thoroughly before deploying it to production</li>
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