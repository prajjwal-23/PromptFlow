/**
 * Node Properties Component
 * 
 * This component displays and allows editing of selected node properties.
 */

import { useState, useEffect } from 'react';
import { Node } from 'reactflow';
import { nodeTypes } from '../../store/canvasStore';

interface NodePropertiesProps {
  node: Node;
  onClose: () => void;
  onUpdateNodeData: (nodeId: string, data: any) => void;
}

export function NodeProperties({ node, onClose, onUpdateNodeData }: NodePropertiesProps) {
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  const nodeTypeConfig = nodeTypes[node.type as keyof typeof nodeTypes];

  useEffect(() => {
    // Initialize form data with node's current data
    setFormData({
      label: node.data.label || '',
      config: node.data.config || {},
    });
  }, [node.data]);

  const handleChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      config: {
        ...prev.config,
        [field]: value,
      },
    }));

    // Clear errors when user starts typing
    if (formErrors[field]) {
      setFormErrors(prev => ({
        ...prev,
        [field]: '',
      }));
    }
  };

  const handleLabelChange = (value: string) => {
    setFormData(prev => ({
      ...prev,
      label: value,
    }));
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    // Validate based on node type
    switch (node.type) {
      case 'input':
        if (!formData.config.placeholder?.trim()) {
          errors.placeholder = 'Placeholder is required';
        }
        break;
      case 'llm':
        if (!formData.config.model?.trim()) {
          errors.model = 'Model selection is required';
        }
        if (formData.config.temperature && (formData.config.temperature < 0 || formData.config.temperature > 2)) {
          errors.temperature = 'Temperature must be between 0 and 2';
        }
        break;
      case 'retrieval':
        if (!formData.config.collection?.trim()) {
          errors.collection = 'Collection name is required';
        }
        if (formData.config.maxResults && (formData.config.maxResults < 1 || formData.config.maxResults > 100)) {
          errors.maxResults = 'Max results must be between 1 and 100';
        }
        break;
      case 'tool':
        if (!formData.config.endpoint?.trim()) {
          errors.endpoint = 'Endpoint URL is required';
        }
        break;
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSave = () => {
    if (!validateForm()) {
      return;
    }

    onUpdateNodeData(node.id, formData);
  };

  const renderConfigFields = () => {
    switch (node.type) {
      case 'input':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Input Type
              </label>
              <select
                value={formData.config.inputType || 'text'}
                onChange={(e) => handleChange('inputType', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
              >
                <option value="text">Text</option>
                <option value="textarea">Textarea</option>
                <option value="number">Number</option>
                <option value="email">Email</option>
                <option value="password">Password</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Placeholder Text
              </label>
              <input
                type="text"
                value={formData.config.placeholder || ''}
                onChange={(e) => handleChange('placeholder', e.target.value)}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-primary focus:border-primary ${
                  formErrors.placeholder ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="Enter placeholder text..."
              />
              {formErrors.placeholder && (
                <p className="mt-1 text-sm text-red-600">{formErrors.placeholder}</p>
              )}
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="required"
                checked={formData.config.required || false}
                onChange={(e) => handleChange('required', e.target.checked)}
                className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
              />
              <label htmlFor="required" className="ml-2 text-sm text-gray-700">
                Required field
              </label>
            </div>
          </>
        );

      case 'llm':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Model
              </label>
              <select
                value={formData.config.model || 'gpt-3.5-turbo'}
                onChange={(e) => handleChange('model', e.target.value)}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-primary focus:border-primary ${
                  formErrors.model ? 'border-red-300' : 'border-gray-300'
                }`}
              >
                <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                <option value="gpt-4">GPT-4</option>
                <option value="gpt-4-turbo">GPT-4 Turbo</option>
                <option value="claude-3-opus">Claude 3 Opus</option>
                <option value="claude-3-sonnet">Claude 3 Sonnet</option>
              </select>
              {formErrors.model && (
                <p className="mt-1 text-sm text-red-600">{formErrors.model}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Temperature: {formData.config.temperature || 0.7}
              </label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={formData.config.temperature || 0.7}
                onChange={(e) => handleChange('temperature', parseFloat(e.target.value))}
                className="w-full"
              />
              {formErrors.temperature && (
                <p className="mt-1 text-sm text-red-600">{formErrors.temperature}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max Tokens
              </label>
              <input
                type="number"
                min="1"
                max="4000"
                value={formData.config.maxTokens || 1000}
                onChange={(e) => handleChange('maxTokens', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                System Prompt
              </label>
              <textarea
                rows={4}
                value={formData.config.systemPrompt || ''}
                onChange={(e) => handleChange('systemPrompt', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
                placeholder="Enter system prompt..."
              />
            </div>
          </>
        );

      case 'retrieval':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Collection Name
              </label>
              <input
                type="text"
                value={formData.config.collection || ''}
                onChange={(e) => handleChange('collection', e.target.value)}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-primary focus:border-primary ${
                  formErrors.collection ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="Enter collection name..."
              />
              {formErrors.collection && (
                <p className="mt-1 text-sm text-red-600">{formErrors.collection}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max Results
              </label>
              <input
                type="number"
                min="1"
                max="100"
                value={formData.config.maxResults || 5}
                onChange={(e) => handleChange('maxResults', parseInt(e.target.value))}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-primary focus:border-primary ${
                  formErrors.maxResults ? 'border-red-300' : 'border-gray-300'
                }`}
              />
              {formErrors.maxResults && (
                <p className="mt-1 text-sm text-red-600">{formErrors.maxResults}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Similarity Threshold: {formData.config.similarityThreshold || 0.7}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={formData.config.similarityThreshold || 0.7}
                onChange={(e) => handleChange('similarityThreshold', parseFloat(e.target.value))}
                className="w-full"
              />
            </div>
          </>
        );

      case 'output':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Output Type
              </label>
              <select
                value={formData.config.outputType || 'text'}
                onChange={(e) => handleChange('outputType', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
              >
                <option value="text">Text</option>
                <option value="json">JSON</option>
                <option value="markdown">Markdown</option>
                <option value="html">HTML</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Format
              </label>
              <select
                value={formData.config.format || 'plain'}
                onChange={(e) => handleChange('format', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
              >
                <option value="plain">Plain</option>
                <option value="formatted">Formatted</option>
                <option value="structured">Structured</option>
              </select>
            </div>
          </>
        );

      case 'tool':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tool Type
              </label>
              <select
                value={formData.config.toolType || 'api'}
                onChange={(e) => handleChange('toolType', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
              >
                <option value="api">API Call</option>
                <option value="function">Function</option>
                <option value="webhook">Webhook</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Endpoint URL
              </label>
              <input
                type="url"
                value={formData.config.endpoint || ''}
                onChange={(e) => handleChange('endpoint', e.target.value)}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-primary focus:border-primary ${
                  formErrors.endpoint ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="https://api.example.com/endpoint"
              />
              {formErrors.endpoint && (
                <p className="mt-1 text-sm text-red-600">{formErrors.endpoint}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                HTTP Method
              </label>
              <select
                value={formData.config.method || 'POST'}
                onChange={(e) => handleChange('method', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
              >
                <option value="GET">GET</option>
                <option value="POST">POST</option>
                <option value="PUT">PUT</option>
                <option value="DELETE">DELETE</option>
              </select>
            </div>
          </>
        );

      default:
        return null;
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center text-lg"
              style={{ backgroundColor: `${nodeTypeConfig.color}20` }}
            >
              <span>{nodeTypeConfig.icon}</span>
            </div>
            <div>
              <h2 className="text-lg font-medium text-gray-900">Node Properties</h2>
              <p className="text-sm text-gray-500">{nodeTypeConfig.label}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-md"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* Form */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-6">
          {/* Basic Info */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Node Label
            </label>
            <input
              type="text"
              value={formData.label || ''}
              onChange={(e) => handleLabelChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
              placeholder="Enter node label..."
            />
          </div>

          {/* Configuration Fields */}
          <div>
            <h3 className="text-sm font-medium text-gray-900 mb-3">Configuration</h3>
            <div className="space-y-4">
              {renderConfigFields()}
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex space-x-3">
          <button
            onClick={handleSave}
            className="flex-1 px-4 py-2 bg-primary text-white font-medium rounded-md hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
          >
            Save Changes
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 text-gray-700 font-medium rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}