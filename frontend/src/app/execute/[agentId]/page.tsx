/**
 * Agent execution page - provides interface for executing agents with real-time monitoring.
 */

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useExecutionStore } from '../../../store/executionStore';
import { useAuthStore } from '../../../store/authStore';
import { useAgentStore } from '../../../store/agentStore';
import { RunPanel, EventStream, NodeExecution } from '../../../components/Execution';
import { 
  ArrowLeftIcon,
  PlayIcon,
  ChartBarIcon,
  CogIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import Link from 'next/link';

export default function AgentExecutePage() {
  const params = useParams();
  const router = useRouter();
  const agentId = params.agentId as string;
  
  const { user } = useAuthStore();
  const {
    currentExecution,
    events,
    isRunning,
    isLoading,
    error,
    startExecution,
    clearError
  } = useExecutionStore();

  const { agents, fetchAgents } = useAgentStore();
  const [activeTab, setActiveTab] = useState<'control' | 'events' | 'nodes'>('control');
  const [inputData, setInputData] = useState<Record<string, any>>({});
  const [agent, setAgent] = useState<any>(null);

  // Fetch agent data on component mount
  useEffect(() => {
    if (agentId && user) {
      loadAgentData();
    }
  }, [agentId, user]);

  const loadAgentData = async () => {
    try {
      await fetchAgents();
      const foundAgent = agents.find(a => a.id === agentId);
      if (foundAgent) {
        setAgent(foundAgent);
        // Set default input data based on agent graph
        if (foundAgent.graph_json?.nodes) {
          const defaultInputs: Record<string, any> = {};
          foundAgent.graph_json.nodes
            .filter((node: any) => node.type === 'input')
            .forEach((node: any) => {
              defaultInputs[node.id] = node.data?.default_value || '';
            });
          setInputData(defaultInputs);
        }
      }
    } catch (error) {
      console.error('Failed to load agent data:', error);
    }
  };

  const handleStartExecution = async () => {
    if (!agentId) return;

    try {
      clearError();
      await startExecution(agentId, inputData);
      setActiveTab('events'); // Switch to events tab when execution starts
    } catch (error) {
      console.error('Failed to start execution:', error);
    }
  };

  const handleInputChange = (key: string, value: any) => {
    setInputData(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const addInputField = () => {
    const key = `input_${Object.keys(inputData).length + 1}`;
    setInputData(prev => ({
      ...prev,
      [key]: ''
    }));
  };

  const removeInputField = (key: string) => {
    const newInputData = { ...inputData };
    delete newInputData[key];
    setInputData(newInputData);
  };

  const tabs = [
    { id: 'control', name: 'Control', icon: PlayIcon },
    { id: 'events', name: 'Events', icon: DocumentTextIcon },
    { id: 'nodes', name: 'Nodes', icon: CogIcon }
  ];

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Authentication Required</h1>
          <p className="text-gray-600">Please log in to execute agents.</p>
        </div>
      </div>
    );
  }

  if (isLoading && !agent) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <div className="text-lg font-medium text-gray-900">Loading agent...</div>
        </div>
      </div>
    );
  }

  if (!agent && !isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Agent Not Found</h1>
          <p className="text-gray-600 mb-4">The agent you're looking for doesn't exist or you don't have access to it.</p>
          <Link
            href="/agents"
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Back to Agents
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <Link
                href="/agents"
                className="text-gray-600 hover:text-gray-900"
              >
                <ArrowLeftIcon className="h-5 w-5" />
              </Link>
              <div>
                <h1 className="text-xl font-semibold text-gray-900">Execute Agent</h1>
                <p className="text-sm text-gray-500">
                  {agent?.name || agentId}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              {currentExecution && (
                <Link
                  href={`/runs/${currentExecution.id}`}
                  className="text-indigo-600 hover:text-indigo-900 text-sm"
                >
                  View Execution
                </Link>
              )}
              <Link
                href={`/agents/${agentId}/edit`}
                className="text-gray-600 hover:text-gray-900 text-sm"
              >
                Edit Agent
              </Link>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
            <div className="flex">
              <div className="flex-shrink-0">
                <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-800">{error}</p>
              </div>
              <div className="ml-auto pl-3">
                <button
                  onClick={clearError}
                  className="text-red-400 hover:text-red-600"
                >
                  <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Agent Info */}
        {agent && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">Agent Name</h3>
                <p className="text-lg font-semibold text-gray-900">{agent.name}</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">Description</h3>
                <p className="text-gray-600">{agent.description || 'No description provided'}</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">Graph Complexity</h3>
                <p className="text-gray-600">
                  {agent.graph_json?.nodes?.length || 0} nodes, {agent.graph_json?.edges?.length || 0} edges
                </p>
              </div>
            </div>

            {agent.graph_json && (
              <div className="mt-6">
                <h4 className="text-sm font-medium text-gray-700 mb-3">Input Configuration</h4>
                <div className="space-y-3">
                  {Object.entries(inputData).map(([key, value]) => (
                    <div key={key} className="flex items-center space-x-3">
                      <input
                        type="text"
                        value={key}
                        onChange={(e) => {
                          const newKey = e.target.value;
                          if (newKey !== key) {
                            const newInputData = { ...inputData };
                            delete newInputData[key];
                            newInputData[newKey] = value;
                            setInputData(newInputData);
                          }
                        }}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                        placeholder="Field name"
                      />
                      <input
                        type="text"
                        value={value}
                        onChange={(e) => handleInputChange(key, e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                        placeholder="Field value"
                      />
                      <button
                        onClick={() => removeInputField(key)}
                        className="text-red-600 hover:text-red-800"
                      >
                        <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                        </svg>
                      </button>
                    </div>
                  ))}
                  
                  {Object.keys(inputData).length === 0 && (
                    <div className="text-center py-4 text-gray-500 text-sm">
                      No input fields configured. Click "Add Field" to get started.
                    </div>
                  )}
                  
                  <button
                    onClick={addInputField}
                    className="mt-3 text-indigo-600 hover:text-indigo-800 text-sm font-medium"
                  >
                    + Add Field
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Quick Start Button */}
        {!isRunning && !currentExecution && (
          <div className="bg-white rounded-lg shadow p-6 mb-6 text-center">
            <button
              onClick={handleStartExecution}
              className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
            >
              <PlayIcon className="h-5 w-5 mr-2" />
              Start Execution
            </button>
            <p className="mt-2 text-sm text-gray-500">
              Configure your input data above, then click to start execution
            </p>
          </div>
        )}

        {/* Run Panel */}
        {(isRunning || currentExecution) && (
          <div className="mb-6">
            <RunPanel
              agentId={agentId}
              className="w-full"
            />
          </div>
        )}

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`${
                      activeTab === tab.id
                        ? 'border-indigo-500 text-indigo-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    } group inline-flex items-center py-4 px-6 border-b-2 font-medium text-sm`}
                  >
                    <Icon
                      className={`${
                        activeTab === tab.id ? 'text-indigo-500' : 'text-gray-400 group-hover:text-gray-500'
                      } mr-2 h-5 w-5`}
                      aria-hidden="true"
                    />
                    {tab.name}
                  </button>
                );
              })}
            </nav>
          </div>

          <div className="p-6">
            {activeTab === 'control' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Execution Control</h3>
                  <RunPanel
                    agentId={agentId}
                    className="w-full"
                  />
                </div>
              </div>
            )}

            {activeTab === 'events' && (
              <EventStream
                executionId={currentExecution?.id}
                showFilters={true}
                maxHeight="600px"
              />
            )}

            {activeTab === 'nodes' && (
              <NodeExecution
                executionId={currentExecution?.id}
                showDetails={true}
                compact={false}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}