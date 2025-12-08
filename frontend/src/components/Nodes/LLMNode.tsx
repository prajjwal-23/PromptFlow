/**
 * LLM Node Component
 * 
 * This component represents a Large Language Model node in the workflow.
 */

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

interface LLMNodeData {
  label: string;
  config: {
    model: string;
    temperature: number;
    maxTokens: number;
    systemPrompt: string;
  };
}

export const LLMNode = memo(({ data, selected }: NodeProps<LLMNodeData>) => {
  const { label, config } = data;

  return (
    <div
      className={`px-4 py-3 shadow-md rounded-lg bg-background border-2 min-w-[200px] ${
        selected ? 'border-primary' : 'border-border'
      }`}
    >
      {/* Input Handles */}
      <Handle
        type="target"
        position={Position.Left}
        id="prompt"
        className="w-3 h-3 bg-primary border-2 border-background"
      />
      <Handle
        type="target"
        position={Position.Left}
        id="context"
        className="w-3 h-3 bg-primary border-2 border-background"
        style={{ top: '50%' }}
      />

      {/* Output Handle */}
      <Handle
        type="source"
        position={Position.Right}
        id="response"
        className="w-3 h-3 bg-primary border-2 border-background"
      />

      {/* Node Header */}
      <div className="flex items-center mb-2">
        <div className="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center mr-2">
          <span className="text-sm">🤖</span>
        </div>
        <div className="flex-1">
          <h3 className="text-sm font-medium text-foreground">{label || 'LLM'}</h3>
          <p className="text-xs text-muted-foreground">Language Model</p>
        </div>
      </div>

      {/* Node Content */}
      <div className="space-y-2">
        <div className="text-xs text-muted-foreground">
          <div className="flex items-center justify-between">
            <span>Model:</span>
            <span className="font-medium">{config?.model || 'gpt-3.5-turbo'}</span>
          </div>
        </div>

        <div className="text-xs text-muted-foreground">
          <div className="flex items-center justify-between">
            <span>Temperature:</span>
            <span className="font-medium">{config?.temperature || 0.7}</span>
          </div>
        </div>

        <div className="text-xs text-muted-foreground">
          <div className="flex items-center justify-between">
            <span>Max Tokens:</span>
            <span className="font-medium">{config?.maxTokens || 1000}</span>
          </div>
        </div>

        {config?.systemPrompt && (
          <div className="text-xs text-muted-foreground">
            <div className="truncate">
              <span className="text-muted-foreground/60">System: </span>
              {config.systemPrompt.length > 30 
                ? config.systemPrompt.substring(0, 30) + '...' 
                : config.systemPrompt}
            </div>
          </div>
        )}
      </div>

      {/* Status Indicators */}
      <div className="mt-2 pt-2 border-t border-border">
        <div className="flex justify-between">
          <div className="flex items-center">
            <div className="w-2 h-2 bg-primary rounded-full mr-1"></div>
            <span className="text-xs text-muted-foreground">Inputs</span>
          </div>
          <div className="flex items-center">
            <div className="w-2 h-2 bg-primary rounded-full mr-1"></div>
            <span className="text-xs text-muted-foreground">Output</span>
          </div>
        </div>
        <div className="flex justify-between mt-1">
          <span className="text-xs text-muted-foreground/60">prompt, context</span>
          <span className="text-xs text-muted-foreground/60">response</span>
        </div>
      </div>
    </div>
  );
});

LLMNode.displayName = 'LLMNode';