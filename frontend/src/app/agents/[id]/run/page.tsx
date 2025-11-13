/**
 * Agent Run Page
 * 
 * This page allows running an agent and viewing the results.
 */
'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useAuthStore } from '../../../../store/authStore';
import { useWorkspaceStore } from '../../../../store/workspaceStore';
import { useAgentStore } from '../../../../store/agentStore';
import { ProtectedRoute } from '../../../../components/ProtectedRoute';

export default function AgentRunPage() {
  const router = useRouter();
  const params = useParams();
  const agentId = params.id as string;
  
  const { user } = useAuthStore();
  const { currentWorkspace } = useWorkspaceStore();
  const {
    currentAgent,
    isLoading,
    error,
    fetchAgent,
    clearError,
  } = useAgentStore();

  const [isRunning, setIsRunning] = useState(false);
  const [runResult, setRunResult] = useState<any>(null);
  const [inputData, setInputData] = useState('');

  useEffect(() => {
    if (agentId) {
      fetchAgent(agentId);
    }
  }, [agentId, fetchAgent]);

  const handleRun = async () => {
    if (!agentId || !currentAgent) return;
    
    setIsRunning(true);
    setRunResult(null);
    clearError();
    
    try {
      // TODO: Implement actual agent running logic
      // For now, simulate a run
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      setRunResult({
        status: 'completed',
        output: 'Agent executed successfully',
        duration: '2.3s',
        tokens: 150,
      });
    } catch (error) {
      console.error('Failed to run agent:', error);
      setRunResult({
        status: 'failed',
        error: 'Failed to execute agent',
      });
    } finally {
      setIsRunning(false);
    }
  };

  const handleBack = () => {
    router.push(`/agents/${agentId}`);
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
              onClick={handleBack}
              className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/90"
            >
              Back to Agent
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
                    onClick={handleBack}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                  </button>
                  <h1 className="text-3xl font-bold text-gray-900">Run Agent</h1>
                  <span className="text-sm text-gray-500">
                    {currentAgent.name}
                  </span>
                </div>
                <p className="text-gray-600">
                  Execute your AI agent and view the results
                </p>
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

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Input Section */}
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-medium text-gray-900">Input</h2>
                <p className="mt-1 text-sm text-gray-500">Provide input data for the agent</p>
              </div>
              <div className="px-6 py-6">
                <div className="space-y-4">
                  <div>
                    <label htmlFor="input" className="block text-sm font-medium text-gray-700 mb-2">
                      Input Data
                    </label>
                    <textarea
                      id="input"
                      rows={6}
                      value={inputData}
                      onChange={(e) => setInputData(e.target.value)}
                      className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
                      placeholder="Enter your input data here..."
                    />
                  </div>
                  
                  <button
                    onClick={handleRun}
                    disabled={isRunning || !inputData.trim()}
                    className="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isRunning ? (
                      <>
                        <svg className="w-4 h-4 mr-2 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
                        Running...
                      </>
                    ) : (
                      <>
                        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        Run Agent
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* Output Section */}
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-medium text-gray-900">Output</h2>
                <p className="mt-1 text-sm text-gray-500">View the agent execution results</p>
              </div>
              <div className="px-6 py-6">
                {isRunning ? (
                  <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
                    <p className="mt-2 text-gray-600">Agent is running...</p>
                  </div>
                ) : runResult ? (
                  <div className="space-y-4">
                    <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      runResult.status === 'completed' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {runResult.status === 'completed' ? 'Completed' : 'Failed'}
                    </div>
                    
                    {runResult.status === 'completed' ? (
                      <div>
                        <div className="bg-gray-50 rounded-lg p-4">
                          <h3 className="text-sm font-medium text-gray-900 mb-2">Output</h3>
                          <p className="text-sm text-gray-700">{runResult.output}</p>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4 mt-4">
                          <div className="bg-gray-50 rounded-lg p-4">
                            <h3 className="text-sm font-medium text-gray-900 mb-1">Duration</h3>
                            <p className="text-sm text-gray-700">{runResult.duration}</p>
                          </div>
                          <div className="bg-gray-50 rounded-lg p-4">
                            <h3 className="text-sm font-medium text-gray-900 mb-1">Tokens Used</h3>
                            <p className="text-sm text-gray-700">{runResult.tokens}</p>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="bg-red-50 rounded-lg p-4">
                        <h3 className="text-sm font-medium text-red-900 mb-2">Error</h3>
                        <p className="text-sm text-red-700">{runResult.error}</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <svg className="w-12 h-12 mx-auto mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <p>Run the agent to see results here</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}