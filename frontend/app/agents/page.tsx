/**
 * Agents Page
 * 
 * This page displays all agents for the current user and allows agent management.
 */
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '../store/authStore';
import { useWorkspaceStore } from '../store/workspaceStore';
import { useAgentStore, getAgentStatus, getAgentStatusColor } from '../store/agentStore';
import { ProtectedRoute } from '../components/ProtectedRoute';
import { AgentCard } from '../components/Agent/AgentCard';
import { AgentForm } from '../components/Agent/AgentForm';

export default function AgentsPage() {
  const router = useRouter();
  const { user } = useAuthStore();
  const { currentWorkspace } = useWorkspaceStore();
  const {
    agents,
    isLoading,
    isCreating,
    error,
    fetchAgents,
    createAgent,
    clearError,
  } = useAgentStore();

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'inactive' | 'draft'>('all');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    if (currentWorkspace) {
      fetchAgents(currentWorkspace.id);
    } else {
      fetchAgents(); // Fetch all agents if no workspace is selected
    }
  }, [fetchAgents, currentWorkspace]);

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
      
      setShowCreateForm(false);
      // Navigate to the agent editor
      router.push(`/agents/${newAgent.id}/edit`);
    } catch (error) {
      console.error('Failed to create agent:', error);
    }
  };

  const handleAgentClick = (agentId: string) => {
    router.push(`/agents/${agentId}/edit`);
  };

  const handleAgentRun = (agentId: string) => {
    router.push(`/agents/${agentId}/run`);
  };

  // Filter agents based on status and search term
  const filteredAgents = agents.filter(agent => {
    const status = getAgentStatus(agent);
    
    // Status filter
    if (filterStatus !== 'all' && status !== filterStatus) {
      return false;
    }
    
    // Search filter
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      return (
        agent.name.toLowerCase().includes(searchLower) ||
        (agent.description && agent.description.toLowerCase().includes(searchLower))
      );
    }
    
    return true;
  });

  const getStatusCounts = () => {
    const counts = {
      all: agents.length,
      active: agents.filter(agent => getAgentStatus(agent) === 'active').length,
      inactive: agents.filter(agent => getAgentStatus(agent) === 'inactive').length,
      draft: agents.filter(agent => getAgentStatus(agent) === 'draft').length,
    };
    return counts;
  };

  const statusCounts = getStatusCounts();

  if (!currentWorkspace) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">No Workspace Selected</h1>
            <p className="text-gray-600 mb-4">Please select a workspace to manage agents.</p>
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
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <button
                    onClick={() => router.push('/workspaces')}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                  </button>
                  <h1 className="text-3xl font-bold text-gray-900">Agents</h1>
                  <span className="text-sm text-gray-500">
                    in {currentWorkspace.name}
                  </span>
                </div>
                <p className="text-gray-600">
                  Create and manage your AI agents
                </p>
              </div>
              <button
                onClick={() => setShowCreateForm(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
              >
                <svg
                  className="w-4 h-4 mr-2"
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
                Create Agent
              </button>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-6 rounded-md bg-red-50 p-4">
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
                  <h3 className="text-sm font-medium text-red-800">{error}</h3>
                </div>
                <div className="ml-auto pl-3">
                  <div className="-mx-1.5 -my-1.5">
                    <button
                      onClick={clearError}
                      className="inline-flex bg-red-50 rounded-md p-1.5 text-red-500 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-red-50 focus:ring-red-600"
                    >
                      <span className="sr-only">Dismiss</span>
                      <svg
                        className="h-5 w-5"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                      >
                        <path
                          fillRule="evenodd"
                          d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Filters and Search */}
          <div className="bg-white shadow rounded-lg p-6 mb-6">
            <div className="flex flex-col space-y-4 sm:flex-row sm:space-y-0 sm:space-x-4">
              {/* Search */}
              <div className="flex-1">
                <label htmlFor="search" className="sr-only">
                  Search agents
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <svg
                      className="h-5 w-5 text-gray-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                      />
                    </svg>
                  </div>
                  <input
                    id="search"
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-primary focus:border-primary sm:text-sm"
                    placeholder="Search agents..."
                  />
                </div>
              </div>

              {/* Status Filters */}
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-500">Filter by status:</span>
                <div className="flex rounded-md shadow-sm">
                  {(['all', 'active', 'inactive', 'draft'] as const).map((status) => (
                    <button
                      key={status}
                      onClick={() => setFilterStatus(status)}
                      className={`relative inline-flex items-center px-3 py-2 border text-sm font-medium focus:z-10 focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary ${
                        filterStatus === status
                          ? 'bg-primary text-white border-primary'
                          : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                      } ${
                        status === 'all' ? 'rounded-l-md' : ''
                      } ${
                        status === 'draft' ? 'rounded-r-md' : ''
                      }`}
                    >
                      {status.charAt(0).toUpperCase() + status.slice(1)}
                      <span className="ml-1 bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded text-xs">
                        {statusCounts[status]}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Loading State */}
          {isLoading && (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          )}

          {/* Empty State */}
          {!isLoading && filteredAgents.length === 0 && !showCreateForm && (
            <div className="text-center py-12">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
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
              <h3 className="mt-2 text-sm font-medium text-gray-900">No agents</h3>
              <p className="mt-1 text-sm text-gray-500">
                {searchTerm || filterStatus !== 'all' 
                  ? 'No agents match your current filters.'
                  : 'Get started by creating your first AI agent.'
                }
              </p>
              <div className="mt-6">
                <button
                  onClick={() => setShowCreateForm(true)}
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
                >
                  <svg
                    className="w-4 h-4 mr-2"
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
                  Create Agent
                </button>
              </div>
            </div>
          )}

          {/* Create Form */}
          {showCreateForm && (
            <div className="mb-8">
              <div className="bg-white shadow rounded-lg">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h2 className="text-lg font-medium text-gray-900">Create New Agent</h2>
                  <p className="mt-1 text-sm text-gray-500">
                    Set up a new AI agent to automate your workflows
                  </p>
                </div>
                <div className="px-6 py-6">
                  <AgentForm
                    onSubmit={handleCreateAgent}
                    onCancel={() => setShowCreateForm(false)}
                    isSubmitting={isCreating}
                    workspaceId={currentWorkspace.id}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Agents Grid */}
          {!isLoading && filteredAgents.length > 0 && (
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {filteredAgents.map((agent) => (
                <AgentCard
                  key={agent.id}
                  agent={agent}
                  onClick={() => handleAgentClick(agent.id)}
                  onRun={() => handleAgentRun(agent.id)}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
}