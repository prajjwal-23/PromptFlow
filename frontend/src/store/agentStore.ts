/**
 * Agent state management using Zustand.
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { api } from './authStore';

// Types
export interface Agent {
  id: string;
  workspace_id: string;
  name: string;
  description: string | null;
  graph_json: Record<string, any> | null;
  version: string;
  is_active: boolean;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface AgentCreateData {
  name: string;
  description?: string;
  workspace_id: string;
  graph_json?: Record<string, any>;
}

export interface AgentUpdateData {
  name?: string;
  description?: string;
  graph_json?: Record<string, any>;
  is_active?: boolean;
}

export interface AgentDuplicateData {
  name: string;
}

export interface AgentState {
  // State
  agents: Agent[];
  currentAgent: Agent | null;
  isLoading: boolean;
  isCreating: boolean;
  isUpdating: boolean;
  isDeleting: boolean;
  error: string | null;

  // Actions
  fetchAgents: (workspaceId?: string) => Promise<void>;
  fetchAgent: (id: string) => Promise<void>;
  createAgent: (data: AgentCreateData) => Promise<Agent>;
  updateAgent: (id: string, data: AgentUpdateData) => Promise<void>;
  deleteAgent: (id: string) => Promise<void>;
  duplicateAgent: (id: string, data: AgentDuplicateData) => Promise<Agent>;
  setCurrentAgent: (agent: Agent | null) => void;
  
  // Utility
  clearError: () => void;
  setLoading: (loading: boolean) => void;
  reset: () => void;
}

const initialState = {
  agents: [],
  currentAgent: null,
  isLoading: false,
  isCreating: false,
  isUpdating: false,
  isDeleting: false,
  error: null,
};

export const useAgentStore = create<AgentState>()(
  persist(
    (set, get) => ({
      ...initialState,

      // Fetch all agents (optionally filtered by workspace)
      fetchAgents: async (workspaceId?: string) => {
        set({ isLoading: true, error: null });
        
        try {
          const params = workspaceId ? { workspace_id: workspaceId } : {};
          const response = await api.get('/agents', { params });
          const agents = response.data;
          
          set({
            agents,
            isLoading: false,
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to fetch agents';
          set({
            isLoading: false,
            error: errorMessage,
          });
          throw error;
        }
      },

      // Fetch single agent
      fetchAgent: async (id: string) => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await api.get(`/agents/${id}`);
          const agent = response.data;
          
          set({
            currentAgent: agent,
            isLoading: false,
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to fetch agent';
          set({
            isLoading: false,
            error: errorMessage,
          });
          throw error;
        }
      },

      // Create new agent
      createAgent: async (data: AgentCreateData) => {
        set({ isCreating: true, error: null });
        
        try {
          const response = await api.post('/agents', data);
          const newAgent = response.data;
          
          // Add to agents list
          const currentAgents = get().agents;
          set({
            agents: [newAgent, ...currentAgents],
            currentAgent: newAgent,
            isCreating: false,
          });
          
          return newAgent;
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to create agent';
          set({
            isCreating: false,
            error: errorMessage,
          });
          throw error;
        }
      },

      // Update agent
      updateAgent: async (id: string, data: AgentUpdateData) => {
        set({ isUpdating: true, error: null });
        
        try {
          const response = await api.put(`/agents/${id}`, data);
          const updatedAgent = response.data;
          
          // Update in agents list
          const currentAgents = get().agents;
          const updatedAgents = currentAgents.map(agent => 
            agent.id === id ? updatedAgent : agent
          );
          
          // Update current agent if it matches
          const currentAgent = get().currentAgent;
          const newCurrentAgent = currentAgent?.id === id 
            ? updatedAgent 
            : currentAgent;
          
          set({
            agents: updatedAgents,
            currentAgent: newCurrentAgent,
            isUpdating: false,
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to update agent';
          set({
            isUpdating: false,
            error: errorMessage,
          });
          throw error;
        }
      },

      // Delete agent
      deleteAgent: async (id: string) => {
        set({ isDeleting: true, error: null });
        
        try {
          await api.delete(`/agents/${id}`);
          
          // Remove from agents list
          const currentAgents = get().agents;
          const updatedAgents = currentAgents.filter(agent => agent.id !== id);
          
          // Clear current agent if it matches
          const currentAgent = get().currentAgent;
          const newCurrentAgent = currentAgent?.id === id 
            ? null 
            : currentAgent;
          
          set({
            agents: updatedAgents,
            currentAgent: newCurrentAgent,
            isDeleting: false,
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to delete agent';
          set({
            isDeleting: false,
            error: errorMessage,
          });
          throw error;
        }
      },

      // Duplicate agent
      duplicateAgent: async (id: string, data: AgentDuplicateData) => {
        set({ isCreating: true, error: null });
        
        try {
          const response = await api.post(`/agents/${id}/duplicate`, data);
          const duplicatedAgent = response.data;
          
          // Add to agents list
          const currentAgents = get().agents;
          set({
            agents: [duplicatedAgent, ...currentAgents],
            isCreating: false,
          });
          
          return duplicatedAgent;
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to duplicate agent';
          set({
            isCreating: false,
            error: errorMessage,
          });
          throw error;
        }
      },

      // Set current agent
      setCurrentAgent: (agent: Agent | null) => {
        set({ currentAgent: agent });
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
    }),
    {
      name: 'agent-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        currentAgent: state.currentAgent,
      }),
    }
  )
);

// Selectors for common use cases
export const selectAgents = (state: AgentState) => state.agents;
export const selectCurrentAgent = (state: AgentState) => state.currentAgent;
export const selectAgentById = (state: AgentState, id: string) => 
  state.agents.find(agent => agent.id === id);
export const selectAgentsByWorkspace = (state: AgentState, workspaceId: string) => 
  state.agents.filter(agent => agent.workspace_id === workspaceId);

// Helper functions
export const canEditAgent = (agent: Agent | null, userWorkspaceRole?: string): boolean => {
  if (!agent) return false;
  return userWorkspaceRole === 'owner' || userWorkspaceRole === 'admin';
};

export const canDeleteAgent = (agent: Agent | null, userWorkspaceRole?: string, userId?: string): boolean => {
  if (!agent || !userId) return false;
  return userWorkspaceRole === 'owner' || agent.created_by === userId;
};

export const getAgentStatus = (agent: Agent): 'active' | 'inactive' | 'draft' => {
  if (!agent.is_active) return 'inactive';
  if (!agent.graph_json || Object.keys(agent.graph_json).length === 0) return 'draft';
  return 'active';
};

export const getAgentStatusColor = (status: 'active' | 'inactive' | 'draft'): string => {
  switch (status) {
    case 'active':
      return 'bg-green-100 text-green-800';
    case 'inactive':
      return 'bg-gray-100 text-gray-800';
    case 'draft':
      return 'bg-yellow-100 text-yellow-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};