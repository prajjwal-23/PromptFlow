/**
 * Agent Editor Page
 * 
 * This page provides the visual workflow editor for building and editing agents.
 */
'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useAuthStore } from '../../../store/authStore';
import { useWorkspaceStore } from '../../../store/workspaceStore';
import { useAgentStore } from '../../../store/agentStore';
import { useCanvasStore } from '../../../store/canvasStore';
import { ProtectedRoute } from '../../../components/ProtectedRoute';
import { AgentCanvas } from '../../../components/Canvas/AgentCanvas';

export default function AgentEditorPage() {
  const router = useRouter();
  const params = useParams();
  const agentId = params.id as string;
  
  const { user } = useAuthStore();
  const { currentWorkspace } = useWorkspaceStore();
  const {
    currentAgent,
    isLoading: agentLoading,
    error: agentError,
    fetchAgent,
    updateAgent,
  } = useAgentStore();
  
  const {
    nodes,
    edges,
    isLoading: canvasLoading,
    error: canvasError,
    loadGraph,
    saveGraph,
    clearError,
  } = useCanvasStore();

  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);

  useEffect(() => {
    if (agentId) {
      fetchAgent(agentId);
    }
  }, [agentId, fetchAgent]);

  useEffect(() => {
    // Load graph data when agent is fetched
    if (currentAgent && currentAgent.graph_json) {
      const graphData = currentAgent.graph_json as any;
      if (graphData.nodes && graphData.edges) {
        loadGraph({
          nodes: graphData.nodes,
          edges: graphData.edges,
        });
      }
    }
  }, [currentAgent, loadGraph]);

  const handleSave = async () => {
    if (!agentId || !currentAgent) return;
    
    setIsSaving(true);
    clearError();
    
    try {
      // Create graph data
      const graphData = {
        nodes,
        edges,
        metadata: {
          lastModified: new Date().toISOString(),
          version: '1.0',
        },
      };

      // Update agent with new graph data
      await updateAgent(agentId, {
        graph_json: graphData,
      });

      setLastSaved(new Date());
    } catch (error) {
      console.error('Failed to save agent:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleExport = () => {
    const graphData = {
      nodes,
      edges,
      metadata: {
        exportedAt: new Date().toISOString(),
        agentId,
        agentName: currentAgent?.name,
        version: '1.0',
      },
    };

    const dataStr = JSON.stringify(graphData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `${currentAgent?.name || 'agent'}-workflow-${Date.now()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleRun = () => {
    router.push(`/agents/${agentId}/run`);
  };

  const handleBack = () => {
    if (currentWorkspace) {
      router.push(`/workspaces/${currentWorkspace.id}/agents`);
    } else {
      router.push('/agents');
    }
  };

  if (agentLoading || !currentAgent) {
    return (
      <ProtectedRoute>
        <div className="h-screen flex items-center justify-center bg-gray-50">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading agent...</p>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  if (agentError) {
    return (
      <ProtectedRoute>
        <div className="h-screen flex items-center justify-center bg-gray-50">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Error</h1>
            <p className="text-gray-600 mb-4">{agentError}</p>
            <button
              onClick={handleBack}
              className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/90"
            >
              Go Back
            </button>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <div className="h-screen flex flex-col bg-gray-50">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={handleBack}
                className="p-2 text-gray-500 hover:text-gray-700 rounded-md"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              
              <div>
                <h1 className="text-lg font-medium text-gray-900">{currentAgent.name}</h1>
                <p className="text-sm text-gray-500">
                  {currentWorkspace?.name} • Agent Editor
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              {/* Save Status */}
              {lastSaved && (
                <div className="text-sm text-gray-500">
                  Saved {lastSaved.toLocaleTimeString()}
                </div>
              )}

              {/* Action Buttons */}
              <button
                onClick={handleExport}
                className="px-3 py-1.5 text-sm border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
              >
                Export
              </button>
              
              <button
                onClick={handleRun}
                className="px-3 py-1.5 text-sm bg-green-600 text-white rounded-md hover:bg-green-700"
              >
                Run Agent
              </button>
              
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="px-3 py-1.5 text-sm bg-primary text-white rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-1"
              >
                {isSaving ? (
                  <>
                    <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
                    <span>Saving...</span>
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V2"
                      />
                    </svg>
                    <span>Save</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Error Display */}
        {(agentError || canvasError) && (
          <div className="bg-red-50 border-b border-red-200 px-4 py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <svg className="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
                <span className="text-sm text-red-800">
                  {agentError || canvasError}
                </span>
              </div>
              <button
                onClick={clearError}
                className="text-red-500 hover:text-red-700"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            </div>
          </div>
        )}

        {/* Canvas */}
        <div className="flex-1">
          {canvasLoading ? (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
                <p className="mt-2 text-gray-600">Loading canvas...</p>
              </div>
            </div>
          ) : (
            <AgentCanvas agentId={agentId} />
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
}