/**
 * Individual run detail page - shows comprehensive execution information.
 */

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useExecutionStore } from '../../../store/executionStore';
import { useAuthStore } from '../../../store/authStore';
import { RunPanel, EventStream, NodeExecution, ExecutionLog } from '../../../components/Execution';
import { 
  ArrowLeftIcon,
  ArrowPathIcon,
  DocumentTextIcon,
  ChartBarIcon,
  CogIcon
} from '@heroicons/react/24/outline';
import Link from 'next/link';

export default function RunDetailPage() {
  const params = useParams();
  const router = useRouter();
  const runId = params.runId as string;
  
  const { user } = useAuthStore();
  const {
    currentExecution,
    events,
    isLoading,
    error,
    fetchExecution,
    fetchExecutionEvents,
    clearError
  } = useExecutionStore();

  const [activeTab, setActiveTab] = useState<'overview' | 'events' | 'nodes' | 'logs'>('overview');
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Fetch execution data on component mount
  useEffect(() => {
    if (runId && user) {
      loadExecutionData();
    }
  }, [runId, user]);

  const loadExecutionData = async () => {
    try {
      setIsRefreshing(true);
      clearError();
      await Promise.all([
        fetchExecution(runId),
        fetchExecutionEvents(runId, 100)
      ]);
    } catch (error) {
      console.error('Failed to load execution data:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleRefresh = () => {
    loadExecutionData();
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'cancelled':
        return 'bg-yellow-100 text-yellow-800';
      case 'timeout':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDuration = (execution: any): string => {
    if (!execution.started_at) return '-';
    
    const startTime = new Date(execution.started_at);
    const endTime = execution.completed_at 
      ? new Date(execution.completed_at)
      : new Date();
    
    const duration = endTime.getTime() - startTime.getTime();
    
    if (duration < 1000) return `${duration}ms`;
    if (duration < 60000) return `${(duration / 1000).toFixed(1)}s`;
    return `${(duration / 60000).toFixed(1)}m`;
  };

  const tabs = [
    { id: 'overview', name: 'Overview', icon: ChartBarIcon },
    { id: 'events', name: 'Events', icon: DocumentTextIcon },
    { id: 'nodes', name: 'Nodes', icon: CogIcon },
    { id: 'logs', name: 'Logs', icon: DocumentTextIcon }
  ];

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Authentication Required</h1>
          <p className="text-gray-600">Please log in to view execution details.</p>
        </div>
      </div>
    );
  }

  if (isLoading && !currentExecution) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <div className="text-lg font-medium text-gray-900">Loading execution...</div>
        </div>
      </div>
    );
  }

  if (!currentExecution && !isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Execution Not Found</h1>
          <p className="text-gray-600 mb-4">The execution you're looking for doesn't exist or you don't have access to it.</p>
          <Link
            href="/runs"
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Back to Executions
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
                href="/runs"
                className="text-gray-600 hover:text-gray-900"
              >
                <ArrowLeftIcon className="h-5 w-5" />
              </Link>
              <div>
                <h1 className="text-xl font-semibold text-gray-900">Execution Details</h1>
                <p className="text-sm text-gray-500">
                  ID: {runId}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={handleRefresh}
                disabled={isRefreshing}
                className="p-2 text-gray-600 hover:text-gray-900 disabled:opacity-50"
              >
                <ArrowPathIcon className={`h-5 w-5 ${isRefreshing ? 'animate-spin' : ''}`} />
              </button>
              <Link
                href={`/execute/${currentExecution?.agent_id}`}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Run Again
              </Link>
            </div>
          </div>
        </div>
      </div>

      {currentExecution && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Error Display */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
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

          {/* Execution Summary */}
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">Status</h3>
                <div className={`px-3 py-1 inline-flex text-sm leading-5 font-semibold rounded-full ${getStatusColor(currentExecution.status)}`}>
                  {currentExecution.status}
                </div>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">Duration</h3>
                <p className="text-lg font-semibold text-gray-900">
                  {formatDuration(currentExecution)}
                </p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">Nodes</h3>
                <p className="text-lg font-semibold text-gray-900">
                  {currentExecution.metrics.completed_nodes}/{currentExecution.metrics.total_nodes}
                </p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">Tokens Used</h3>
                <p className="text-lg font-semibold text-gray-900">
                  {currentExecution.metrics.total_tokens_used.toLocaleString()}
                </p>
              </div>
            </div>

            <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">
              <div>
                <span className="font-medium text-gray-700">Agent ID:</span>
                <span className="ml-2 text-gray-600">{currentExecution.agent_id}</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Created:</span>
                <span className="ml-2 text-gray-600">
                  {new Date(currentExecution.created_at).toLocaleString()}
                </span>
              </div>
              {currentExecution.started_at && (
                <div>
                  <span className="font-medium text-gray-700">Started:</span>
                  <span className="ml-2 text-gray-600">
                    {new Date(currentExecution.started_at).toLocaleString()}
                  </span>
                </div>
              )}
              {currentExecution.completed_at && (
                <div>
                  <span className="font-medium text-gray-700">Completed:</span>
                  <span className="ml-2 text-gray-600">
                    {new Date(currentExecution.completed_at).toLocaleString()}
                  </span>
                </div>
              )}
              <div>
                <span className="font-medium text-gray-700">Success Rate:</span>
                <span className="ml-2 text-gray-600">
                  {currentExecution.metrics.success_rate.toFixed(1)}%
                </span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Failed Nodes:</span>
                <span className="ml-2 text-gray-600">
                  {currentExecution.metrics.failed_nodes}
                </span>
              </div>
            </div>

            {currentExecution.error_message && (
              <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-md">
                <h4 className="text-sm font-medium text-red-800 mb-2">Error Message</h4>
                <p className="text-sm text-red-600">{currentExecution.error_message}</p>
              </div>
            )}
          </div>

          {/* Run Panel */}
          <div className="mb-6">
            <RunPanel
              agentId={currentExecution.agent_id}
              className="w-full"
            />
          </div>

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
              {activeTab === 'overview' && (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-4">Execution Overview</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-3">Performance Metrics</h4>
                        <dl className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <dt className="text-gray-600">Total Execution Time:</dt>
                            <dd className="text-gray-900">{formatDuration(currentExecution)}</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-gray-600">Average Node Time:</dt>
                            <dd className="text-gray-900">
                              {currentExecution.metrics.average_execution_time.toFixed(2)}ms
                            </dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-gray-600">Peak Memory Usage:</dt>
                            <dd className="text-gray-900">
                              {(currentExecution.metrics.peak_memory_usage / 1024 / 1024).toFixed(2)}MB
                            </dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-gray-600">Peak CPU Usage:</dt>
                            <dd className="text-gray-900">
                              {currentExecution.metrics.peak_cpu_usage.toFixed(1)}%
                            </dd>
                          </div>
                        </dl>
                      </div>
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-3">Execution Statistics</h4>
                        <dl className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <dt className="text-gray-600">Total Nodes:</dt>
                            <dd className="text-gray-900">{currentExecution.metrics.total_nodes}</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-gray-600">Completed Nodes:</dt>
                            <dd className="text-gray-900">{currentExecution.metrics.completed_nodes}</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-gray-600">Failed Nodes:</dt>
                            <dd className="text-gray-900">{currentExecution.metrics.failed_nodes}</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-gray-600">Skipped Nodes:</dt>
                            <dd className="text-gray-900">{currentExecution.metrics.skipped_nodes}</dd>
                          </div>
                        </dl>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'events' && (
                <EventStream
                  executionId={runId}
                  showFilters={true}
                  maxHeight="600px"
                />
              )}

              {activeTab === 'nodes' && (
                <NodeExecution
                  executionId={runId}
                  showDetails={true}
                  compact={false}
                />
              )}

              {activeTab === 'logs' && (
                <ExecutionLog
                  agentId={currentExecution.agent_id}
                  showFilters={false}
                  maxEntries={100}
                />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}