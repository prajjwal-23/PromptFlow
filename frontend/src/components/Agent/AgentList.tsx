/**
 * Agent List Component
 * 
 * This component displays a list of agents with filtering and search capabilities.
 */

import { useState, useMemo } from 'react';
import { Agent } from '../../store/agentStore';
import { getAgentStatus, getAgentStatusColor } from '../../store/agentStore';
import { AgentCard } from './AgentCard';

interface AgentListProps {
  agents: Agent[];
  isLoading?: boolean;
  onAgentClick: (agentId: string) => void;
  onAgentEdit?: (agent: Agent) => void;
  onAgentDelete?: (agent: Agent) => void;
  onAgentRun?: (agent: Agent) => void;
  onAgentDuplicate?: (agent: Agent) => void;
  showActions?: boolean;
}

export function AgentList({
  agents,
  isLoading = false,
  onAgentClick,
  onAgentEdit,
  onAgentDelete,
  onAgentRun,
  onAgentDuplicate,
  showActions = true,
}: AgentListProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'inactive' | 'draft'>('all');
  const [sortBy, setSortBy] = useState<'name' | 'created_at' | 'updated_at'>('updated_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Filter and sort agents
  const filteredAndSortedAgents = useMemo(() => {
    let filtered = agents;

    // Search filtering
    if (searchTerm) {
      filtered = filtered.filter(agent =>
        agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (agent.description && agent.description.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    // Status filtering
    if (filterStatus !== 'all') {
      filtered = filtered.filter(agent => {
        const status = getAgentStatus(agent);
        return status === filterStatus;
      });
    }

    // Sorting
    return filtered.sort((a, b) => {
      let comparison = 0;

      switch (sortBy) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'created_at':
          comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
          break;
        case 'updated_at':
          comparison = new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime();
          break;
      }

      return sortOrder === 'asc' ? comparison : -comparison;
    });
  }, [agents, searchTerm, filterStatus, sortBy, sortOrder]);

  const handleSort = (field: 'name' | 'created_at' | 'updated_at') => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  const getStatusCounts = () => {
    const counts = {
      all: agents.length,
      active: agents.filter(agent => getAgentStatus(agent) === 'active').length,
      inactive: agents.filter(agent => getAgentStatus(agent) === 'inactive').length,
      draft: agents.filter(agent => getAgentStatus(agent) === 'draft').length,
    };
    return counts;
  };

  const statusCounts = getStatusCounts();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Search and Filters */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex flex-col space-y-4 sm:flex-row sm:space-y-0 sm:space-x-4">
          {/* Search */}
          <div className="flex-1">
            <label htmlFor="search" className="sr-only">
              Search agents
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg
                  className="h-5 w-5 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
              </div>
              <input
                id="search"
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-primary focus:border-primary sm:text-sm"
                placeholder="Search agents..."
              />
            </div>
          </div>

          {/* Status Filters */}
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-500">Status:</span>
            <div className="flex rounded-md shadow-sm">
              {(['all', 'active', 'inactive', 'draft'] as const).map((status) => (
                <button
                  key={status}
                  onClick={() => setFilterStatus(status)}
                  className={`relative inline-flex items-center px-3 py-2 border text-sm font-medium focus:z-10 focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary ${
                    filterStatus === status
                      ? 'bg-primary text-white border-primary'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  } ${
                    status === 'all' ? 'rounded-l-md' : ''
                  } ${
                    status === 'draft' ? 'rounded-r-md' : ''
                  }`}
                >
                  {status.charAt(0).toUpperCase() + status.slice(1)}
                  <span className="ml-1 bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded text-xs">
                    {statusCounts[status]}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Sort Controls */}
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-500">Sort by:</span>
            <div className="flex rounded-md shadow-sm">
              <button
                onClick={() => handleSort('name')}
                className={`relative inline-flex items-center px-3 py-2 rounded-l-md border text-sm font-medium focus:z-10 focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary ${
                  sortBy === 'name'
                    ? 'bg-primary text-white border-primary'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                Name
                {sortBy === 'name' && (
                  <span className="ml-1">
                    {sortOrder === 'asc' ? '↑' : '↓'}
                  </span>
                )}
              </button>
              <button
                onClick={() => handleSort('created_at')}
                className={`relative -ml-px inline-flex items-center px-3 py-2 border text-sm font-medium focus:z-10 focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary ${
                  sortBy === 'created_at'
                    ? 'bg-primary text-white border-primary'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                Created
                {sortBy === 'created_at' && (
                  <span className="ml-1">
                    {sortOrder === 'asc' ? '↑' : '↓'}
                  </span>
                )}
              </button>
              <button
                onClick={() => handleSort('updated_at')}
                className={`relative -ml-px inline-flex items-center px-3 py-2 rounded-r-md border text-sm font-medium focus:z-10 focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary ${
                  sortBy === 'updated_at'
                    ? 'bg-primary text-white border-primary'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                Updated
                {sortBy === 'updated_at' && (
                  <span className="ml-1">
                    {sortOrder === 'asc' ? '↑' : '↓'}
                  </span>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Results Count */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500">
          Showing {filteredAndSortedAgents.length} of {agents.length} agents
        </p>
      </div>

      {/* Agents Grid */}
      {filteredAndSortedAgents.length === 0 ? (
        <div className="text-center py-12">
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
          <h3 className="mt-2 text-sm font-medium text-gray-900">
            {searchTerm || filterStatus !== 'all' ? 'No matching agents' : 'No agents'}
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            {searchTerm || filterStatus !== 'all'
              ? 'Try adjusting your search terms or filters'
              : 'Get started by creating your first agent.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {filteredAndSortedAgents.map((agent) => (
            <AgentCard
              key={agent.id}
              agent={agent}
              onClick={() => onAgentClick(agent.id)}
              onEdit={onAgentEdit ? () => onAgentEdit(agent) : undefined}
              onDelete={onAgentDelete ? () => onAgentDelete(agent) : undefined}
              onRun={onAgentRun ? () => onAgentRun(agent) : undefined}
              onDuplicate={onAgentDuplicate ? () => onAgentDuplicate(agent) : undefined}
              showActions={showActions}
            />
          ))}
        </div>
      )}
    </div>
  );
}