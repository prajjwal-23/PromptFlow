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
        <h3 className="text-lg font-semibold text-foreground mb-4">Agent Settings</h3>
        
        {/* Agent Information */}
        <div className="bg-background border border-border rounded-lg shadow-sm">
          <div className="px-6 py-4 border-b border-border">
            <h4 className="text-md font-medium text-foreground">Agent Information</h4>
            <p className="mt-1 text-sm text-muted-foreground">
              Basic information and metadata about this agent
            </p>
          </div>
          <div className="px-6 py-4 space-y-4">
            <div>
              <label className="block text-sm font-medium text-foreground">Agent ID</label>
              <div className="mt-1 flex items-center gap-2">
                <code className="px-2 py-1 bg-muted text-sm text-foreground rounded border">
                  {agent.id}
                </code>
                <button
                  onClick={() => navigator.clipboard.writeText(agent.id)}
                  className="text-muted-foreground hover:text-foreground transition-colors"
                  title="Copy to clipboard"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                </button>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-foreground">Version</label>
              <p className="mt-1 text-sm text-foreground">{agent.version}</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-foreground">Status</label>
              <div className="mt-1">
                <span
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    agent.is_active
                      ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                      : 'bg-muted text-muted-foreground'
                  }`}
                >
                  {agent.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-foreground">Created By</label>
              <p className="mt-1 text-sm text-foreground">{agent.created_by}</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-foreground">Created Date</label>
              <p className="mt-1 text-sm text-foreground">
                {formatDate(agent.created_at)}
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-foreground">Last Updated</label>
              <p className="mt-1 text-sm text-foreground">
                {formatDate(agent.updated_at)}
              </p>
            </div>
          </div>
        </div>

        {/* Workflow Statistics */}
        <div className="bg-background border border-border rounded-lg mt-6 shadow-sm">
          <div className="px-6 py-4 border-b border-border">
            <h4 className="text-md font-medium text-foreground">Workflow Statistics</h4>
            <p className="mt-1 text-sm text-muted-foreground">
              Information about the agent's workflow structure
            </p>
          </div>
          <div className="px-6 py-4 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-muted/50 rounded-lg p-4 border">
                <div className="flex items-center">
                  <svg className="w-8 h-8 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-foreground">{getNodeCount()}</p>
                    <p className="text-sm text-muted-foreground">Nodes</p>
                  </div>
                </div>
              </div>
              
              <div className="bg-muted/50 rounded-lg p-4 border">
                <div className="flex items-center">
                  <svg className="w-8 h-8 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-foreground">{getConnectionCount()}</p>
                    <p className="text-sm text-muted-foreground">Connections</p>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="border-t border-border pt-4">
              <h5 className="text-sm font-medium text-foreground mb-2">Workflow Complexity</h5>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Complexity Score</span>
                  <span className="text-sm font-medium text-foreground">
                    {getNodeCount() + getConnectionCount()} points
                  </span>
                </div>
                <div className="w-full bg-muted rounded-full h-2">
                  <div 
                    className="bg-primary h-2 rounded-full" 
                    style={{ width: `${Math.min((getNodeCount() + getConnectionCount()) * 5, 100)}%` }}
                  ></div>
                </div>
                <p className="text-xs text-muted-foreground">
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
        <div className="bg-background border border-border rounded-lg mt-6 shadow-sm">
          <div className="px-6 py-4 border-b border-border">
            <h4 className="text-md font-medium text-foreground">API Access</h4>
            <p className="mt-1 text-sm text-muted-foreground">
              Information for programmatic access to this agent
            </p>
          </div>
          <div className="px-6 py-4 space-y-4">
            <div>
              <label className="block text-sm font-medium text-foreground">API Endpoint</label>
              <div className="mt-1 flex items-center gap-2">
                <code className="px-2 py-1 bg-muted text-sm text-foreground rounded border flex-1">
                  POST /api/v1/agents/{agent.id}/run
                </code>
                <button
                  onClick={() => navigator.clipboard.writeText(`POST /api/v1/agents/${agent.id}/run`)}
                  className="text-muted-foreground hover:text-foreground transition-colors"
                  title="Copy to clipboard"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                </button>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-foreground">Authentication</label>
              <p className="mt-1 text-sm text-foreground">
                Bearer token required (use your account access token)
              </p>
            </div>
          </div>
        </div>

        {/* Danger Zone */}
        {canDelete && (
          <div className="bg-background border border-border rounded-lg mt-6 border-red-200/50 dark:border-red-900/50 shadow-sm">
            <div className="px-6 py-4 border-b border-red-200/50 dark:border-red-900/50 bg-red-50/50 dark:bg-red-950/20">
              <h4 className="text-md font-medium text-red-900 dark:text-red-400">Danger Zone</h4>
              <p className="mt-1 text-sm text-red-700 dark:text-red-300">
                Irreversible actions that affect this agent
              </p>
            </div>
            <div className="px-6 py-4">
              <div className="flex items-center justify-between">
                <div>
                  <h5 className="text-sm font-medium text-foreground">Delete Agent</h5>
                  <p className="text-sm text-muted-foreground">
                    Once you delete an agent, there is no going back. Please be certain.
                  </p>
                </div>
                <button
                  onClick={() => setShowDeleteConfirm(true)}
                  className="px-4 py-2 border border-red-300 shadow-sm text-sm font-medium rounded-md text-red-700 bg-background hover:bg-red-50 dark:hover:bg-red-950/20 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors"
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
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-background border border-border rounded-lg p-6 max-w-md w-full mx-4 shadow-lg">
            <div className="flex items-center mb-4">
              <div className="flex-shrink-0">
                <svg className="h-6 w-6 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-lg font-medium text-foreground">Delete Agent</h3>
                <p className="text-sm text-muted-foreground">
                  This action cannot be undone. This will permanently delete the agent "{agent.name}" and all its workflow data.
                </p>
              </div>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-foreground mb-2">
                Type the agent name to confirm
              </label>
              <input
                type="text"
                value={deleteConfirmText}
                onChange={(e) => setDeleteConfirmText(e.target.value)}
                placeholder={agent.name}
                className="block w-full px-3 py-2 border border-input bg-background rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 sm:text-sm transition-colors"
              />
            </div>

            <div className="flex gap-3 justify-end">
              <button
                onClick={() => {
                  setShowDeleteConfirm(false);
                  setDeleteConfirmText('');
                }}
                className="px-4 py-2 border border-input bg-background shadow-sm text-sm font-medium rounded-md text-foreground hover:bg-muted focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={deleteConfirmText !== agent.name}
                className="px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
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