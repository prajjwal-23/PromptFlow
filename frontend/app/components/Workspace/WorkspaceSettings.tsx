/**
 * Workspace Settings Component
 * 
 * This component displays workspace settings and management options.
 */

import { useState } from 'react';
import { Workspace } from '../../store/workspaceStore';

interface WorkspaceSettingsProps {
  workspace: Workspace;
  canDelete: boolean;
  onDelete: () => void;
}

export function WorkspaceSettings({ workspace, canDelete, onDelete }: WorkspaceSettingsProps) {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');

  const handleDelete = () => {
    if (deleteConfirmText === workspace.name) {
      onDelete();
      setShowDeleteConfirm(false);
      setDeleteConfirmText('');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Workspace Settings</h3>
        
        {/* Workspace Information */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h4 className="text-md font-medium text-gray-900">Workspace Information</h4>
            <p className="mt-1 text-sm text-gray-500">
              Basic information about this workspace
            </p>
          </div>
          <div className="px-6 py-4 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Workspace ID</label>
              <div className="mt-1 flex items-center gap-2">
                <code className="px-2 py-1 bg-gray-100 text-sm text-gray-800 rounded">
                  {workspace.id}
                </code>
                <button
                  onClick={() => navigator.clipboard.writeText(workspace.id)}
                  className="text-gray-400 hover:text-gray-600"
                  title="Copy to clipboard"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                </button>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Created By</label>
              <p className="mt-1 text-sm text-gray-900">{workspace.created_by}</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Created Date</label>
              <p className="mt-1 text-sm text-gray-900">
                {new Date(workspace.created_at).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Last Updated</label>
              <p className="mt-1 text-sm text-gray-900">
                {new Date(workspace.updated_at).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </p>
            </div>
          </div>
        </div>

        {/* Access Control */}
        <div className="bg-white shadow rounded-lg mt-6">
          <div className="px-6 py-4 border-b border-gray-200">
            <h4 className="text-md font-medium text-gray-900">Access Control</h4>
            <p className="mt-1 text-sm text-gray-500">
              Manage access permissions and security settings
            </p>
          </div>
          <div className="px-6 py-4 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h5 className="text-sm font-medium text-gray-900">Your Role</h5>
                <p className="text-sm text-gray-500">
                  {workspace.role === 'owner' && 'You have full control over this workspace'}
                  {workspace.role === 'admin' && 'You can manage members and settings'}
                  {workspace.role === 'member' && 'You can view and create agents'}
                </p>
              </div>
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  workspace.role === 'owner'
                    ? 'bg-purple-100 text-purple-800'
                    : workspace.role === 'admin'
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                {workspace.role}
              </span>
            </div>
            
            <div className="border-t pt-4">
              <h5 className="text-sm font-medium text-gray-900 mb-2">Permission Summary</h5>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <svg className={`w-4 h-4 ${
                    workspace.role === 'owner' || workspace.role === 'admin' ? 'text-green-500' : 'text-gray-300'
                  }`} fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  <span className="text-sm text-gray-700">View workspace</span>
                </div>
                <div className="flex items-center gap-2">
                  <svg className={`w-4 h-4 ${
                    workspace.role === 'owner' || workspace.role === 'admin' ? 'text-green-500' : 'text-gray-300'
                  }`} fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  <span className="text-sm text-gray-700">Create and edit agents</span>
                </div>
                <div className="flex items-center gap-2">
                  <svg className={`w-4 h-4 ${
                    workspace.role === 'owner' || workspace.role === 'admin' ? 'text-green-500' : 'text-gray-300'
                  }`} fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  <span className="text-sm text-gray-700">Manage members</span>
                </div>
                <div className="flex items-center gap-2">
                  <svg className={`w-4 h-4 ${
                    workspace.role === 'owner' ? 'text-green-500' : 'text-gray-300'
                  }`} fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  <span className="text-sm text-gray-700">Delete workspace</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Danger Zone */}
        {canDelete && (
          <div className="bg-white shadow rounded-lg mt-6 border border-red-200">
            <div className="px-6 py-4 border-b border-red-200 bg-red-50">
              <h4 className="text-md font-medium text-red-900">Danger Zone</h4>
              <p className="mt-1 text-sm text-red-700">
                Irreversible actions that affect this workspace
              </p>
            </div>
            <div className="px-6 py-4">
              <div className="flex items-center justify-between">
                <div>
                  <h5 className="text-sm font-medium text-gray-900">Delete Workspace</h5>
                  <p className="text-sm text-gray-500">
                    Once you delete a workspace, there is no going back. Please be certain.
                  </p>
                </div>
                <button
                  onClick={() => setShowDeleteConfirm(true)}
                  className="px-4 py-2 border border-red-300 shadow-sm text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                >
                  Delete Workspace
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center mb-4">
              <div className="flex-shrink-0">
                <svg className="h-6 w-6 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-lg font-medium text-gray-900">Delete Workspace</h3>
                <p className="text-sm text-gray-500">
                  This action cannot be undone. This will permanently delete the workspace "{workspace.name}" and all its agents.
                </p>
              </div>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Type the workspace name to confirm
              </label>
              <input
                type="text"
                value={deleteConfirmText}
                onChange={(e) => setDeleteConfirmText(e.target.value)}
                placeholder={workspace.name}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-red-500 focus:border-red-500 sm:text-sm"
              />
            </div>

            <div className="flex gap-3 justify-end">
              <button
                onClick={() => {
                  setShowDeleteConfirm(false);
                  setDeleteConfirmText('');
                }}
                className="px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={deleteConfirmText !== workspace.name}
                className="px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Delete Workspace
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}