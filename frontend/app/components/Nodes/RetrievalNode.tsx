/**
 * Retrieval Node Component
 * 
 * This component represents a retrieval node in the workflow.
 */

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

interface RetrievalNodeData {
  label: string;
  config: {
    collection: string;
    maxResults: number;
    similarityThreshold: number;
  };
}

export const RetrievalNode = memo(({ data, selected }: NodeProps<RetrievalNodeData>) => {
  const { label, config } = data;

  return (
    <div
      className={`px-4 py-3 shadow-md rounded-lg bg-white border-2 min-w-[200px] ${
        selected ? 'border-primary' : 'border-gray-200'
      }`}
    >
      {/* Input Handle */}
      <Handle
        type="target"
        position={Position.Left}
        id="query"
        className="w-3 h-3 bg-purple-500 border-2 border-white"
      />

      {/* Output Handle */}
      <Handle
        type="source"
        position={Position.Right}
        id="documents"
        className="w-3 h-3 bg-purple-500 border-2 border-white"
      />

      {/* Node Header */}
      <div className="flex items-center mb-2">
        <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center mr-2">
          <span className="text-sm">🔍</span>
        </div>
        <div className="flex-1">
          <h3 className="text-sm font-medium text-gray-900">{label || 'Retrieval'}</h3>
          <p className="text-xs text-gray-500">Knowledge Base</p>
        </div>
      </div>

      {/* Node Content */}
      <div className="space-y-2">
        <div className="text-xs text-gray-600">
          <div className="flex items-center justify-between">
            <span>Collection:</span>
            <span className="font-medium truncate max-w-[100px]" title={config?.collection || 'default'}>
              {config?.collection || 'default'}
            </span>
          </div>
        </div>

        <div className="text-xs text-gray-600">
          <div className="flex items-center justify-between">
            <span>Max Results:</span>
            <span className="font-medium">{config?.maxResults || 5}</span>
          </div>
        </div>

        <div className="text-xs text-gray-600">
          <div className="flex items-center justify-between">
            <span>Threshold:</span>
            <span className="font-medium">{config?.similarityThreshold || 0.7}</span>
          </div>
        </div>
      </div>

      {/* Status Indicators */}
      <div className="mt-2 pt-2 border-t border-gray-100">
        <div className="flex justify-between">
          <div className="flex items-center">
            <div className="w-2 h-2 bg-purple-500 rounded-full mr-1"></div>
            <span className="text-xs text-gray-500">Input</span>
          </div>
          <div className="flex items-center">
            <div className="w-2 h-2 bg-purple-500 rounded-full mr-1"></div>
            <span className="text-xs text-gray-500">Output</span>
          </div>
        </div>
        <div className="flex justify-between mt-1">
          <span className="text-xs text-gray-400">query</span>
          <span className="text-xs text-gray-400">documents</span>
        </div>
      </div>
    </div>
  );
});

RetrievalNode.displayName = 'RetrievalNode';