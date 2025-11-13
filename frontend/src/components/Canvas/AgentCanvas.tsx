/**
 * Agent Canvas Component
 * 
 * This is the main canvas component for building agent workflows using React Flow.
 */

import { useCallback, useMemo } from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Controls,
  MiniMap,
  Background,
  BackgroundVariant,
  Panel,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { useCanvasStore } from '../../store/canvasStore';
import { NodePalette } from './NodePalette';
import { CanvasControls } from './CanvasControls';
import { NodeProperties } from './NodeProperties';

// Import node types
import { InputNode } from '../Nodes/InputNode';
import { LLMNode } from '../Nodes/LLMNode';
import { RetrievalNode } from '../Nodes/RetrievalNode';
import { OutputNode } from '../Nodes/OutputNode';
import { ToolNode } from '../Nodes/ToolNode';

// Node type definitions
const nodeTypes = {
  input: InputNode,
  llm: LLMNode,
  retrieval: RetrievalNode,
  output: OutputNode,
  tool: ToolNode,
};

interface AgentCanvasProps {
  agentId?: string;
  readOnly?: boolean;
}

export function AgentCanvas({ agentId, readOnly = false }: AgentCanvasProps) {
  const {
    nodes,
    edges,
    selectedNode,
    showProperties,
    onNodesChange,
    onEdgesChange,
    onConnect,
    setSelectedNode,
    setShowProperties,
    addNode,
    updateNodeData,
    saveGraph,
  } = useCanvasStore();

  const [nodesState, setNodesState, onNodesChangeHandler] = useNodesState(nodes);
  const [edgesState, setEdgesState, onEdgesChangeHandler] = useEdgesState(edges);

  // Update store when nodes change
  const handleNodesChange = useCallback(
    (changes: any) => {
      onNodesChangeHandler(changes);
      onNodesChange(changes);
    },
    [onNodesChangeHandler, onNodesChange]
  );

  // Update store when edges change
  const handleEdgesChange = useCallback(
    (changes: any) => {
      onEdgesChangeHandler(changes);
      onEdgesChange(changes);
    },
    [onEdgesChangeHandler, onEdgesChange]
  );

  // Handle new connections
  const handleConnect = useCallback(
    (connection: Connection) => {
      onConnect(connection);
      setEdgesState((eds) => addEdge(connection, eds));
    },
    [onConnect, setEdgesState]
  );

  // Handle node selection
  const onNodeClick = useCallback(
    (event: React.MouseEvent, node: Node) => {
      if (!readOnly) {
        setSelectedNode(node);
        setShowProperties(true);
      }
    },
    [readOnly, setSelectedNode, setShowProperties]
  );

  // Handle pane click (deselect node)
  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
    setShowProperties(false);
  }, [setSelectedNode, setShowProperties]);

  // Handle node drag
  const onNodeDragStop = useCallback(
    (event: React.MouseEvent, node: Node) => {
      // Update node position in store
      updateNodeData(node.id, { position: node.position });
    },
    [updateNodeData]
  );

  // Add new node from palette
  const handleAddNode = useCallback(
    (nodeType: string, position: { x: number; y: number }) => {
      addNode(nodeType, position);
    },
    [addNode]
  );

  // Memoize flow props
  const flowProps = useMemo(() => ({
    nodes: nodesState,
    edges: edgesState,
    onNodesChange: handleNodesChange,
    onEdgesChange: handleEdgesChange,
    onConnect: handleConnect,
    onNodeClick,
    onPaneClick,
    onNodeDragStop,
    nodeTypes,
    deleteKeyCode: ['Backspace', 'Delete'],
    connectionLineStyle: { stroke: '#3b82f6', strokeWidth: 2 },
    snapToGrid: true,
    snapGrid: [20, 20] as [number, number],
    defaultViewport: { x: 0, y: 0, zoom: 1 },
    minZoom: 0.1,
    maxZoom: 2,
    fitView: true,
    attributionPosition: 'bottom-right' as const,
  }), [
    nodesState,
    edgesState,
    handleNodesChange,
    handleEdgesChange,
    handleConnect,
    onNodeClick,
    onPaneClick,
    onNodeDragStop,
    nodeTypes,
  ]);

  return (
    <div className="h-full w-full flex">
      {/* Node Palette */}
      {!readOnly && (
        <div className="w-64 bg-white border-r border-gray-200 flex-shrink-0">
          <NodePalette onAddNode={handleAddNode} />
        </div>
      )}

      {/* Main Canvas Area */}
      <div className="flex-1 relative">
        <ReactFlow {...flowProps}>
          <Background variant={BackgroundVariant.Dots} gap={20} size={1} />
          <Controls position="top-left" />
          <MiniMap 
            position="top-right"
            nodeColor={(node) => {
              switch (node.type) {
                case 'input': return '#10b981';
                case 'llm': return '#3b82f6';
                case 'retrieval': return '#8b5cf6';
                case 'output': return '#f59e0b';
                case 'tool': return '#ef4444';
                default: return '#6b7280';
              }
            }}
            maskColor="rgba(0, 0, 0, 0.1)"
          />
          
          {/* Custom Controls Panel */}
          {!readOnly && (
            <Panel position="bottom-center">
              <CanvasControls onSave={saveGraph} agentId={agentId} />
            </Panel>
          )}
        </ReactFlow>

        {/* Empty State */}
        {nodesState.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="text-center">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">Start building your workflow</h3>
              <p className="mt-1 text-sm text-gray-500">
                Drag nodes from the palette to begin creating your agent
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Node Properties Panel */}
      {!readOnly && showProperties && selectedNode && (
        <div className="w-80 bg-white border-l border-gray-200 flex-shrink-0">
          <NodeProperties
            node={selectedNode}
            onClose={() => setShowProperties(false)}
            onUpdateNodeData={updateNodeData}
          />
        </div>
      )}
    </div>
  );
}