/**
 * Workspace List Component
 * 
 * This component displays a list of workspaces with filtering and search capabilities.
 */

import { useState, useMemo } from 'react';
import { Workspace } from '../../store/workspaceStore';
import { WorkspaceCard } from './WorkspaceCard';

interface WorkspaceListProps {
  workspaces: Workspace[];
  isLoading?: boolean;
  onWorkspaceClick: (workspaceId: string) => void;
  onWorkspaceEdit?: (workspace: Workspace) => void;
  onWorkspaceDelete?: (workspace: Workspace) => void;
  showActions?: boolean;
}

export function WorkspaceList({
  workspaces,
  isLoading = false,
  onWorkspaceClick,
  onWorkspaceEdit,
  onWorkspaceDelete,
  showActions = true,
}: WorkspaceListProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'name' | 'created_at' | 'updated_at'>('updated_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Filter and sort workspaces
  const filteredAndSortedWorkspaces = useMemo(() => {
    let filtered = workspaces;

    // Search filtering
    if (searchTerm) {
      filtered = filtered.filter(workspace =>
        workspace.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (workspace.description && workspace.description.toLowerCase().includes(searchTerm.toLowerCase()))
      );
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
  }, [workspaces, searchTerm, sortBy, sortOrder]);

  const handleSort = (field: 'name' | 'created_at' | 'updated_at') => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

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
              Search workspaces
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
                placeholder="Search workspaces..."
              />
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
          Showing {filteredAndSortedWorkspaces.length} of {workspaces.length} workspaces
        </p>
      </div>

      {/* Workspaces Grid */}
      {filteredAndSortedWorkspaces.length === 0 ? (
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
              d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">
            {searchTerm ? 'No matching workspaces' : 'No workspaces'}
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            {searchTerm 
              ? 'Try adjusting your search terms'
              : 'Get started by creating your first workspace.'
            }
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {filteredAndSortedWorkspaces.map((workspace) => (
            <WorkspaceCard
              key={workspace.id}
              workspace={workspace}
              onClick={() => onWorkspaceClick(workspace.id)}
              onEdit={onWorkspaceEdit ? () => onWorkspaceEdit(workspace) : undefined}
              onDelete={onWorkspaceDelete ? () => onWorkspaceDelete(workspace) : undefined}
              showActions={showActions}
            />
          ))}
        </div>
      )}
    </div>
  );
}