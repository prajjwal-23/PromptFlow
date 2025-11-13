/**
 * Node Palette Component
 * 
 * This component displays available node types that can be dragged onto the canvas.
 */

import { useCallback } from 'react';
import { nodeTypes } from '../../store/canvasStore';

interface NodePaletteProps {
  onAddNode: (nodeType: string, position: { x: number; y: number }) => void;
}

export function NodePalette({ onAddNode }: NodePaletteProps) {
  const handleDragStart = useCallback(
    (event: React.DragEvent, nodeType: string) => {
      event.dataTransfer.setData('application/reactflow', nodeType);
      event.dataTransfer.effectAllowed = 'move';
    },
    []
  );

  const handleNodeClick = useCallback(
    (nodeType: string) => {
      // Add node at a default position
      const position = { x: 300, y: 100 };
      onAddNode(nodeType, position);
    },
    [onAddNode]
  );

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-medium text-gray-900">Node Palette</h2>
        <p className="text-sm text-gray-500 mt-1">
          Drag or click to add nodes to your workflow
        </p>
      </div>

      {/* Node Types */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-4">
          {Object.entries(nodeTypes).map(([type, config]) => (
            <div
              key={type}
              className="group cursor-pointer"
              draggable
              onDragStart={(event) => handleDragStart(event, type)}
              onClick={() => handleNodeClick(type)}
            >
              <div className="p-3 border border-gray-200 rounded-lg hover:border-primary hover:shadow-md transition-all duration-200">
                <div className="flex items-center space-x-3">
                  {/* Node Icon */}
                  <div
                    className="flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center text-lg"
                    style={{ backgroundColor: `${config.color}20` }}
                  >
                    <span>{config.icon}</span>
                  </div>

                  {/* Node Info */}
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-medium text-gray-900 truncate">
                      {config.label}
                    </h3>
                    <p className="text-xs text-gray-500 mt-1">
                      {config.description}
                    </p>
                  </div>

                  {/* Add Button */}
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                    <button
                      className="p-1 text-primary hover:text-primary/80"
                      title={`Add ${config.label} node`}
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M12 4v16m8-8H4"
                        />
                      </svg>
                    </button>
                  </div>
                </div>

                {/* Input/Output Indicators */}
                <div className="mt-3 flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-2">
                    {config.inputs.length > 0 && (
                      <div className="flex items-center space-x-1">
                        <span className="text-gray-500">Inputs:</span>
                        <div className="flex space-x-1">
                          {config.inputs.map((input, index) => (
                            <div
                              key={index}
                              className="w-2 h-2 bg-blue-500 rounded-full"
                              title={input}
                            />
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="flex items-center space-x-2">
                    {config.outputs.length > 0 && (
                      <div className="flex items-center space-x-1">
                        <span className="text-gray-500">Outputs:</span>
                        <div className="flex space-x-1">
                          {config.outputs.map((output, index) => (
                            <div
                              key={index}
                              className="w-2 h-2 bg-green-500 rounded-full"
                              title={output}
                            />
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Help Section */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <h3 className="text-sm font-medium text-gray-900 mb-2">Quick Tips</h3>
        <ul className="text-xs text-gray-600 space-y-1">
          <li>• Drag nodes onto the canvas to add them</li>
          <li>• Click nodes to configure their properties</li>
          <li>• Connect nodes by dragging from output to input handles</li>
          <li>• Double-click connections to remove them</li>
          <li>• Use Ctrl+Z/Cmd+Z to undo changes</li>
        </ul>
      </div>
    </div>
  );
}