/**
 * NodeExecution component for displaying individual node execution status.
 *
 * This component shows the status of individual nodes in the execution graph,
 * including progress, timing, and detailed node information.
 */

'use client';

import React, { useState, useEffect } from 'react';
import { useExecutionStore } from '../../store/executionStore';
import { 
  CheckCircleIcon, 
  XCircleIcon, 
  ClockIcon, 
  PlayIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

interface NodeExecutionProps {
  executionId?: string;
  showDetails?: boolean;
  compact?: boolean;
  className?: string;
}

interface NodeStatus {
  id: string;
  name: string;
  type: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped' | 'timeout';
  startTime?: string;
  endTime?: string;
  duration?: number;
  tokensUsed?: number;
  error?: string;
  output?: any;
  progress?: number;
}

export const NodeExecution: React.FC<NodeExecutionProps> = ({
  executionId,
  showDetails = true,
  compact = false,
  className = ''
}) => {
  const {
    currentExecution,
    events,
    updateNodeOutput
  } = useExecutionStore();

  const [nodes, setNodes] = useState<NodeStatus[]>([]);
  const [selectedNode, setSelectedNode] = useState<NodeStatus | null>(null);

  // Process events to extract node status
  useEffect(() => {
    if (!currentExecution || (executionId && currentExecution.id !== executionId)) {
      setNodes([]);
      return;
    }

    const nodeMap = new Map<string, NodeStatus>();

    // Get node outputs from execution
    const nodeOutputs = currentExecution.node_outputs || {};

    // Process events to build node status
    events
      .filter(event => event.run_id === currentExecution.id && event.node_id)
      .forEach(event => {
        const nodeId = event.node_id!;
        
        if (!nodeMap.has(nodeId)) {
          nodeMap.set(nodeId, {
            id: nodeId,
            name: nodeId.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
            type: 'unknown',
            status: 'pending'
          });
        }

        const node = nodeMap.get(nodeId)!;

        // Update node based on event type
        switch (event.event_type) {
          case 'node_started':
            node.status = 'running';
            node.startTime = event.timestamp;
            break;
          case 'node_completed':
            node.status = 'completed';
            node.endTime = event.timestamp;
            if (node.startTime) {
              node.duration = new Date(node.endTime).getTime() - new Date(node.startTime).getTime();
            }
            if (event.token_count) {
              node.tokensUsed = event.token_count;
            }
            break;
          case 'node_failed':
            node.status = 'failed';
            node.endTime = event.timestamp;
            node.error = event.message;
            if (node.startTime) {
              node.duration = new Date(node.endTime).getTime() - new Date(node.startTime).getTime();
            }
            break;
          case 'node_skipped':
            node.status = 'skipped';
            node.endTime = event.timestamp;
            break;
          case 'node_timeout':
            node.status = 'timeout';
            node.endTime = event.timestamp;
            node.error = event.message;
            break;
        }

        // Update with node output data if available
        if (nodeOutputs[nodeId]) {
          const output = nodeOutputs[nodeId];
          node.output = output.data;
          node.tokensUsed = output.tokens_used;
          node.duration = output.execution_time;
          if (output.status !== node.status) {
            node.status = output.status as any;
          }
        }
      });

    // Convert to array and sort by start time
    const nodesArray = Array.from(nodeMap.values()).sort((a, b) => {
      if (!a.startTime && !b.startTime) return 0;
      if (!a.startTime) return 1;
      if (!b.startTime) return -1;
      return new Date(a.startTime).getTime() - new Date(b.startTime).getTime();
    });

    setNodes(nodesArray);
  }, [currentExecution, events, executionId]);

  const getStatusIcon = (status: NodeStatus['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      case 'running':
        return <PlayIcon className="h-5 w-5 text-blue-500" />;
      case 'timeout':
        return <ExclamationTriangleIcon className="h-5 w-5 text-orange-500" />;
      case 'skipped':
        return <ClockIcon className="h-5 w-5 text-gray-400" />;
      case 'pending':
      default:
        return <ClockIcon className="h-5 w-5 text-gray-300" />;
    }
  };

  const getStatusColor = (status: NodeStatus['status']) => {
    switch (status) {
      case 'completed':
        return 'text-green-700 bg-green-50 border-green-200';
      case 'failed':
        return 'text-red-700 bg-red-50 border-red-200';
      case 'running':
        return 'text-blue-700 bg-blue-50 border-blue-200';
      case 'timeout':
        return 'text-orange-700 bg-orange-50 border-orange-200';
      case 'skipped':
        return 'text-gray-600 bg-gray-50 border-gray-200';
      case 'pending':
      default:
        return 'text-gray-500 bg-gray-50 border-gray-200';
    }
  };

  const formatDuration = (duration?: number): string => {
    if (!duration) return '-';
    if (duration < 1000) return `${duration}ms`;
    return `${(duration / 1000).toFixed(2)}s`;
  };

  const formatTokens = (tokens?: number): string => {
    if (!tokens) return '-';
    return tokens.toLocaleString();
  };

  const getNodeProgress = (node: NodeStatus): number => {
    if (node.status === 'completed') return 100;
    if (node.status === 'running') return node.progress || 50;
    if (node.status === 'failed' || node.status === 'timeout') return 100;
    return 0;
  };

  if (compact) {
    return (
      <div className={`space-y-2 ${className}`}>
        {nodes.map(node => (
          <div
            key={node.id}
            className="flex items-center space-x-3 p-2 bg-muted/50 rounded-md"
          >
            {getStatusIcon(node.status)}
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-foreground truncate">
                  {node.name}
                </span>
                <span className="text-xs text-muted-foreground">
                  {formatDuration(node.duration)}
                </span>
              </div>
              <div className="w-full bg-muted rounded-full h-1 mt-1">
                <div
                  className="bg-blue-600 h-1 rounded-full transition-all duration-300"
                  style={{ width: `${getNodeProgress(node)}%` }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className={`bg-background border border-border rounded-lg shadow-sm ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-border">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-foreground">Node Execution</h3>
          <div className="flex items-center space-x-4 text-sm text-muted-foreground">
            <span>Total: {nodes.length}</span>
            <span className="text-success">
              Completed: {nodes.filter(n => n.status === 'completed').length}
            </span>
            <span className="text-destructive">
              Failed: {nodes.filter(n => n.status === 'failed').length}
            </span>
            <span className="text-primary">
              Running: {nodes.filter(n => n.status === 'running').length}
            </span>
          </div>
        </div>
      </div>

      {/* Nodes List */}
      <div className="divide-y divide-border">
        {nodes.length === 0 ? (
          <div className="px-6 py-8 text-center text-muted-foreground">
            <div className="text-lg font-medium mb-2">No nodes executing</div>
            <div className="text-sm">
              Start an execution to see node status here
            </div>
          </div>
        ) : (
          nodes.map(node => (
            <div
              key={node.id}
              className={`px-6 py-4 hover:bg-muted/50 cursor-pointer transition-colors ${
                selectedNode?.id === node.id ? 'bg-muted/50' : ''
              }`}
              onClick={() => setSelectedNode(selectedNode?.id === node.id ? null : node)}
            >
              <div className="flex items-start space-x-4">
                {/* Status Icon */}
                <div className="flex-shrink-0 mt-1">
                  {getStatusIcon(node.status)}
                </div>

                {/* Node Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-foreground">
                        {node.name}
                      </h4>
                      <p className="text-sm text-muted-foreground">
                        Type: {node.type} • ID: {node.id}
                      </p>
                    </div>
                    <div className={`px-2 py-1 text-xs font-medium rounded-full border ${getStatusColor(node.status)}`}>
                      {node.status}
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="mt-3">
                    <div className="w-full bg-muted rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all duration-300 ${
                          node.status === 'completed' ? 'bg-green-600' :
                          node.status === 'failed' || node.status === 'timeout' ? 'bg-red-600' :
                          node.status === 'running' ? 'bg-blue-600' : 'bg-gray-300'
                        }`}
                        style={{ width: `${getNodeProgress(node)}%` }}
                      />
                    </div>
                  </div>

                  {/* Metrics */}
                  <div className="mt-3 flex items-center space-x-6 text-sm text-muted-foreground">
                    <div>
                      <span className="font-medium">Duration:</span>
                      <span className="ml-1">{formatDuration(node.duration)}</span>
                    </div>
                    {node.tokensUsed && (
                      <div>
                        <span className="font-medium">Tokens:</span>
                        <span className="ml-1">{formatTokens(node.tokensUsed)}</span>
                      </div>
                    )}
                    {node.startTime && (
                      <div>
                        <span className="font-medium">Started:</span>
                        <span className="ml-1">{new Date(node.startTime).toLocaleTimeString()}</span>
                      </div>
                    )}
                  </div>

                  {/* Error Message */}
                  {node.error && (
                    <div className="mt-3 p-3 bg-destructive/10 border border-destructive/20 rounded-md">
                      <div className="flex">
                        <ExclamationTriangleIcon className="h-5 w-5 text-destructive mr-2" />
                        <p className="text-sm text-destructive">{node.error}</p>
                      </div>
                    </div>
                  )}

                  {/* Expanded Details */}
                  {selectedNode?.id === node.id && showDetails && (
                    <div className="mt-4 p-4 bg-muted/50 rounded-md">
                      <h5 className="text-sm font-medium text-foreground mb-3">Node Details</h5>
                      
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="font-medium text-foreground">Node ID:</span>
                          <p className="text-muted-foreground">{node.id}</p>
                        </div>
                        <div>
                          <span className="font-medium text-foreground">Type:</span>
                          <p className="text-muted-foreground">{node.type}</p>
                        </div>
                        <div>
                          <span className="font-medium text-foreground">Status:</span>
                          <p className="text-muted-foreground">{node.status}</p>
                        </div>
                        <div>
                          <span className="font-medium text-foreground">Progress:</span>
                          <p className="text-muted-foreground">{getNodeProgress(node)}%</p>
                        </div>
                      </div>

                      {node.output && (
                        <div className="mt-4">
                          <h6 className="text-sm font-medium text-foreground mb-2">Output</h6>
                          <pre className="text-xs text-muted-foreground bg-background p-3 rounded border border-border overflow-auto max-h-32">
                            {typeof node.output === 'string' 
                              ? node.output 
                              : JSON.stringify(node.output, null, 2)
                            }
                          </pre>
                        </div>
                      )}

                      {node.startTime && (
                        <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <span className="font-medium text-foreground">Start Time:</span>
                            <p className="text-muted-foreground">{new Date(node.startTime).toLocaleString()}</p>
                          </div>
                          {node.endTime && (
                            <div>
                              <span className="font-medium text-foreground">End Time:</span>
                              <p className="text-muted-foreground">{new Date(node.endTime).toLocaleString()}</p>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default NodeExecution;