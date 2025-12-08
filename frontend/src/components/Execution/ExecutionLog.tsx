/**
 * ExecutionLog component for execution history and log viewing.
 *
 * This component displays execution history, logs, and provides filtering
 * and search capabilities for past executions.
 */

'use client';

import React, { useState, useEffect } from 'react';
import { useExecutionStore } from '../../store/executionStore';
import { 
  MagnifyingGlassIcon,
  FunnelIcon,
  CalendarIcon,
  ClockIcon,
  DocumentTextIcon,
  ChevronDownIcon,
  ChevronRightIcon
} from '@heroicons/react/24/outline';

interface ExecutionLogProps {
  agentId?: string;
  showFilters?: boolean;
  maxEntries?: number;
  className?: string;
}

interface LogEntry {
  id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'debug';
  message: string;
  source: string;
  details?: any;
}

export const ExecutionLog: React.FC<ExecutionLogProps> = ({
  agentId,
  showFilters = true,
  maxEntries = 50,
  className = ''
}) => {
  const {
    executions,
    currentExecution,
    events,
    fetchExecutions,
    fetchExecutionEvents
  } = useExecutionStore();

  const [filteredExecutions, setFilteredExecutions] = useState(executions);
  const [selectedExecution, setSelectedExecution] = useState<string | null>(null);
  const [logEntries, setLogEntries] = useState<LogEntry[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [dateFilter, setDateFilter] = useState<string>('all');
  const [expandedLogs, setExpandedLogs] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(false);

  // Fetch executions on component mount
  useEffect(() => {
    const loadExecutions = async () => {
      setIsLoading(true);
      try {
        await fetchExecutions(agentId, undefined, maxEntries);
      } catch (error) {
        console.error('Failed to fetch executions:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadExecutions();
  }, [agentId, maxEntries, fetchExecutions]);

  // Filter executions based on criteria
  useEffect(() => {
    let filtered = executions;

    // Filter by agent ID if specified
    if (agentId) {
      filtered = filtered.filter(exec => exec.agent_id === agentId);
    }

    // Filter by status
    if (statusFilter !== 'all') {
      filtered = filtered.filter(exec => exec.status === statusFilter);
    }

    // Filter by date
    if (dateFilter !== 'all') {
      const now = new Date();
      const filterDate = new Date();
      
      switch (dateFilter) {
        case 'today':
          filterDate.setHours(0, 0, 0, 0);
          break;
        case 'week':
          filterDate.setDate(now.getDate() - 7);
          break;
        case 'month':
          filterDate.setMonth(now.getMonth() - 1);
          break;
      }
      
      filtered = filtered.filter(exec => 
        new Date(exec.created_at) >= filterDate
      );
    }

    // Filter by search term
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(exec =>
        exec.id.toLowerCase().includes(term) ||
        exec.agent_id.toLowerCase().includes(term) ||
        (exec.error_message && exec.error_message.toLowerCase().includes(term))
      );
    }

    setFilteredExecutions(filtered);
  }, [executions, agentId, statusFilter, dateFilter, searchTerm]);

  // Load events for selected execution
  useEffect(() => {
    if (selectedExecution) {
      const loadEvents = async () => {
        try {
          await fetchExecutionEvents(selectedExecution, 100);
        } catch (error) {
          console.error('Failed to fetch execution events:', error);
        }
      };

      loadEvents();
    }
  }, [selectedExecution, fetchExecutionEvents]);

  // Convert events to log entries
  useEffect(() => {
    if (selectedExecution) {
      const entries: LogEntry[] = events
        .filter(event => event.run_id === selectedExecution)
        .map(event => ({
          id: event.id,
          timestamp: event.timestamp,
          level: event.level,
          message: event.message,
          source: event.event_type,
          details: event.data
        }));

      setLogEntries(entries);
    } else {
      setLogEntries([]);
    }
  }, [events, selectedExecution]);

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

  const getLevelColor = (level: string): string => {
    switch (level) {
      case 'error':
        return 'text-red-600 bg-red-50';
      case 'warning':
        return 'text-yellow-600 bg-yellow-50';
      case 'info':
        return 'text-blue-600 bg-blue-50';
      case 'debug':
        return 'text-gray-600 bg-gray-50';
      default:
        return 'text-gray-600 bg-gray-50';
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

  const toggleLogExpansion = (logId: string) => {
    const newExpanded = new Set(expandedLogs);
    if (newExpanded.has(logId)) {
      newExpanded.delete(logId);
    } else {
      newExpanded.add(logId);
    }
    setExpandedLogs(newExpanded);
  };

  const handleExecutionClick = (executionId: string) => {
    setSelectedExecution(selectedExecution === executionId ? null : executionId);
  };

  return (
    <div className={`bg-background border border-border rounded-lg shadow-sm ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-border">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-foreground">Execution Log</h3>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-muted-foreground">
              {filteredExecutions.length} executions
            </span>
            {selectedExecution && (
              <button
                onClick={() => setSelectedExecution(null)}
                className="text-sm text-primary hover:text-primary/80 transition-colors"
              >
                Clear Selection
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="px-6 py-4 border-b border-border bg-muted/50">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Search */}
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search executions..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 w-full px-3 py-2 border border-input bg-background rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary sm:text-sm transition-colors"
              />
            </div>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 border border-input bg-background rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary sm:text-sm transition-colors"
            >
              <option value="all">All Status</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
              <option value="running">Running</option>
              <option value="cancelled">Cancelled</option>
              <option value="timeout">Timeout</option>
            </select>

            {/* Date Filter */}
            <select
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
              className="w-full px-3 py-2 border border-input bg-background rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary sm:text-sm transition-colors"
            >
              <option value="all">All Time</option>
              <option value="today">Today</option>
              <option value="week">Past Week</option>
              <option value="month">Past Month</option>
            </select>

            {/* Refresh Button */}
            <button
              onClick={() => fetchExecutions(agentId, undefined, maxEntries)}
              disabled={isLoading}
              className="w-full px-3 py-2 border border-input bg-background text-foreground rounded-md shadow-sm hover:bg-muted focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary sm:text-sm disabled:opacity-50 transition-colors"
            >
              {isLoading ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
        </div>
      )}

      {/* Content */}
      <div className="divide-y divide-border">
        {isLoading ? (
          <div className="px-6 py-8 text-center text-muted-foreground">
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent mx-auto mb-4"></div>
            <div className="text-lg font-medium">Loading executions...</div>
          </div>
        ) : filteredExecutions.length === 0 ? (
          <div className="px-6 py-8 text-center text-muted-foreground">
            <DocumentTextIcon className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <div className="text-lg font-medium mb-2">No executions found</div>
            <div className="text-sm">
              {executions.length === 0
                ? 'Start an execution to see logs here'
                : 'Try adjusting your filters to see more executions'
              }
            </div>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {filteredExecutions.map(execution => (
              <div key={execution.id} className="hover:bg-muted/50 transition-colors">
                {/* Execution Header */}
                <div
                  className="px-6 py-4 cursor-pointer"
                  onClick={() => handleExecutionClick(execution.id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      {/* Expand/Collapse Icon */}
                      <div className="flex-shrink-0">
                        {selectedExecution === execution.id ? (
                          <ChevronDownIcon className="h-5 w-5 text-muted-foreground" />
                        ) : (
                          <ChevronRightIcon className="h-5 w-5 text-muted-foreground" />
                        )}
                      </div>

                      {/* Execution Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-3">
                          <span className="text-sm font-medium text-foreground truncate">
                            {execution.id}
                          </span>
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(execution.status)}`}>
                            {execution.status}
                          </span>
                          {execution.is_running && (
                            <div className="flex items-center text-primary">
                              <div className="w-2 h-2 bg-primary rounded-full mr-2 animate-pulse"></div>
                              <span className="text-xs">Running</span>
                            </div>
                          )}
                        </div>
                        <div className="mt-1 flex items-center space-x-4 text-sm text-muted-foreground">
                          <div className="flex items-center">
                            <CalendarIcon className="h-4 w-4 mr-1" />
                            {new Date(execution.created_at).toLocaleDateString()}
                          </div>
                          <div className="flex items-center">
                            <ClockIcon className="h-4 w-4 mr-1" />
                            {formatDuration(execution)}
                          </div>
                          <div>
                            Agent: {execution.agent_id}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Metrics */}
                    <div className="flex items-center space-x-6 text-sm text-muted-foreground">
                      <div>
                        <span className="font-medium">Nodes:</span>
                        <span className="ml-1">{execution.metrics.total_nodes}</span>
                      </div>
                      <div>
                        <span className="font-medium">Tokens:</span>
                        <span className="ml-1">{execution.metrics.total_tokens_used.toLocaleString()}</span>
                      </div>
                      <div>
                        <span className="font-medium">Success:</span>
                        <span className="ml-1">{execution.metrics.success_rate.toFixed(1)}%</span>
                      </div>
                    </div>
                  </div>

                  {/* Expanded Details */}
                  {selectedExecution === execution.id && (
                    <div className="px-6 py-4 border-t border-border bg-muted/50">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Execution Details */}
                        <div>
                          <h4 className="text-sm font-medium text-foreground mb-3">Execution Details</h4>
                          <dl className="space-y-2 text-sm">
                            <div className="flex justify-between">
                              <dt className="text-muted-foreground">Execution ID:</dt>
                              <dd className="text-foreground font-mono text-xs">{execution.id}</dd>
                            </div>
                            <div className="flex justify-between">
                              <dt className="text-muted-foreground">Agent ID:</dt>
                              <dd className="text-foreground font-mono text-xs">{execution.agent_id}</dd>
                            </div>
                            <div className="flex justify-between">
                              <dt className="text-muted-foreground">Created:</dt>
                              <dd className="text-foreground">{new Date(execution.created_at).toLocaleString()}</dd>
                            </div>
                            {execution.started_at && (
                              <div className="flex justify-between">
                                <dt className="text-muted-foreground">Started:</dt>
                                <dd className="text-foreground">{new Date(execution.started_at).toLocaleString()}</dd>
                              </div>
                            )}
                            {execution.completed_at && (
                              <div className="flex justify-between">
                                <dt className="text-muted-foreground">Completed:</dt>
                                <dd className="text-foreground">{new Date(execution.completed_at).toLocaleString()}</dd>
                              </div>
                            )}
                            {execution.error_message && (
                              <div className="col-span-2">
                                <dt className="text-muted-foreground">Error:</dt>
                                <dd className="text-destructive mt-1">{execution.error_message}</dd>
                              </div>
                            )}
                          </dl>
                        </div>

                        {/* Performance Metrics */}
                        <div>
                          <h4 className="text-sm font-medium text-foreground mb-3">Performance Metrics</h4>
                          <dl className="space-y-2 text-sm">
                            <div className="flex justify-between">
                              <dt className="text-muted-foreground">Total Nodes:</dt>
                              <dd className="text-foreground">{execution.metrics.total_nodes}</dd>
                            </div>
                            <div className="flex justify-between">
                              <dt className="text-muted-foreground">Completed:</dt>
                              <dd className="text-foreground">{execution.metrics.completed_nodes}</dd>
                            </div>
                            <div className="flex justify-between">
                              <dt className="text-muted-foreground">Failed:</dt>
                              <dd className="text-foreground">{execution.metrics.failed_nodes}</dd>
                            </div>
                            <div className="flex justify-between">
                              <dt className="text-muted-foreground">Total Time:</dt>
                              <dd className="text-foreground">{formatDuration(execution)}</dd>
                            </div>
                            <div className="flex justify-between">
                              <dt className="text-muted-foreground">Tokens Used:</dt>
                              <dd className="text-foreground">{execution.metrics.total_tokens_used.toLocaleString()}</dd>
                            </div>
                            <div className="flex justify-between">
                              <dt className="text-muted-foreground">Success Rate:</dt>
                              <dd className="text-foreground">{execution.metrics.success_rate.toFixed(1)}%</dd>
                            </div>
                          </dl>
                        </div>
                      </div>

                      {/* Event Logs */}
                      {logEntries.length > 0 && (
                        <div className="mt-6">
                          <h4 className="text-sm font-medium text-foreground mb-3">Event Logs</h4>
                          <div className="space-y-2 max-h-64 overflow-y-auto">
                            {logEntries.map(log => (
                              <div
                                key={log.id}
                                className="flex items-start space-x-3 p-2 bg-background rounded border border-border"
                              >
                                <div className={`px-2 py-1 text-xs font-medium rounded ${getLevelColor(log.level)}`}>
                                  {log.level.toUpperCase()}
                                </div>
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center justify-between">
                                    <span className="text-sm font-medium text-foreground">
                                      {log.source}
                                    </span>
                                    <span className="text-xs text-muted-foreground">
                                      {new Date(log.timestamp).toLocaleTimeString()}
                                    </span>
                                  </div>
                                  <p className="text-sm text-muted-foreground mt-1">{log.message}</p>
                                  {log.details && (
                                    <button
                                      onClick={() => toggleLogExpansion(log.id)}
                                      className="text-xs text-primary hover:text-primary/80 mt-1 transition-colors"
                                    >
                                      {expandedLogs.has(log.id) ? 'Hide details' : 'Show details'}
                                    </button>
                                  )}
                                  {expandedLogs.has(log.id) && log.details && (
                                    <pre className="mt-2 text-xs text-muted-foreground bg-muted p-2 rounded overflow-auto max-h-32">
                                      {JSON.stringify(log.details, null, 2)}
                                    </pre>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ExecutionLog;