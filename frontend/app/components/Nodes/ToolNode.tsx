/**
 * Tool Node Component
 * 
 * This component represents a tool node in the workflow.
 */

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

interface ToolNodeData {
  label: string;
  config: {
    toolType: string;
    endpoint: string;
    method: string;
  };
}

export const ToolNode = memo(({ data, selected }: NodeProps<ToolNodeData>) => {
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
        id="input"
        className="w-3 h-3 bg-red-500 border-2 border-white"
      />

      {/* Output Handle */}
      <Handle
        type="source"
        position={Position.Right}
        id="result"
        className="w-3 h-3 bg-red-500 border-2 border-white"
      />

      {/* Node Header */}
      <div className="flex items-center mb-2">
        <div className="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center mr-2">
          <span className="text-sm">🔧</span>
        </div>
        <div className="flex-1">
          <h3 className="text-sm font-medium text-gray-900">{label || 'Tool'}</h3>
          <p className="text-xs text-gray-500">External Tool</p>
        </div>
      </div>

      {/* Node Content */}
      <div className="space-y-2">
        <div className="text-xs text-gray-600">
          <div className="flex items-center justify-between">
            <span>Type:</span>
            <span className="font-medium">{config?.toolType || 'api'}</span>
          </div>
        </div>

        <div className="text-xs text-gray-600">
          <div className="flex items-center justify-between">
            <span>Method:</span>
            <span className="font-medium">{config?.method || 'POST'}</span>
          </div>
        </div>

        {config?.endpoint && (
          <div className="text-xs text-gray-600">
            <div className="truncate">
              <span className="text-gray-400">Endpoint: </span>
              {config.endpoint.length > 25 
                ? config.endpoint.substring(0, 25) + '...' 
                : config.endpoint}
            </div>
          </div>
        )}
      </div>

      {/* Status Indicators */}
      <div className="mt-2 pt-2 border-t border-gray-100">
        <div className="flex justify-between">
          <div className="flex items-center">
            <div className="w-2 h-2 bg-red-500 rounded-full mr-1"></div>
            <span className="text-xs text-gray-500">Input</span>
          </div>
          <div className="flex items-center">
            <div className="w-2 h-2 bg-red-500 rounded-full mr-1"></div>
            <span className="text-xs text-gray-500">Output</span>
          </div>
        </div>
        <div className="flex justify-between mt-1">
          <span className="text-xs text-gray-400">input</span>
          <span className="text-xs text-gray-400">result</span>
        </div>
      </div>
    </div>
  );
});

ToolNode.displayName = 'ToolNode';