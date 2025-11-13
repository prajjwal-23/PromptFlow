/**
 * Agent Detail/Edit Page
 * 
 * This page displays agent details and provides editing capabilities.
 */
'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useAuthStore } from '../../store/authStore';
import { useWorkspaceStore } from '../../store/workspaceStore';
import { useAgentStore, getAgentStatus, getAgentStatusColor } from '../../store/agentStore';
import { ProtectedRoute } from '../../components/ProtectedRoute';
import { AgentForm } from '../../components/Agent/AgentForm';
import { AgentSettings } from '../../components/Agent/AgentSettings';

export default function AgentPage() {
  const router = useRouter();
  const params = useParams();
  const agentId = params.id as string;
  
  const { user } = useAuthStore();
  const { currentWorkspace } = useWorkspaceStore();
  const {
    currentAgent,
    isLoading,
    isUpdating,
    isDeleting,
    error,
    fetchAgent,
    updateAgent,
    deleteAgent,
    clearError,
  } = useAgentStore();

  const [activeTab, setActiveTab] = useState<'overview' | 'edit' | 'settings'>('overview');
  const [showEditForm, setShowEditForm] = useState(false);

  useEffect(() => {
    if (agentId) {
      fetchAgent(agentId);
    }
  }, [agentId, fetchAgent]);

  const handleUpdateAgent = async (data: { name: string; description?: string }) => {
    if (!agentId) return;
    
    try {
      await updateAgent(agentId, data);
      setShowEditForm(false);
    } catch (error) {
      console.error('Failed to update agent:', error);
    }
  };

  const handleDeleteAgent = async () => {
    if (!agentId) return;
    
    if (window.confirm('Are you sure you want to delete this agent? This action cannot be undone.')) {
      try {
        await deleteAgent(agentId);
        if (currentWorkspace) {
          router.push(`/workspaces/${currentWorkspace.id}/agents`);
        } else {
          router.push('/agents');
        }
      } catch (error) {
        console.error('Failed to delete agent:', error);
      }
    }
  };

  const handleEditAgent = () => {
    router.push(`/agents/${agentId}/edit`);
  };

  const handleRunAgent = () => {
    router.push(`/agents/${agentId}/run`);
  };

  if (isLoading && !currentAgent) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </ProtectedRoute>
    );
  }

  if (!currentAgent) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Agent not found</h1>
            <p className="text-gray-600 mb-4">The agent you're looking for doesn't exist or you don't have access to it.</p>
            <button
              onClick={() => router.push('/agents')}
              className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/90"
            >
              Back to Agents
            </button>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  const agentStatus = getAgentStatus(currentAgent);
  const canEditAgent = !!currentWorkspace && (
    currentWorkspace.role === 'owner' || currentWorkspace.role === 'admin'
  );
  const canDeleteAgent = canEditAgent && (
    currentWorkspace?.role === 'owner' || currentAgent.created_by === user?.id
  );

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
                    onClick={() => {
                      if (currentWorkspace) {
                        router.push(`/workspaces/${currentWorkspace.id}/agents`);
                      } else {
                        router.push('/agents');
                      }
                    }}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                  </button>
                  <h1 className="text-3xl font-bold text-gray-900">{currentAgent.name}</h1>
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getAgentStatusColor(
                      agentStatus
                    )}`}
                  >
                    {agentStatus}
                  </span>
                </div>
                {currentAgent.description && (
                  <p className="text-gray-600">{currentAgent.description}</p>
                )}
              </div>
              
              <div className="flex items-center gap-2">
                <button
                  onClick={handleRunAgent}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Run Agent
                </button>
                
                <button
                  onClick={handleEditAgent}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  Edit Workflow
                </button>
                
                {canEditAgent && (
                  <button
                    onClick={() => setShowEditForm(true)}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                    Edit Details
                  </button>
                )}
                
                {canDeleteAgent && (
                  <button
                    onClick={handleDeleteAgent}
                    className="inline-flex items-center px-4 py-2 border border-red-300 text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                    Delete
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-6 rounded-md bg-red-50 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
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
                      <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Edit Form */}
          {showEditForm && (
            <div className="mb-8">
              <div className="bg-white shadow rounded-lg">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h2 className="text-lg font-medium text-gray-900">Edit Agent</h2>
                  <p className="mt-1 text-sm text-gray-500">Update agent information</p>
                </div>
                <div className="px-6 py-6">
                  <AgentForm
                    agent={{
                      name: currentAgent.name,
                      description: currentAgent.description,
                    }}
                    onSubmit={handleUpdateAgent}
                    onCancel={() => setShowEditForm(false)}
                    isSubmitting={isUpdating}
                    submitButtonText="Update Agent"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Tabs */}
          <div className="bg-white shadow rounded-lg">
            <div className="border-b border-gray-200">
              <nav className="flex -mb-px">
                <button
                  onClick={() => setActiveTab('overview')}
                  className={`py-4 px-6 text-sm font-medium border-b-2 ${
                    activeTab === 'overview'
                      ? 'border-primary text-primary'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Overview
                </button>
                <button
                  onClick={() => setActiveTab('edit')}
                  className={`py-4 px-6 text-sm font-medium border-b-2 ${
                    activeTab === 'edit'
                      ? 'border-primary text-primary'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Workflow
                </button>
                {canEditAgent && (
                  <button
                    onClick={() => setActiveTab('settings')}
                    className={`py-4 px-6 text-sm font-medium border-b-2 ${
                      activeTab === 'settings'
                        ? 'border-primary text-primary'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    Settings
                  </button>
                )}
              </nav>
            </div>

            <div className="p-6">
              {activeTab === 'overview' && (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-4">Agent Overview</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="bg-gray-50 rounded-lg p-4">
                        <h4 className="text-sm font-medium text-gray-500 mb-2">Agent Details</h4>
                        <dl className="space-y-2">
                          <div>
                            <dt className="text-sm text-gray-600">Status</dt>
                            <dd className="text-sm font-medium text-gray-900">
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getAgentStatusColor(agentStatus)}`}>
                                {agentStatus}
                              </span>
                            </dd>
                          </div>
                          <div>
                            <dt className="text-sm text-gray-600">Version</dt>
                            <dd className="text-sm font-medium text-gray-900">{currentAgent.version}</dd>
                          </div>
                          <div>
                            <dt className="text-sm text-gray-600">Created</dt>
                            <dd className="text-sm font-medium text-gray-900">
                              {new Date(currentAgent.created_at).toLocaleDateString('en-US', {
                                year: 'numeric',
                                month: 'long',
                                day: 'numeric',
                              })}
                            </dd>
                          </div>
                          <div>
                            <dt className="text-sm text-gray-600">Last Updated</dt>
                            <dd className="text-sm font-medium text-gray-900">
                              {new Date(currentAgent.updated_at).toLocaleDateString('en-US', {
                                year: 'numeric',
                                month: 'long',
                                day: 'numeric',
                              })}
                            </dd>
                          </div>
                        </dl>
                      </div>
                      
                      <div className="bg-gray-50 rounded-lg p-4">
                        <h4 className="text-sm font-medium text-gray-500 mb-2">Workflow Information</h4>
                        <dl className="space-y-2">
                          <div>
                            <dt className="text-sm text-gray-600">Nodes</dt>
                            <dd className="text-sm font-medium text-gray-900">
                              {currentAgent.graph_json?.nodes?.length || 0} nodes
                            </dd>
                          </div>
                          <div>
                            <dt className="text-sm text-gray-600">Connections</dt>
                            <dd className="text-sm font-medium text-gray-900">
                              {currentAgent.graph_json?.edges?.length || 0} connections
                            </dd>
                          </div>
                          <div>
                            <dt className="text-sm text-gray-600">Workspace</dt>
                            <dd className="text-sm font-medium text-gray-900">
                              {currentWorkspace?.name || 'Unknown'}
                            </dd>
                          </div>
                          <div>
                            <dt className="text-sm text-gray-600">Created By</dt>
                            <dd className="text-sm font-medium text-gray-900">
                              {currentAgent.created_by}
                            </dd>
                          </div>
                        </dl>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'edit' && (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-4">Visual Workflow Editor</h3>
                    <div className="bg-gray-50 rounded-lg p-8 text-center">
                      <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                      <h3 className="mt-2 text-sm font-medium text-gray-900">Visual Editor Coming Soon</h3>
                      <p className="mt-1 text-sm text-gray-500">
                        The visual workflow editor will be available in the next phase of development.
                      </p>
                      <div className="mt-6">
                        <button
                          onClick={handleEditAgent}
                          className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
                        >
                          Open Editor
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'settings' && canEditAgent && (
                <AgentSettings
                  agent={currentAgent}
                  canDelete={canDeleteAgent}
                  onDelete={handleDeleteAgent}
                />
              )}
            </div>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}