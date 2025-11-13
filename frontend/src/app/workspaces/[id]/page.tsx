/**
 * Workspace Detail Page
 * 
 * This page displays workspace details, members, and settings.
 */
'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useAuthStore } from '../../../store/authStore';
import { useWorkspaceStore } from '../../../store/workspaceStore';
import { ProtectedRoute } from '../../../components/ProtectedRoute';
import { WorkspaceCard } from '../../../components/Workspace/WorkspaceCard';
import { WorkspaceForm } from '../../../components/Workspace/WorkspaceForm';
import { WorkspaceMembers } from '../../../components/Workspace/WorkspaceMembers';
import { WorkspaceSettings } from '../../../components/Workspace/WorkspaceSettings';

export default function WorkspacePage() {
  const router = useRouter();
  const params = useParams();
  const workspaceId = params.id as string;
  
  const { user } = useAuthStore();
  const {
    currentWorkspace,
    workspaceMembers,
    isLoading,
    isUpdating,
    error,
    fetchWorkspace,
    fetchWorkspaceMembers,
    updateWorkspace,
    deleteWorkspace,
    clearError,
  } = useWorkspaceStore();

  const [activeTab, setActiveTab] = useState<'overview' | 'members' | 'settings'>('overview');
  const [showEditForm, setShowEditForm] = useState(false);

  useEffect(() => {
    if (workspaceId) {
      fetchWorkspace(workspaceId);
      fetchWorkspaceMembers(workspaceId);
    }
  }, [workspaceId, fetchWorkspace, fetchWorkspaceMembers]);

  const handleUpdateWorkspace = async (data: { name: string; description?: string }) => {
    if (!workspaceId) return;
    
    try {
      await updateWorkspace(workspaceId, data);
      setShowEditForm(false);
    } catch (error) {
      console.error('Failed to update workspace:', error);
    }
  };

  const handleDeleteWorkspace = async () => {
    if (!workspaceId) return;
    
    if (window.confirm('Are you sure you want to delete this workspace? This action cannot be undone.')) {
      try {
        await deleteWorkspace(workspaceId);
        router.push('/workspaces');
      } catch (error) {
        console.error('Failed to delete workspace:', error);
      }
    }
  };

  const canManageWorkspace = currentWorkspace && (
    currentWorkspace.role === 'owner' || currentWorkspace.role === 'admin'
  );

  const canDeleteWorkspace = currentWorkspace && currentWorkspace.role === 'owner';

  if (isLoading && !currentWorkspace) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </ProtectedRoute>
    );
  }

  if (!currentWorkspace) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Workspace not found</h1>
            <p className="text-gray-600 mb-4">The workspace you're looking for doesn't exist or you don't have access to it.</p>
            <button
              onClick={() => router.push('/workspaces')}
              className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/90"
            >
              Back to Workspaces
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
                  <h1 className="text-3xl font-bold text-gray-900">{currentWorkspace.name}</h1>
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      currentWorkspace.role === 'owner'
                        ? 'bg-purple-100 text-purple-800'
                        : currentWorkspace.role === 'admin'
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {currentWorkspace.role}
                  </span>
                </div>
                {currentWorkspace.description && (
                  <p className="text-gray-600">{currentWorkspace.description}</p>
                )}
              </div>
              
              {canManageWorkspace && (
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setShowEditForm(true)}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                    Edit Workspace
                  </button>
                  
                  {canDeleteWorkspace && (
                    <button
                      onClick={handleDeleteWorkspace}
                      className="inline-flex items-center px-4 py-2 border border-red-300 text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                    >
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                      Delete
                    </button>
                  )}
                </div>
              )}
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
                  <h2 className="text-lg font-medium text-gray-900">Edit Workspace</h2>
                  <p className="mt-1 text-sm text-gray-500">Update workspace information</p>
                </div>
                <div className="px-6 py-6">
                  <WorkspaceForm
                    workspace={{
                      name: currentWorkspace.name,
                      description: currentWorkspace.description,
                    }}
                    onSubmit={handleUpdateWorkspace}
                    onCancel={() => setShowEditForm(false)}
                    isSubmitting={isUpdating}
                    submitButtonText="Update Workspace"
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
                  onClick={() => setActiveTab('members')}
                  className={`py-4 px-6 text-sm font-medium border-b-2 ${
                    activeTab === 'members'
                      ? 'border-primary text-primary'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Members ({workspaceMembers.length})
                </button>
                {canManageWorkspace && (
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
                    <h3 className="text-lg font-medium text-gray-900 mb-4">Workspace Overview</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="bg-gray-50 rounded-lg p-4">
                        <h4 className="text-sm font-medium text-gray-500 mb-2">Workspace Details</h4>
                        <dl className="space-y-2">
                          <div>
                            <dt className="text-sm text-gray-600">Created</dt>
                            <dd className="text-sm font-medium text-gray-900">
                              {new Date(currentWorkspace.created_at).toLocaleDateString('en-US', {
                                year: 'numeric',
                                month: 'long',
                                day: 'numeric',
                              })}
                            </dd>
                          </div>
                          <div>
                            <dt className="text-sm text-gray-600">Last Updated</dt>
                            <dd className="text-sm font-medium text-gray-900">
                              {new Date(currentWorkspace.updated_at).toLocaleDateString('en-US', {
                                year: 'numeric',
                                month: 'long',
                                day: 'numeric',
                              })}
                            </dd>
                          </div>
                          <div>
                            <dt className="text-sm text-gray-600">Members</dt>
                            <dd className="text-sm font-medium text-gray-900">
                              {currentWorkspace.member_count} member{currentWorkspace.member_count !== 1 ? 's' : ''}
                            </dd>
                          </div>
                        </dl>
                      </div>
                      
                      <div className="bg-gray-50 rounded-lg p-4">
                        <h4 className="text-sm font-medium text-gray-500 mb-2">Your Role</h4>
                        <div className="flex items-center gap-2">
                          <span
                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              currentWorkspace.role === 'owner'
                                ? 'bg-purple-100 text-purple-800'
                                : currentWorkspace.role === 'admin'
                                ? 'bg-blue-100 text-blue-800'
                                : 'bg-gray-100 text-gray-800'
                            }`}
                          >
                            {currentWorkspace.role}
                          </span>
                          <span className="text-sm text-gray-600">
                            {currentWorkspace.role === 'owner' && 'You can manage all aspects of this workspace'}
                            {currentWorkspace.role === 'admin' && 'You can manage members and settings'}
                            {currentWorkspace.role === 'member' && 'You can view and create agents'}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'members' && (
                <WorkspaceMembers
                  workspace={currentWorkspace}
                  members={workspaceMembers}
                  canManageMembers={canManageWorkspace || false}
                />
              )}

              {activeTab === 'settings' && canManageWorkspace && (
                <WorkspaceSettings
                  workspace={currentWorkspace}
                  canDelete={canDeleteWorkspace || false}
                  onDelete={handleDeleteWorkspace}
                />
              )}
            </div>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}