/**
 * RunPanel component for execution control and monitoring.
 *
 * Premium UI implementation with dark mode, glassmorphism, and modern controls.
 */

'use client';

import React, { useState, useEffect } from 'react';
import { PlayIcon, PauseIcon, StopIcon, ArrowPathIcon, ChevronDownIcon, PlusIcon, TrashIcon } from '@heroicons/react/24/outline';
import { useExecutionStore, getExecutionStatusColor, getExecutionStatusIcon, canCancelExecution, canRestartExecution } from '../../store/executionStore';
import { getWebSocketClient } from '../../websocket/client';

interface RunPanelProps {
  agentId: string;
  onExecutionStart?: (executionId: string) => void;
  onExecutionComplete?: (executionId: string, result: any) => void;
  className?: string;
}

export const RunPanel: React.FC<RunPanelProps> = ({
  agentId,
  onExecutionStart,
  onExecutionComplete,
  className = ''
}) => {
  const {
    currentExecution,
    isRunning,
    isCreating,
    isCancelling,
    error,
    websocketConnected,
    startExecution,
    cancelExecution,
    pauseExecution,
    resumeExecution,
    restartExecution,
    clearError
  } = useExecutionStore();

  const [inputData, setInputData] = useState<Record<string, any>>({});
  const [isExpanded, setIsExpanded] = useState(false);

  // Initialize WebSocket connection
  useEffect(() => {
    const wsClient = getWebSocketClient();

    wsClient.on('execution_started', (message) => {
      if (onExecutionStart && message.data?.execution_id) {
        onExecutionStart(message.data.execution_id);
      }
    });

    wsClient.on('execution_completed', (message) => {
      if (onExecutionComplete && message.data?.execution_id) {
        onExecutionComplete(message.data.execution_id, message.data?.result);
      }
    });

    wsClient.connect().catch(console.error);

    return () => {
      wsClient.disconnect();
    };
  }, [agentId, onExecutionStart, onExecutionComplete]);

  const handleStartExecution = async () => {
    if (!agentId) return;
    try {
      clearError();
      await startExecution(agentId, inputData);
    } catch (error) {
      console.error('Failed to start execution:', error);
    }
  };

  const handleCancelExecution = async () => {
    if (!currentExecution) return;
    try {
      await cancelExecution(currentExecution.id);
    } catch (error) {
      console.error('Failed to cancel execution:', error);
    }
  };

  const handlePauseExecution = async () => {
    if (!currentExecution) return;
    try {
      await pauseExecution(currentExecution.id);
    } catch (error) {
      console.error('Failed to pause execution:', error);
    }
  };

  const handleResumeExecution = async () => {
    if (!currentExecution) return;
    try {
      await resumeExecution(currentExecution.id);
    } catch (error) {
      console.error('Failed to resume execution:', error);
    }
  };

  const handleRestartExecution = async () => {
    if (!currentExecution) return;
    try {
      await restartExecution(currentExecution.id);
    } catch (error) {
      console.error('Failed to restart execution:', error);
    }
  };

  const handleInputChange = (key: string, value: any) => {
    setInputData(prev => ({ ...prev, [key]: value }));
  };

  const addInputField = () => {
    const key = `input_${Object.keys(inputData).length + 1}`;
    setInputData(prev => ({ ...prev, [key]: '' }));
  };

  const removeInputField = (key: string) => {
    const newInputData = { ...inputData };
    delete newInputData[key];
    setInputData(newInputData);
  };

  const canCancel = currentExecution ? canCancelExecution(currentExecution) : false;
  const canRestart = currentExecution ? canRestartExecution(currentExecution) : false;

  // Premium Status Badge
  const StatusBadge = ({ status }: { status: string }) => {
    const colors: Record<string, string> = {
      running: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
      completed: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
      failed: 'bg-red-500/10 text-red-400 border-red-500/20',
      cancelled: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
      pending: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20',
    };

    const colorClass = colors[status] || colors.pending;

    return (
      <div className={`flex items-center px-2.5 py-1 rounded-full border text-xs font-medium ${colorClass} backdrop-blur-sm`}>
        <span className="relative flex h-2 w-2 mr-2">
          {status === 'running' && (
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-current opacity-75"></span>
          )}
          <span className="relative inline-flex rounded-full h-2 w-2 bg-current"></span>
        </span>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </div>
    );
  };

  return (
    <div className={`group relative overflow-hidden rounded-xl border border-border bg-background/95 backdrop-blur-xl shadow-2xl ${className}`}>
      {/* Ambient Glow */}
      <div className="absolute -top-24 -right-24 h-48 w-48 rounded-full bg-primary/10 blur-3xl transition-all duration-500 group-hover:bg-primary/20" />

      {/* Header */}
      <div className="relative flex items-center justify-between border-b border-border/50 px-6 py-4">
        <div className="flex items-center gap-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted ring-1 ring-border">
            <PlayIcon className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-foreground">Control Center</h3>
            <p className="text-xs text-muted-foreground">Manage agent execution flow</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {currentExecution && <StatusBadge status={currentExecution.status} />}

          <div className={`flex items-center gap-2 px-2 py-1 rounded-full text-xs font-medium border ${websocketConnected
              ? 'bg-success/10 text-success border-success/30'
              : 'bg-destructive/10 text-destructive border-destructive/30'
            }`}>
          <div className={`h-1.5 w-1.5 rounded-full ${websocketConnected ? 'bg-success' : 'bg-destructive'}`} />
            {websocketConnected ? 'Live' : 'Offline'}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="relative px-6 py-6">
        {/* Error Display */}
        {error && (
          <div className="mb-6 rounded-lg border border-destructive/20 bg-destructive/5 p-4">
            <div className="flex items-start gap-3">
              <div className="rounded-full bg-destructive/10 p-1">
                <svg className="h-4 w-4 text-destructive" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-destructive">Execution Error</p>
                <p className="mt-1 text-xs text-destructive/80">{error}</p>
              </div>
              <button onClick={clearError} className="text-destructive hover:text-destructive/80 transition-colors">
                <span className="sr-only">Dismiss</span>
                <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </div>
        )}

        {/* Controls Grid */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {!isRunning ? (
            <button
              onClick={handleStartExecution}
              disabled={isCreating || !agentId}
              className="group relative flex items-center justify-center gap-2 rounded-lg bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/20 transition-all hover:bg-primary/90 hover:shadow-primary/40 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isCreating ? (
                <svg className="h-5 w-5 animate-spin text-white/80" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
              ) : (
                <PlayIcon className="h-5 w-5" />
              )}
              <span>{isCreating ? 'Initializing...' : 'Start Execution'}</span>
            </button>
          ) : (
            <div className="flex gap-2">
              {canCancel && (
                <button
                  onClick={handleCancelExecution}
                  disabled={isCancelling}
                  className="flex-1 flex items-center justify-center gap-2 rounded-lg bg-destructive/10 px-4 py-3 text-sm font-semibold text-destructive ring-1 ring-destructive/20 transition-all hover:bg-destructive/20 hover:text-destructive/80"
                >
                  {isCancelling ? (
                    <svg className="h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                  ) : (
                    <StopIcon className="h-5 w-5" />
                  )}
                  <span>Stop</span>
                </button>
              )}

              <button
                onClick={handlePauseExecution}
                className="flex-1 flex items-center justify-center gap-2 rounded-lg bg-muted px-4 py-3 text-sm font-semibold text-foreground ring-1 ring-border transition-all hover:bg-muted/80"
              >
                <PauseIcon className="h-5 w-5" />
                <span>Pause</span>
              </button>

              <button
                onClick={handleResumeExecution}
                className="flex-1 flex items-center justify-center gap-2 rounded-lg bg-muted px-4 py-3 text-sm font-semibold text-foreground ring-1 ring-border transition-all hover:bg-muted/80"
              >
                <PlayIcon className="h-5 w-5" />
                <span>Resume</span>
              </button>
            </div>
          )}

          {canRestart && (
            <button
              onClick={handleRestartExecution}
              className="flex items-center justify-center gap-2 rounded-lg bg-muted px-4 py-3 text-sm font-semibold text-foreground ring-1 ring-border transition-all hover:bg-muted/80"
            >
              <ArrowPathIcon className="h-5 w-5" />
              <span>Restart</span>
            </button>
          )}
        </div>

        {/* Stats Grid */}
        {currentExecution && (
          <div className="mt-6 grid grid-cols-2 gap-3">
            <div className="rounded-lg bg-muted/50 p-3 ring-1 ring-border/50">
              <p className="text-xs font-medium text-muted-foreground">Execution ID</p>
              <p className="mt-1 truncate text-sm font-mono text-foreground">{currentExecution.id}</p>
            </div>
            <div className="rounded-lg bg-muted/50 p-3 ring-1 ring-border/50">
              <p className="text-xs font-medium text-muted-foreground">Started At</p>
              <p className="mt-1 text-sm font-mono text-foreground">
                {currentExecution.started_at ? new Date(currentExecution.started_at).toLocaleTimeString() : '-'}
              </p>
            </div>
          </div>
        )}

        {/* Configuration Section */}
        <div className="mt-6 border-t border-border/50 pt-4">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex w-full items-center justify-between rounded-lg px-2 py-2 text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
          >
            <span>Input Configuration</span>
            <ChevronDownIcon className={`h-4 w-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
          </button>

          {isExpanded && (
            <div className="mt-4 space-y-3 animate-in slide-in-from-top-2 fade-in duration-200">
              {Object.entries(inputData).map(([key, value]) => (
                <div key={key} className="flex items-center gap-2">
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
                    className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground placeholder-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary transition-colors"
                    placeholder="Key"
                  />
                  <input
                    type="text"
                    value={value}
                    onChange={(e) => handleInputChange(key, e.target.value)}
                    className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground placeholder-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary transition-colors"
                    placeholder="Value"
                  />
                  <button
                    onClick={() => removeInputField(key)}
                    className="rounded-md p-2 text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors"
                  >
                    <TrashIcon className="h-4 w-4" />
                  </button>
                </div>
              ))}

              <button
                onClick={addInputField}
                className="flex w-full items-center justify-center gap-2 rounded-md border border-dashed border-border py-2 text-sm text-muted-foreground hover:border-border hover:bg-muted/50 hover:text-foreground transition-colors"
              >
                <PlusIcon className="h-4 w-4" />
                <span>Add Input Parameter</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RunPanel;