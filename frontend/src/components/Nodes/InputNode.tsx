/**
 * Input Node Component
 * 
 * This component represents an input node in the workflow.
 */

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

interface InputNodeData {
  label: string;
  config: {
    inputType: string;
    placeholder: string;
    required: boolean;
  };
}

export const InputNode = memo(({ data, selected }: NodeProps<InputNodeData>) => {
  const { label, config } = data;

  return (
    <div
      className={`px-4 py-3 shadow-md rounded-lg bg-background border-2 min-w-[200px] ${
        selected ? 'border-primary' : 'border-border'
      }`}
    >
      {/* Output Handle */}
      <Handle
        type="source"
        position={Position.Right}
        id="value"
        className="w-3 h-3 bg-success border-2 border-background"
      />

      {/* Node Header */}
      <div className="flex items-center mb-2">
        <div className="w-8 h-8 bg-success/10 rounded-lg flex items-center justify-center mr-2">
          <span className="text-sm">📝</span>
        </div>
        <div className="flex-1">
          <h3 className="text-sm font-medium text-foreground">{label || 'Input'}</h3>
          <p className="text-xs text-muted-foreground">User Input</p>
        </div>
      </div>

      {/* Node Content */}
      <div className="space-y-2">
        <div className="text-xs text-muted-foreground">
          <div className="flex items-center justify-between">
            <span>Type:</span>
            <span className="font-medium">{config?.inputType || 'text'}</span>
          </div>
        </div>

        {config?.placeholder && (
          <div className="text-xs text-muted-foreground">
            <div className="truncate">
              <span className="text-muted-foreground/60">Placeholder: </span>
              {config.placeholder}
            </div>
          </div>
        )}

        {config?.required && (
          <div className="flex items-center text-xs text-primary">
            <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            Required field
          </div>
        )}
      </div>

      {/* Status Indicator */}
      <div className="mt-2 pt-2 border-t border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <div className="w-2 h-2 bg-success rounded-full mr-1"></div>
            <span className="text-xs text-muted-foreground">Output</span>
          </div>
          <span className="text-xs text-muted-foreground/60">value</span>
        </div>
      </div>
    </div>
  );
});

InputNode.displayName = 'InputNode';