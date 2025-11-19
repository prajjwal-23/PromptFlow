/**
 * Execution state management using Zustand.
 * 
 * This store manages the state for agent executions, including real-time updates,
 * WebSocket integration, and execution lifecycle management.
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { api } from './authStore';

// Types
export interface ExecutionInput {
  [key: string]: any;
}

export interface ExecutionConfig {
  max_execution_time?: number;
  max_concurrent_nodes?: number;
  enable_streaming?: boolean;
  enable_metrics?: boolean;
  retry_failed_nodes?: boolean;
  save_intermediate_results?: boolean;
  priority?: 'low' | 'normal' | 'high' | 'critical';
}

export interface ExecutionMetrics {
  total_nodes: number;
  completed_nodes: number;
  failed_nodes: number;
  skipped_nodes: number;
  total_execution_time: number;
  total_tokens_used: number;
  peak_memory_usage: number;
  peak_cpu_usage: number;
  network_requests: number;
  success_rate: number;
  average_execution_time: number;
}

export interface NodeOutput {
  node_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped' | 'timeout';
  data?: Record<string, any>;
  error?: string;
  execution_time: number;
  tokens_used: number;
  metadata?: Record<string, any>;
  timestamp: string;
}

export interface ExecutionEvent {
  id: string;
  run_id: string;
  node_id?: string;
  event_type: string;
  level: 'info' | 'warning' | 'error' | 'debug';
  message: string;
  data?: Record<string, any>;
  timestamp: string;
  duration_ms?: number;
  token_count?: number;
}

export interface Execution {
  id: string;
  agent_id: string;
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled' | 'timeout';
  input_data: ExecutionInput;
  output_data?: Record<string, any>;
  error_message?: string;
  metrics: ExecutionMetrics;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  updated_at: string;
  duration?: number;
  is_finished: boolean;
  is_running: boolean;
  metadata: Record<string, any>;
  node_outputs?: Record<string, NodeOutput>;
}

export interface ExecutionState {
  // State
  executions: Execution[];
  currentExecution: Execution | null;
  events: ExecutionEvent[];
  isRunning: boolean;
  isLoading: boolean;
  isCreating: boolean;
  isCancelling: boolean;
  isPausing: boolean;
  isResuming: boolean;
  error: string | null;
  websocketConnected: boolean;
  
  // WebSocket connection state
  websocketUrl: string | null;
  reconnectAttempts: number;
  lastHeartbeat: string | null;
  
  // Performance metrics
  totalExecutions: number;
  successfulExecutions: number;
  failedExecutions: number;
  averageExecutionTime: number;
  
  // Actions
  startExecution: (agentId: string, inputData: ExecutionInput, config?: ExecutionConfig) => Promise<Execution>;
  cancelExecution: (executionId: string) => Promise<boolean>;
  pauseExecution: (executionId: string) => Promise<boolean>;
  resumeExecution: (executionId: string) => Promise<boolean>;
  restartExecution: (executionId: string) => Promise<Execution>;
  
  // Fetch operations
  fetchExecutions: (agentId?: string, status?: string, limit?: number, offset?: number) => Promise<void>;
  fetchExecution: (executionId: string) => Promise<void>;
  fetchExecutionEvents: (executionId: string, limit?: number, eventType?: string) => Promise<void>;
  fetchExecutionMetrics: (executionId: string) => Promise<ExecutionMetrics>;
  
  // WebSocket operations
  connectWebSocket: (executionId: string) => Promise<void>;
  disconnectWebSocket: (executionId: string) => Promise<void>;
  subscribeToExecution: (executionId: string, eventTypes?: string[]) => Promise<string>;
  unsubscribeFromExecution: (executionId: string, subscriptionId: string) => Promise<boolean>;
  
  // Event handling
  addEvent: (event: ExecutionEvent) => void;
  clearEvents: () => void;
  clearError: () => void;
  setLoading: (loading: boolean) => void;
  reset: () => void;
  
  // Optimistic updates
  updateExecutionStatus: (executionId: string, status: Execution['status']) => void;
  updateNodeOutput: (executionId: string, nodeId: string, output: NodeOutput) => void;
  updateMetrics: (executionId: string, metrics: Partial<ExecutionMetrics>) => void;
}

const initialState = {
  executions: [],
  currentExecution: null,
  events: [],
  isRunning: false,
  isLoading: false,
  isCreating: false,
  isCancelling: false,
  isPausing: false,
  isResuming: false,
  error: null,
  websocketConnected: false,
  websocketUrl: null,
  reconnectAttempts: 0,
  lastHeartbeat: null,
  totalExecutions: 0,
  successfulExecutions: 0,
  failedExecutions: 0,
  averageExecutionTime: 0,
};

export const useExecutionStore = create<ExecutionState>()(
  persist(
    (set, get) => ({
      ...initialState,

      // Start a new execution
      startExecution: async (agentId: string, inputData: ExecutionInput, config?: ExecutionConfig) => {
        set({ isCreating: true, error: null });
        
        try {
          const response = await api.post('/runs/', {
            agent_id: agentId,
            input_data: inputData,
            config: config || {},
            priority: config?.priority || 'normal',
            metadata: {
              started_at: new Date().toISOString(),
            },
          });
          
          const execution = response.data;
          
          // Add to executions list
          const currentExecutions = get().executions;
          set({
            executions: [execution, ...currentExecutions],
            currentExecution: execution,
            isCreating: false,
            isRunning: true,
            totalExecutions: get().totalExecutions + 1,
          });
          
          // Connect to WebSocket for real-time updates
          await get().connectWebSocket(execution.id);
          
          return execution;
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to start execution';
          set({
            isCreating: false,
            error: errorMessage,
            isRunning: false,
          });
          throw error;
        }
      },

      // Cancel an execution
      cancelExecution: async (executionId: string) => {
        set({ isCancelling: true, error: null });
        
        try {
          const response = await api.post(`/runs/${executionId}/cancel`);
          const success = response.data.success;
          
          if (success) {
            // Update execution status
            const currentExecutions = get().executions;
            const updatedExecutions = currentExecutions.map(exec =>
              exec.id === executionId
                ? { ...exec, status: 'cancelled' as const }
                : exec
            );
            
            const currentExecution = get().currentExecution;
            const newCurrentExecution = currentExecution?.id === executionId
              ? { ...currentExecution, status: 'cancelled' as const }
              : currentExecution;
            
            set({
              executions: updatedExecutions,
              currentExecution: newCurrentExecution,
              isCancelling: false,
              isRunning: false,
              failedExecutions: get().failedExecutions + 1,
            });
            
            // Disconnect WebSocket
            await get().disconnectWebSocket(executionId);
          }
          
          return success;
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to cancel execution';
          set({
            isCancelling: false,
            error: errorMessage,
          });
          return false;
        }
      },

      // Pause an execution
      pauseExecution: async (executionId: string) => {
        set({ isPausing: true, error: null });
        
        try {
          const response = await api.post(`/runs/${executionId}/pause`);
          const success = response.data.success;
          
          if (success) {
            // Update execution status
            const currentExecutions = get().executions;
            const updatedExecutions = currentExecutions.map(exec =>
              exec.id === executionId
                ? { ...exec, status: 'paused' as const }
                : exec
            );
            
            const currentExecution = get().currentExecution;
            const newCurrentExecution = currentExecution?.id === executionId
              ? { ...currentExecution, status: 'paused' as const }
              : currentExecution;
            
            set({
              executions: updatedExecutions,
              currentExecution: newCurrentExecution,
              isPausing: false,
              isRunning: false,
            });
            
            // Add pause event
            get().addEvent({
              id: `pause_${executionId}_${Date.now()}`,
              run_id: executionId,
              event_type: 'execution_paused',
              level: 'info',
              message: 'Execution paused',
              timestamp: new Date().toISOString(),
            });
          }
          
          return success;
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to pause execution';
          set({
            isPausing: false,
            error: errorMessage,
          });
          return false;
        }
      },

      // Resume a paused execution
      resumeExecution: async (executionId: string) => {
        set({ isResuming: true, error: null });
        
        try {
          const response = await api.post(`/runs/${executionId}/resume`);
          const success = response.data.success;
          
          if (success) {
            // Update execution status
            const currentExecutions = get().executions;
            const updatedExecutions = currentExecutions.map(exec =>
              exec.id === executionId
                ? { ...exec, status: 'running' as const }
                : exec
            );
            
            const currentExecution = get().currentExecution;
            const newCurrentExecution = currentExecution?.id === executionId
              ? { ...currentExecution, status: 'running' as const }
              : currentExecution;
            
            set({
              executions: updatedExecutions,
              currentExecution: newCurrentExecution,
              isResuming: false,
              isRunning: true,
            });
            
            // Add resume event
            get().addEvent({
              id: `resume_${executionId}_${Date.now()}`,
              run_id: executionId,
              event_type: 'execution_resumed',
              level: 'info',
              message: 'Execution resumed',
              timestamp: new Date().toISOString(),
            });
          }
          
          return success;
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to resume execution';
          set({
            isResuming: false,
            error: errorMessage,
          });
          return false;
        }
      },

      // Restart an execution
      restartExecution: async (executionId: string) => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await api.post(`/runs/${executionId}/restart`);
          const newExecution = response.data;
          
          // Add to executions list
          const currentExecutions = get().executions;
          set({
            executions: [newExecution, ...currentExecutions],
            currentExecution: newExecution,
            isLoading: false,
            totalExecutions: get().totalExecutions + 1,
          });
          
          // Connect to WebSocket for real-time updates
          await get().connectWebSocket(newExecution.id);
          
          return newExecution;
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to restart execution';
          set({
            isLoading: false,
            error: errorMessage,
          });
          throw error;
        }
      },

      // Fetch executions with optional filtering
      fetchExecutions: async (
        agentId?: string,
        status?: string,
        limit?: number,
        offset?: number
      ) => {
        set({ isLoading: true, error: null });
        
        try {
          const params: Record<string, any> = {};
          if (agentId) params.agent_id = agentId;
          if (status) params.status = status;
          if (limit) params.limit = limit;
          if (offset) params.offset = offset;
          
          const response = await api.get('/runs/', { params });
          const executions = response.data.runs || [];
          
          set({
            executions,
            isLoading: false,
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to fetch executions';
          set({
            isLoading: false,
            error: errorMessage,
          });
          throw error;
        }
      },

      // Fetch single execution
      fetchExecution: async (executionId: string) => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await api.get(`/runs/${executionId}`);
          const execution = response.data;
          
          set({
            currentExecution: execution,
            isLoading: false,
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to fetch execution';
          set({
            isLoading: false,
            error: errorMessage,
          });
          throw error;
        }
      },

      // Fetch execution events
      fetchExecutionEvents: async (executionId: string, limit?: number, eventType?: string) => {
        set({ isLoading: true, error: null });
        
        try {
          const params: Record<string, any> = {};
          if (limit) params.limit = limit;
          if (eventType) params.event_type = eventType;
          
          const response = await api.get(`/runs/${executionId}/events`, { params });
          const events = response.data.events || [];
          
          set({
            events,
            isLoading: false,
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to fetch execution events';
          set({
            isLoading: false,
            error: errorMessage,
          });
          throw error;
        }
      },

      // Fetch execution metrics
      fetchExecutionMetrics: async (executionId: string) => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await api.get(`/runs/${executionId}/metrics`);
          const metrics = response.data;
          
          // Update metrics in current execution
          const currentExecution = get().currentExecution;
          if (currentExecution && currentExecution.id === executionId) {
            set({
              currentExecution: {
                ...currentExecution,
                metrics,
              },
              isLoading: false,
            });
          }
          
          return metrics;
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to fetch execution metrics';
          set({
            isLoading: false,
            error: errorMessage,
          });
          throw error;
        }
      },

      // WebSocket connection management
      connectWebSocket: async (executionId: string) => {
        if (get().websocketConnected && get().currentExecution?.id === executionId) {
          return; // Already connected
        }
        
        const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}/ws/${executionId}`;
        
        try {
          const ws = new WebSocket(wsUrl);
          
          ws.onopen = () => {
            set({
              websocketConnected: true,
              websocketUrl: wsUrl,
              reconnectAttempts: 0,
              lastHeartbeat: new Date().toISOString(),
            });
            
            // Subscribe to execution events
            get().subscribeToExecution(executionId);
          };
          
          ws.onmessage = (event) => {
            try {
              const eventData = JSON.parse(event.data);
              get().addEvent(eventData);
            } catch (error) {
              console.error('WebSocket message error:', error);
            }
          };
          
          ws.onclose = () => {
            set({
              websocketConnected: false,
              websocketUrl: null,
              reconnectAttempts: get().reconnectAttempts + 1,
            });
            
            // Attempt reconnection
            if (get().reconnectAttempts < 3) {
              setTimeout(() => {
                get().connectWebSocket(executionId);
              }, 2000 * Math.pow(2, get().reconnectAttempts));
            }
          };
          
          ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            set({
              error: 'WebSocket connection error',
              websocketConnected: false,
            });
          };
          
        } catch (error) {
          console.error('WebSocket connection error:', error);
          set({
            error: 'Failed to connect WebSocket',
            websocketConnected: false,
          });
        }
      },

      disconnectWebSocket: async (executionId: string) => {
        // This would disconnect the WebSocket connection
        set({
          websocketConnected: false,
          websocketUrl: null,
        });
      },

      // Subscribe to execution events
      subscribeToExecution: async (executionId: string, eventTypes?: string[]) => {
        // This would set up event subscription
        console.log('Subscribing to execution events for:', executionId, eventTypes);
        return `sub_${executionId}_${Date.now()}`;
      },

      // Unsubscribe from execution events
      unsubscribeFromExecution: async (executionId: string, subscriptionId: string) => {
        // This would cancel event subscription
        console.log('Unsubscribing from execution events:', executionId, subscriptionId);
        return true;
      },

      // Event handling
      addEvent: (event: ExecutionEvent) => {
        const currentEvents = get().events;
        const updatedEvents = [event, ...currentEvents];
        
        // Keep only last 1000 events
        const trimmedEvents = updatedEvents.slice(-1000);
        
        set({
          events: trimmedEvents,
        });
        
        // Update execution state based on events
        if (event.event_type === 'execution_completed') {
          const currentExecution = get().currentExecution;
          if (currentExecution && currentExecution.id === event.run_id) {
            set({
              currentExecution: {
                ...currentExecution,
                status: 'completed',
                completed_at: event.timestamp,
              },
              isRunning: false,
              successfulExecutions: get().successfulExecutions + 1,
            });
          }
        } else if (event.event_type === 'execution_failed') {
          const currentExecution = get().currentExecution;
          if (currentExecution && currentExecution.id === event.run_id) {
            set({
              currentExecution: {
                ...currentExecution,
                status: 'failed',
                error_message: event.message,
                completed_at: event.timestamp,
              },
              isRunning: false,
              failedExecutions: get().failedExecutions + 1,
            });
          }
        } else if (event.event_type === 'execution_paused') {
          const currentExecution = get().currentExecution;
          if (currentExecution && currentExecution.id === event.run_id) {
            set({
              currentExecution: {
                ...currentExecution,
                status: 'paused',
              },
              isRunning: false,
            });
          }
        } else if (event.event_type === 'execution_resumed') {
          const currentExecution = get().currentExecution;
          if (currentExecution && currentExecution.id === event.run_id) {
            set({
              currentExecution: {
                ...currentExecution,
                status: 'running',
              },
              isRunning: true,
            });
          }
        }
      },

      clearEvents: () => {
        set({ events: [] });
      },

      // Clear error
      clearError: () => {
        set({ error: null });
      },

      // Set loading state
      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },

      // Reset store
      reset: () => {
        set(initialState);
      },

      // Optimistic updates
      updateExecutionStatus: (executionId: string, status: Execution['status']) => {
        const currentExecutions = get().executions;
        const updatedExecutions = currentExecutions.map(exec =>
          exec.id === executionId
            ? { ...exec, status }
            : exec
        );
        
        const currentExecution = get().currentExecution;
        const newCurrentExecution = currentExecution?.id === executionId
          ? { ...currentExecution, status }
          : currentExecution;
        
        set({
          executions: updatedExecutions,
          currentExecution: newCurrentExecution,
          isRunning: status === 'running',
        });
      },

      updateNodeOutput: (executionId: string, nodeId: string, output: NodeOutput) => {
        const currentExecution = get().currentExecution;
        if (currentExecution && currentExecution.id === executionId) {
          const nodeOutputs = currentExecution.node_outputs || {};
          nodeOutputs[nodeId] = output;
          
          set({
            currentExecution: {
              ...currentExecution,
              node_outputs: nodeOutputs,
            },
          });
        }
      },

      updateMetrics: (executionId: string, metrics: Partial<ExecutionMetrics>) => {
        const currentExecution = get().currentExecution;
        if (currentExecution && currentExecution.id === executionId) {
          const currentMetrics = currentExecution.metrics;
          const updatedMetrics = { ...currentMetrics, ...metrics };
          
          set({
            currentExecution: {
              ...currentExecution,
              metrics: updatedMetrics,
            },
          });
        }
      },
    }),
    {
      name: 'execution-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        currentExecution: state.currentExecution,
        executions: state.executions.slice(-50), // Keep last 50 executions
        websocketConnected: state.websocketConnected,
      }),
    }
  )
);

// Selectors for common use cases
export const selectExecutions = (state: ExecutionState) => state.executions;
export const selectCurrentExecution = (state: ExecutionState) => state.currentExecution;
export const selectExecutionById = (state: ExecutionState, id: string) => 
  state.executions.find(exec => exec.id === id);
export const selectEvents = (state: ExecutionState) => state.events;
export const selectIsRunning = (state: ExecutionState) => state.isRunning;
export const selectWebSocketConnected = (state: ExecutionState) => state.websocketConnected;

// Helper functions
export const getExecutionStatusColor = (status: Execution['status']): string => {
  switch (status) {
    case 'pending':
      return 'bg-gray-100 text-gray-800';
    case 'running':
      return 'bg-blue-100 text-blue-800';
    case 'paused':
      return 'bg-purple-100 text-purple-800';
    case 'completed':
      return 'bg-green-100 text-green-800';
    case 'failed':
      return 'bg-red-100 text-red-800';
    case 'cancelled':
      return 'bg-yellow-100 text-yellow-800';
    case 'timeout':
      return 'bg-orange-100 text-orange-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

export const getExecutionStatusIcon = (status: Execution['status']): string => {
  switch (status) {
    case 'pending':
      return '⏳';
    case 'running':
      return '🔄';
    case 'paused':
      return '⏸️';
    case 'completed':
      return '✅';
    case 'failed':
      return '❌';
    case 'cancelled':
      return '🚫';
    case 'timeout':
      return '⏱';
    default:
      return '❓';
  }
};

export const canCancelExecution = (execution: Execution | null): boolean => {
  if (!execution) return false;
  return ['running', 'pending'].includes(execution.status);
};

export const canPauseExecution = (execution: Execution | null): boolean => {
  if (!execution) return false;
  return ['running'].includes(execution.status);
};

export const canResumeExecution = (execution: Execution | null): boolean => {
  if (!execution) return false;
  return ['paused'].includes(execution.status);
};

export const canRestartExecution = (execution: Execution | null): boolean => {
  if (!execution) return false;
  return ['completed', 'failed', 'cancelled', 'timeout', 'paused'].includes(execution.status);
};

export const isExecutionActive = (execution: Execution | null): boolean => {
  if (!execution) return false;
  return ['pending', 'running', 'paused'].includes(execution.status);
};

export const getExecutionProgress = (execution: Execution | null): number => {
  if (!execution) return 0;
  
  const metrics = execution.metrics;
  if (!metrics) return 0;
  
  const totalNodes = metrics.total_nodes;
  if (totalNodes === 0) return 0;
  
  return (metrics.completed_nodes / totalNodes) * 100;
};