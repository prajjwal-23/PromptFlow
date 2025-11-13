/**
 * Output Node Component
 * 
 * This component represents an output node in the workflow.
 */

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

interface OutputNodeData {
  label: string;
  config: {
    outputType: string;
    format: string;
  };
}

export const OutputNode = memo(({ data, selected }: NodeProps<OutputNodeData>) => {
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
        id="value"
        className="w-3 h-3 bg-amber-500 border-2 border-white"
      />

      {/* Node Header */}
      <div className="flex items-center mb-2">
        <div className="w-8 h-8 bg-amber-100 rounded-lg flex items-center justify-center mr-2">
          <span className="text-sm">📤</span>
        </div>
        <div className="flex-1">
          <h3 className="text-sm font-medium text-gray-900">{label || 'Output'}</h3>
          <p className="text-xs text-gray-500">Result</p>
        </div>
      </div>

      {/* Node Content */}
      <div className="space-y-2">
        <div className="text-xs text-gray-600">
          <div className="flex items-center justify-between">
            <span>Type:</span>
            <span className="font-medium">{config?.outputType || 'text'}</span>
          </div>
        </div>

        <div className="text-xs text-gray-600">
          <div className="flex items-center justify-between">
            <span>Format:</span>
            <span className="font-medium">{config?.format || 'plain'}</span>
          </div>
        </div>
      </div>

      {/* Status Indicator */}
      <div className="mt-2 pt-2 border-t border-gray-100">
        <div className="flex items-center">
          <div className="w-2 h-2 bg-amber-500 rounded-full mr-1"></div>
          <span className="text-xs text-gray-500">Input</span>
        </div>
        <div className="mt-1">
          <span className="text-xs text-gray-400">value</span>
        </div>
      </div>
    </div>
  );
});

OutputNode.displayName = 'OutputNode';