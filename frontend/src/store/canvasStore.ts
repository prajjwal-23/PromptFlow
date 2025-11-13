/**
 * Canvas state management using Zustand.
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { Node, Edge, Connection } from 'reactflow';

// Types
export interface CanvasState {
  // State
  nodes: Node[];
  edges: Edge[];
  selectedNode: Node | null;
  showProperties: boolean;
  isLoading: boolean;
  isSaving: boolean;
  error: string | null;
  history: {
    nodes: Node[];
    edges: Edge[];
  }[];
  historyIndex: number;

  // Actions
  setNodes: (nodes: Node[]) => void;
  setEdges: (edges: Edge[]) => void;
  onNodesChange: (changes: any) => void;
  onEdgesChange: (changes: any) => void;
  onConnect: (connection: Connection) => void;
  setSelectedNode: (node: Node | null) => void;
  setShowProperties: (show: boolean) => void;
  addNode: (type: string, position: { x: number; y: number }) => void;
  updateNodeData: (nodeId: string, data: any) => void;
  deleteNode: (nodeId: string) => void;
  duplicateNode: (nodeId: string) => void;
  
  // History management
  undo: () => void;
  redo: () => void;
  saveToHistory: () => void;
  
  // Graph operations
  clearCanvas: () => void;
  loadGraph: (graph: { nodes: Node[]; edges: Edge[] }) => void;
  saveGraph: (agentId?: string) => Promise<void>;
  
  // Utility
  clearError: () => void;
  reset: () => void;
}

// Node type configurations
export const nodeTypes = {
  input: {
    type: 'input',
    label: 'Input',
    description: 'Start point for user input',
    color: '#10b981',
    icon: '📝',
    inputs: [],
    outputs: ['value'],
  },
  llm: {
    type: 'llm',
    label: 'LLM',
    description: 'Large Language Model processing',
    color: '#3b82f6',
    icon: '🤖',
    inputs: ['prompt', 'context'],
    outputs: ['response'],
  },
  retrieval: {
    type: 'retrieval',
    label: 'Retrieval',
    description: 'Retrieve information from knowledge base',
    color: '#8b5cf6',
    icon: '🔍',
    inputs: ['query'],
    outputs: ['documents'],
  },
  output: {
    type: 'output',
    label: 'Output',
    description: 'End point for results',
    color: '#f59e0b',
    icon: '📤',
    inputs: ['value'],
    outputs: [],
  },
  tool: {
    type: 'tool',
    label: 'Tool',
    description: 'External tool or API integration',
    color: '#ef4444',
    icon: '🔧',
    inputs: ['input'],
    outputs: ['result'],
  },
};

const initialState = {
  nodes: [],
  edges: [],
  selectedNode: null,
  showProperties: false,
  isLoading: false,
  isSaving: false,
  error: null,
  history: [],
  historyIndex: -1,
};

export const useCanvasStore = create<CanvasState>()(
  persist(
    (set, get) => ({
      ...initialState,

      // Set nodes
      setNodes: (nodes: Node[]) => {
        set({ nodes });
      },

      // Set edges
      setEdges: (edges: Edge[]) => {
        set({ edges });
      },

      // Handle nodes changes
      onNodesChange: (changes: any) => {
        const { nodes, saveToHistory } = get();
        const updatedNodes = applyNodeChanges(changes, nodes);
        set({ nodes: updatedNodes });
        
        // Save to history for significant changes
        if (changes.some((change: any) => change.type === 'remove' || change.type === 'add')) {
          saveToHistory();
        }
      },

      // Handle edges changes
      onEdgesChange: (changes: any) => {
        const { edges, saveToHistory } = get();
        const updatedEdges = applyEdgeChanges(changes, edges);
        set({ edges: updatedEdges });
        
        // Save to history for significant changes
        if (changes.some((change: any) => change.type === 'remove' || change.type === 'add')) {
          saveToHistory();
        }
      },

      // Handle new connections
      onConnect: (connection: Connection) => {
        const { edges, saveToHistory } = get();
        const newEdge = {
          id: `edge-${Date.now()}`,
          source: connection.source!,
          target: connection.target!,
          sourceHandle: connection.sourceHandle,
          targetHandle: connection.targetHandle,
          type: 'default',
          animated: true,
        };
        
        const updatedEdges = [...edges, newEdge];
        set({ edges: updatedEdges });
        saveToHistory();
      },

      // Set selected node
      setSelectedNode: (node: Node | null) => {
        set({ selectedNode: node });
      },

      // Show/hide properties panel
      setShowProperties: (show: boolean) => {
        set({ showProperties: show });
      },

      // Add new node
      addNode: (type: string, position: { x: number; y: number }) => {
        const { nodes, saveToHistory } = get();
        const nodeConfig = nodeTypes[type as keyof typeof nodeTypes];
        
        if (!nodeConfig) {
          console.error(`Unknown node type: ${type}`);
          return;
        }

        const newNode: Node = {
          id: `${type}-${Date.now()}`,
          type,
          position,
          data: {
            label: nodeConfig.label,
            config: getDefaultNodeConfig(type),
          },
        };

        const updatedNodes = [...nodes, newNode];
        set({ nodes: updatedNodes, selectedNode: newNode, showProperties: true });
        saveToHistory();
      },

      // Update node data
      updateNodeData: (nodeId: string, data: any) => {
        const { nodes } = get();
        const updatedNodes = nodes.map((node) =>
          node.id === nodeId
            ? { ...node, data: { ...node.data, ...data } }
            : node
        );
        set({ nodes: updatedNodes });
      },

      // Delete node
      deleteNode: (nodeId: string) => {
        const { nodes, edges, saveToHistory } = get();
        const updatedNodes = nodes.filter((node) => node.id !== nodeId);
        const updatedEdges = edges.filter(
          (edge) => edge.source !== nodeId && edge.target !== nodeId
        );
        
        set({ 
          nodes: updatedNodes, 
          edges: updatedEdges, 
          selectedNode: null, 
          showProperties: false 
        });
        saveToHistory();
      },

      // Duplicate node
      duplicateNode: (nodeId: string) => {
        const { nodes, edges, saveToHistory } = get();
        const nodeToDuplicate = nodes.find((node) => node.id === nodeId);
        
        if (!nodeToDuplicate) return;

        const duplicatedNode: Node = {
          ...nodeToDuplicate,
          id: `${nodeToDuplicate.type}-${Date.now()}`,
          position: {
            x: nodeToDuplicate.position.x + 50,
            y: nodeToDuplicate.position.y + 50,
          },
        };

        const updatedNodes = [...nodes, duplicatedNode];
        set({ nodes: updatedNodes, selectedNode: duplicatedNode, showProperties: true });
        saveToHistory();
      },

      // Undo
      undo: () => {
        const { history, historyIndex } = get();
        if (historyIndex > 0) {
          const newIndex = historyIndex - 1;
          const { nodes, edges } = history[newIndex];
          set({ 
            nodes, 
            edges, 
            historyIndex: newIndex 
          });
        }
      },

      // Redo
      redo: () => {
        const { history, historyIndex } = get();
        if (historyIndex < history.length - 1) {
          const newIndex = historyIndex + 1;
          const { nodes, edges } = history[newIndex];
          set({ 
            nodes, 
            edges, 
            historyIndex: newIndex 
          });
        }
      },

      // Save to history
      saveToHistory: () => {
        const { nodes, edges, history, historyIndex } = get();
        const newHistory = history.slice(0, historyIndex + 1);
        newHistory.push({ nodes: [...nodes], edges: [...edges] });
        
        // Limit history size
        if (newHistory.length > 50) {
          newHistory.shift();
        }
        
        set({ 
          history: newHistory, 
          historyIndex: newHistory.length - 1 
        });
      },

      // Clear canvas
      clearCanvas: () => {
        set({ 
          nodes: [], 
          edges: [], 
          selectedNode: null, 
          showProperties: false 
        });
        get().saveToHistory();
      },

      // Load graph
      loadGraph: (graph: { nodes: Node[]; edges: Edge[] }) => {
        set({ 
          nodes: graph.nodes, 
          edges: graph.edges, 
          selectedNode: null, 
          showProperties: false 
        });
        get().saveToHistory();
      },

      // Save graph
      saveGraph: async (agentId?: string) => {
        set({ isSaving: true, error: null });
        
        try {
          const { nodes, edges } = get();
          const graphData = {
            nodes,
            edges,
            metadata: {
              lastModified: new Date().toISOString(),
              version: '1.0',
            },
          };

          // This would be implemented to save to backend
          console.log('Saving graph:', graphData);
          
          // For now, just simulate saving
          await new Promise(resolve => setTimeout(resolve, 1000));
          
          set({ isSaving: false });
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Failed to save graph';
          set({ error: errorMessage, isSaving: false });
        }
      },

      // Clear error
      clearError: () => {
        set({ error: null });
      },

      // Reset store
      reset: () => {
        set(initialState);
      },
    }),
    {
      name: 'canvas-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        nodes: state.nodes,
        edges: state.edges,
      }),
    }
  )
);

// Helper functions
function applyNodeChanges(changes: any[], nodes: Node[]): Node[] {
  return changes.reduce((acc: Node[], change: any) => {
    switch (change.type) {
      case 'position':
        return acc.map((node: Node) =>
          node.id === change.id
            ? { ...node, position: change.position || node.position }
            : node
        );
      case 'remove':
        return acc.filter((node: Node) => node.id !== change.id);
      case 'add':
        return [...acc, change.item];
      default:
        return acc;
    }
  }, nodes);
}

function applyEdgeChanges(changes: any[], edges: Edge[]): Edge[] {
  return changes.reduce((acc: Edge[], change: any) => {
    switch (change.type) {
      case 'remove':
        return acc.filter((edge: Edge) => edge.id !== change.id);
      case 'add':
        return [...acc, change.item];
      default:
        return acc;
    }
  }, edges);
}

export function getDefaultNodeConfig(type: string): any {
  switch (type) {
    case 'input':
      return {
        inputType: 'text',
        placeholder: 'Enter your input...',
        required: true,
      };
    case 'llm':
      return {
        model: 'gpt-3.5-turbo',
        temperature: 0.7,
        maxTokens: 1000,
        systemPrompt: 'You are a helpful assistant.',
      };
    case 'retrieval':
      return {
        collection: 'default',
        maxResults: 5,
        similarityThreshold: 0.7,
      };
    case 'output':
      return {
        outputType: 'text',
        format: 'plain',
      };
    case 'tool':
      return {
        toolType: 'api',
        endpoint: '',
        method: 'POST',
      };
    default:
      return {};
  }
}

// Selectors
export const selectNodes = (state: CanvasState) => state.nodes;
export const selectEdges = (state: CanvasState) => state.edges;
export const selectSelectedNode = (state: CanvasState) => state.selectedNode;
export const selectCanUndo = (state: CanvasState) => state.historyIndex > 0;
export const selectCanRedo = (state: CanvasState) => state.historyIndex < state.history.length - 1;