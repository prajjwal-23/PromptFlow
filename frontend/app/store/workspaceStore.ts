/**
 * Workspace state management using Zustand.
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { api } from './authStore';

// Types
export interface Workspace {
  id: string;
  name: string;
  description: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
  role: 'owner' | 'admin' | 'member';
  member_count: number;
}

export interface WorkspaceMember {
  id: string;
  user_id: string;
  email: string;
  full_name: string;
  role: 'owner' | 'admin' | 'member';
  created_at: string;
}

export interface WorkspaceCreateData {
  name: string;
  description?: string;
}

export interface WorkspaceUpdateData {
  name?: string;
  description?: string;
}

export interface MemberCreateData {
  email: string;
  role?: 'owner' | 'admin' | 'member';
}

export interface WorkspaceState {
  // State
  workspaces: Workspace[];
  currentWorkspace: Workspace | null;
  workspaceMembers: WorkspaceMember[];
  isLoading: boolean;
  isCreating: boolean;
  isUpdating: boolean;
  error: string | null;

  // Actions
  fetchWorkspaces: () => Promise<void>;
  fetchWorkspace: (id: string) => Promise<void>;
  createWorkspace: (data: WorkspaceCreateData) => Promise<Workspace>;
  updateWorkspace: (id: string, data: WorkspaceUpdateData) => Promise<void>;
  deleteWorkspace: (id: string) => Promise<void>;
  setCurrentWorkspace: (workspace: Workspace | null) => void;
  
  // Member management
  fetchWorkspaceMembers: (workspaceId: string) => Promise<void>;
  addWorkspaceMember: (workspaceId: string, data: MemberCreateData) => Promise<void>;
  updateWorkspaceMember: (workspaceId: string, userId: string, role: 'owner' | 'admin' | 'member') => Promise<void>;
  removeWorkspaceMember: (workspaceId: string, userId: string) => Promise<void>;
  
  // Utility
  clearError: () => void;
  setLoading: (loading: boolean) => void;
  reset: () => void;
}

const initialState = {
  workspaces: [],
  currentWorkspace: null,
  workspaceMembers: [],
  isLoading: false,
  isCreating: false,
  isUpdating: false,
  error: null,
};

export const useWorkspaceStore = create<WorkspaceState>()(
  persist(
    (set, get) => ({
      ...initialState,

      // Fetch all workspaces for current user
      fetchWorkspaces: async () => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await api.get('/workspaces');
          const workspaces = response.data;
          
          set({
            workspaces,
            isLoading: false,
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to fetch workspaces';
          set({
            isLoading: false,
            error: errorMessage,
          });
          throw error;
        }
      },

      // Fetch single workspace
      fetchWorkspace: async (id: string) => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await api.get(`/workspaces/${id}`);
          const workspace = response.data;
          
          set({
            currentWorkspace: workspace,
            isLoading: false,
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to fetch workspace';
          set({
            isLoading: false,
            error: errorMessage,
          });
          throw error;
        }
      },

      // Create new workspace
      createWorkspace: async (data: WorkspaceCreateData) => {
        set({ isCreating: true, error: null });
        
        try {
          const response = await api.post('/workspaces', data);
          const newWorkspace = response.data;
          
          // Add to workspaces list
          const currentWorkspaces = get().workspaces;
          set({
            workspaces: [newWorkspace, ...currentWorkspaces],
            currentWorkspace: newWorkspace,
            isCreating: false,
          });
          
          return newWorkspace;
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to create workspace';
          set({
            isCreating: false,
            error: errorMessage,
          });
          throw error;
        }
      },

      // Update workspace
      updateWorkspace: async (id: string, data: WorkspaceUpdateData) => {
        set({ isUpdating: true, error: null });
        
        try {
          const response = await api.put(`/workspaces/${id}`, data);
          const updatedWorkspace = response.data;
          
          // Update in workspaces list
          const currentWorkspaces = get().workspaces;
          const updatedWorkspaces = currentWorkspaces.map(ws => 
            ws.id === id ? updatedWorkspace : ws
          );
          
          // Update current workspace if it matches
          const currentWorkspace = get().currentWorkspace;
          const newCurrentWorkspace = currentWorkspace?.id === id 
            ? updatedWorkspace 
            : currentWorkspace;
          
          set({
            workspaces: updatedWorkspaces,
            currentWorkspace: newCurrentWorkspace,
            isUpdating: false,
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to update workspace';
          set({
            isUpdating: false,
            error: errorMessage,
          });
          throw error;
        }
      },

      // Delete workspace
      deleteWorkspace: async (id: string) => {
        set({ isLoading: true, error: null });
        
        try {
          await api.delete(`/workspaces/${id}`);
          
          // Remove from workspaces list
          const currentWorkspaces = get().workspaces;
          const updatedWorkspaces = currentWorkspaces.filter(ws => ws.id !== id);
          
          // Clear current workspace if it matches
          const currentWorkspace = get().currentWorkspace;
          const newCurrentWorkspace = currentWorkspace?.id === id 
            ? null 
            : currentWorkspace;
          
          set({
            workspaces: updatedWorkspaces,
            currentWorkspace: newCurrentWorkspace,
            isLoading: false,
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to delete workspace';
          set({
            isLoading: false,
            error: errorMessage,
          });
          throw error;
        }
      },

      // Set current workspace
      setCurrentWorkspace: (workspace: Workspace | null) => {
        set({ currentWorkspace: workspace });
      },

      // Fetch workspace members
      fetchWorkspaceMembers: async (workspaceId: string) => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await api.get(`/workspaces/${workspaceId}/members`);
          const members = response.data;
          
          set({
            workspaceMembers: members,
            isLoading: false,
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to fetch workspace members';
          set({
            isLoading: false,
            error: errorMessage,
          });
          throw error;
        }
      },

      // Add workspace member
      addWorkspaceMember: async (workspaceId: string, data: MemberCreateData) => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await api.post(`/workspaces/${workspaceId}/members`, data);
          const newMember = response.data;
          
          // Add to members list
          const currentMembers = get().workspaceMembers;
          set({
            workspaceMembers: [newMember, ...currentMembers],
            isLoading: false,
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to add workspace member';
          set({
            isLoading: false,
            error: errorMessage,
          });
          throw error;
        }
      },

      // Update workspace member role
      updateWorkspaceMember: async (workspaceId: string, userId: string, role: 'owner' | 'admin' | 'member') => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await api.put(`/workspaces/${workspaceId}/members/${userId}`, { role });
          const updatedMember = response.data;
          
          // Update in members list
          const currentMembers = get().workspaceMembers;
          const updatedMembers = currentMembers.map(member => 
            member.user_id === userId ? updatedMember : member
          );
          
          set({
            workspaceMembers: updatedMembers,
            isLoading: false,
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to update workspace member';
          set({
            isLoading: false,
            error: errorMessage,
          });
          throw error;
        }
      },

      // Remove workspace member
      removeWorkspaceMember: async (workspaceId: string, userId: string) => {
        set({ isLoading: true, error: null });
        
        try {
          await api.delete(`/workspaces/${workspaceId}/members/${userId}`);
          
          // Remove from members list
          const currentMembers = get().workspaceMembers;
          const updatedMembers = currentMembers.filter(member => member.user_id !== userId);
          
          set({
            workspaceMembers: updatedMembers,
            isLoading: false,
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to remove workspace member';
          set({
            isLoading: false,
            error: errorMessage,
          });
          throw error;
        }
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
      name: 'workspace-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        currentWorkspace: state.currentWorkspace,
      }),
    }
  )
);

// Selectors for common use cases
export const selectWorkspaces = (state: WorkspaceState) => state.workspaces;
export const selectCurrentWorkspace = (state: WorkspaceState) => state.currentWorkspace;
export const selectWorkspaceById = (state: WorkspaceState, id: string) => 
  state.workspaces.find(ws => ws.id === id);
export const selectWorkspaceMembers = (state: WorkspaceState) => state.workspaceMembers;

// Helper functions
export const canManageWorkspace = (workspace: Workspace | null, userWorkspaceRole?: string): boolean => {
  if (!workspace) return false;
  return workspace.role === 'owner' || workspace.role === 'admin';
};

export const canDeleteWorkspace = (workspace: Workspace | null): boolean => {
  if (!workspace) return false;
  return workspace.role === 'owner';
};

export const canManageMembers = (workspace: Workspace | null): boolean => {
  if (!workspace) return false;
  return workspace.role === 'owner' || workspace.role === 'admin';
};