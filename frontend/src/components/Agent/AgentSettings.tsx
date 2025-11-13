/**
 * Agent Settings Component
 * 
 * This component displays agent settings and management options.
 */

import { useState } from 'react';
import { Agent } from '../../store/agentStore';

interface AgentSettingsProps {
  agent: Agent;
  canDelete: boolean;
  onDelete: () => void;
}

export function AgentSettings({ agent, canDelete, onDelete }: AgentSettingsProps) {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');

  const handleDelete = () => {
    if (deleteConfirmText === agent.name) {
      onDelete();
      setShowDeleteConfirm(false);
      setDeleteConfirmText('');
    }
  };

  const getNodeCount = () => {
    return agent.graph_json?.nodes?.length || 0;
  };

  const getConnectionCount = () => {
    return agent.graph_json?.edges?.length || 0;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Agent Settings</h3>
        
        {/* Agent Information */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h4 className="text-md font-medium text-gray-900">Agent Information</h4>
            <p className="mt-1 text-sm text-gray-500">
              Basic information and metadata about this agent
            </p>
          </div>
          <div className="px-6 py-4 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Agent ID</label>
              <div className="mt-1 flex items-center gap-2">
                <code className="px-2 py-1 bg-gray-100 text-sm text-gray-800 rounded">
                  {agent.id}
                </code>
                <button
                  onClick={() => navigator.clipboard.writeText(agent.id)}
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
              <label className="block text-sm font-medium text-gray-700">Version</label>
              <p className="mt-1 text-sm text-gray-900">{agent.version}</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Status</label>
              <div className="mt-1">
                <span
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    agent.is_active
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {agent.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Created By</label>
              <p className="mt-1 text-sm text-gray-900">{agent.created_by}</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Created Date</label>
              <p className="mt-1 text-sm text-gray-900">
                {formatDate(agent.created_at)}
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Last Updated</label>
              <p className="mt-1 text-sm text-gray-900">
                {formatDate(agent.updated_at)}
              </p>
            </div>
          </div>
        </div>

        {/* Workflow Statistics */}
        <div className="bg-white shadow rounded-lg mt-6">
          <div className="px-6 py-4 border-b border-gray-200">
            <h4 className="text-md font-medium text-gray-900">Workflow Statistics</h4>
            <p className="mt-1 text-sm text-gray-500">
              Information about the agent's workflow structure
            </p>
          </div>
          <div className="px-6 py-4 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center">
                  <svg className="w-8 h-8 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-900">{getNodeCount()}</p>
                    <p className="text-sm text-gray-500">Nodes</p>
                  </div>
                </div>
              </div>
              
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center">
                  <svg className="w-8 h-8 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-900">{getConnectionCount()}</p>
                    <p className="text-sm text-gray-500">Connections</p>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="border-t pt-4">
              <h5 className="text-sm font-medium text-gray-900 mb-2">Workflow Complexity</h5>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Complexity Score</span>
                  <span className="text-sm font-medium text-gray-900">
                    {getNodeCount() + getConnectionCount()} points
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-primary h-2 rounded-full" 
                    style={{ width: `${Math.min((getNodeCount() + getConnectionCount()) * 5, 100)}%` }}
                  ></div>
                </div>
                <p className="text-xs text-gray-500">
                  {getNodeCount() + getConnectionCount() < 5 
                    ? 'Simple workflow' 
                    : getNodeCount() + getConnectionCount() < 15 
                    ? 'Moderate complexity' 
                    : 'Complex workflow'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* API Access */}
        <div className="bg-white shadow rounded-lg mt-6">
          <div className="px-6 py-4 border-b border-gray-200">
            <h4 className="text-md font-medium text-gray-900">API Access</h4>
            <p className="mt-1 text-sm text-gray-500">
              Information for programmatic access to this agent
            </p>
          </div>
          <div className="px-6 py-4 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">API Endpoint</label>
              <div className="mt-1 flex items-center gap-2">
                <code className="px-2 py-1 bg-gray-100 text-sm text-gray-800 rounded flex-1">
                  POST /api/v1/agents/{agent.id}/run
                </code>
                <button
                  onClick={() => navigator.clipboard.writeText(`POST /api/v1/agents/${agent.id}/run`)}
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
              <label className="block text-sm font-medium text-gray-700">Authentication</label>
              <p className="mt-1 text-sm text-gray-900">
                Bearer token required (use your account access token)
              </p>
            </div>
          </div>
        </div>

        {/* Danger Zone */}
        {canDelete && (
          <div className="bg-white shadow rounded-lg mt-6 border border-red-200">
            <div className="px-6 py-4 border-b border-red-200 bg-red-50">
              <h4 className="text-md font-medium text-red-900">Danger Zone</h4>
              <p className="mt-1 text-sm text-red-700">
                Irreversible actions that affect this agent
              </p>
            </div>
            <div className="px-6 py-4">
              <div className="flex items-center justify-between">
                <div>
                  <h5 className="text-sm font-medium text-gray-900">Delete Agent</h5>
                  <p className="text-sm text-gray-500">
                    Once you delete an agent, there is no going back. Please be certain.
                  </p>
                </div>
                <button
                  onClick={() => setShowDeleteConfirm(true)}
                  className="px-4 py-2 border border-red-300 shadow-sm text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                >
                  Delete Agent
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
                <h3 className="text-lg font-medium text-gray-900">Delete Agent</h3>
                <p className="text-sm text-gray-500">
                  This action cannot be undone. This will permanently delete the agent "{agent.name}" and all its workflow data.
                </p>
              </div>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Type the agent name to confirm
              </label>
              <input
                type="text"
                value={deleteConfirmText}
                onChange={(e) => setDeleteConfirmText(e.target.value)}
                placeholder={agent.name}
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
                disabled={deleteConfirmText !== agent.name}
                className="px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Delete Agent
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}