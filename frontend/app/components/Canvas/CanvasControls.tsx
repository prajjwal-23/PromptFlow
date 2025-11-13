/**
 * Canvas Controls Component
 * 
 * This component provides controls for canvas operations like save, undo, redo, etc.
 */

import { useCallback } from 'react';
import { useCanvasStore, selectCanUndo, selectCanRedo } from '../../store/canvasStore';

interface CanvasControlsProps {
  onSave?: (agentId?: string) => Promise<void>;
  agentId?: string;
}

export function CanvasControls({ onSave, agentId }: CanvasControlsProps) {
  const {
    nodes,
    edges,
    isSaving,
    error,
    clearError,
    undo,
    redo,
    clearCanvas,
    saveGraph,
  } = useCanvasStore();

  const canUndo = selectCanUndo(useCanvasStore.getState());
  const canRedo = selectCanRedo(useCanvasStore.getState());

  const handleSave = useCallback(async () => {
    if (onSave) {
      await onSave(agentId);
    } else {
      await saveGraph(agentId);
    }
  }, [onSave, agentId, saveGraph]);

  const handleUndo = useCallback(() => {
    undo();
  }, [undo]);

  const handleRedo = useCallback(() => {
    redo();
  }, [redo]);

  const handleClear = useCallback(() => {
    if (window.confirm('Are you sure you want to clear the entire canvas? This action cannot be undone.')) {
      clearCanvas();
    }
  }, [clearCanvas]);

  const handleExport = useCallback(() => {
    const graphData = {
      nodes,
      edges,
      metadata: {
        exportedAt: new Date().toISOString(),
        version: '1.0',
      },
    };

    const dataStr = JSON.stringify(graphData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `agent-workflow-${agentId || 'export'}-${Date.now()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, [nodes, edges, agentId]);

  return (
    <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-2 flex items-center space-x-2">
      {/* Undo/Redo */}
      <div className="flex items-center space-x-1 border-r border-gray-200 pr-2">
        <button
          onClick={handleUndo}
          disabled={!canUndo}
          className="p-2 text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed rounded"
          title="Undo (Ctrl+Z)"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6"
            />
          </svg>
        </button>
        <button
          onClick={handleRedo}
          disabled={!canRedo}
          className="p-2 text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed rounded"
          title="Redo (Ctrl+Y)"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 10h-10a8 8 0 00-8 8v2M21 10l-6 6m6-6l-6-6"
            />
          </svg>
        </button>
      </div>

      {/* Canvas Operations */}
      <div className="flex items-center space-x-1 border-r border-gray-200 pr-2">
        <button
          onClick={handleClear}
          className="p-2 text-gray-600 hover:text-gray-900 rounded"
          title="Clear Canvas"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
            />
          </svg>
        </button>
        <button
          onClick={handleExport}
          className="p-2 text-gray-600 hover:text-gray-900 rounded"
          title="Export Workflow"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
            />
          </svg>
        </button>
      </div>

      {/* Save */}
      <button
        onClick={handleSave}
        disabled={isSaving}
        className="px-3 py-1.5 bg-primary text-white text-sm font-medium rounded hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-1"
        title="Save Workflow"
      >
        {isSaving ? (
          <>
            <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            <span>Saving...</span>
          </>
        ) : (
          <>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V2"
              />
            </svg>
            <span>Save</span>
          </>
        )}
      </button>

      {/* Status */}
      <div className="flex items-center space-x-2 text-sm text-gray-600 border-l border-gray-200 pl-2">
        <div className="flex items-center space-x-1">
          <div className="w-2 h-2 bg-green-500 rounded-full"></div>
          <span>{nodes.length} nodes</span>
        </div>
        <div className="flex items-center space-x-1">
          <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
          <span>{edges.length} connections</span>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="absolute top-full mt-2 left-0 right-0 bg-red-50 border border-red-200 rounded-lg p-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <svg className="w-4 h-4 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
              <span className="text-sm text-red-800">{error}</span>
            </div>
            <button
              onClick={clearError}
              className="text-red-500 hover:text-red-700"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}