/**
 * Dashboard Page
 * 
 * This is the main dashboard page that provides an overview of user's workspaces and agents.
 */
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '../../store/authStore';
import { useWorkspaceStore } from '../../store/workspaceStore';
import { useAgentStore } from '../../store/agentStore';
import { ProtectedRoute } from '../../components/ProtectedRoute';
import { WorkspaceCard } from '../../components/Workspace/WorkspaceCard';
import { AgentCard } from '../../components/Agent/AgentCard';
import {
  Plus,
  Monitor,
  User,
  LogOut,
  ChevronDown,
  FolderOpen,
  Bot,
  Zap,
  Users,
  Clock,
  Building2
} from 'lucide-react';

export default function DashboardPage() {
  const router = useRouter();
  const { user, logout } = useAuthStore();
  const {
    workspaces,
    isLoading: workspaceLoading,
    fetchWorkspaces,
  } = useWorkspaceStore();
  
  const {
    agents,
    isLoading: agentLoading,
    fetchAgents,
  } = useAgentStore();

  const [activeTab, setActiveTab] = useState<'overview' | 'workspaces' | 'agents'>('overview');
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);

  useEffect(() => {
    fetchWorkspaces();
    fetchAgents();
  }, [fetchWorkspaces, fetchAgents]);

  const handleWorkspaceClick = (workspaceId: string) => {
    router.push(`/workspaces/${workspaceId}`);
  };

  const handleAgentClick = (agentId: string) => {
    router.push(`/agents/${agentId}/edit`);
  };

  const handleCreateWorkspace = () => {
    router.push('/create-workspace');
  };

  const handleCreateAgent = () => {
    router.push('/create-agent');
  };

  const handleLogout = async () => {
    try {
      await logout();
      router.push('/login');
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  const recentWorkspaces = workspaces.slice(0, 3);
  const recentAgents = agents.slice(0, 6);

  if (workspaceLoading || agentLoading) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading dashboard...</p>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
                <p className="text-sm text-gray-500">Welcome back, {user?.full_name}</p>
              </div>
              
              <div className="flex items-center space-x-4">
                <button
                  onClick={handleCreateWorkspace}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  New Workspace
                </button>
                 
                <button
                  onClick={handleCreateAgent}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
                >
                  <Bot className="w-4 h-4 mr-2" />
                  New Agent
                </button>
                
                {/* Profile Dropdown */}
                <div className="relative">
                  <button
                    className="flex items-center p-2 rounded-full hover:bg-gray-100 transition-colors"
                    onClick={() => setShowProfileDropdown(!showProfileDropdown)}
                  >
                    <div className="h-8 w-8 rounded-full bg-gray-200 flex items-center justify-center">
                      <span className="text-sm font-medium text-gray-700">
                        {user?.full_name?.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <ChevronDown className="ml-2 h-4 w-4 text-gray-500" />
                  </button>
                  
                  {showProfileDropdown && (
                    <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-200 z-50">
                      <div className="py-1">
                        <div className="px-4 py-2 border-b border-gray-100">
                          <div className="flex items-center px-3 py-2">
                            <User className="h-5 w-5 text-gray-400" />
                            <span className="ml-3 text-sm font-medium">Profile</span>
                          </div>
                        </div>
                        
                        <div className="px-4 py-2 hover:bg-gray-50 cursor-pointer">
                          <button
                            onClick={() => router.push('/profile')}
                            className="flex items-center w-full text-left text-sm text-gray-700 hover:text-primary"
                          >
                            <User className="mr-3 h-4 w-4 text-gray-400" />
                            View Profile
                          </button>
                        </div>
                        
                        <div className="px-4 py-2 hover:bg-gray-50 cursor-pointer">
                          <button
                            onClick={handleLogout}
                            className="flex items-center w-full text-left text-sm text-gray-700 hover:text-red-600"
                          >
                            <LogOut className="mr-3 h-4 w-4 text-gray-400" />
                            Logout
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <nav className="flex space-x-8">
              <button
                onClick={() => setActiveTab('overview')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'overview'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Overview
              </button>
              <button
                onClick={() => setActiveTab('workspaces')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'workspaces'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Workspaces ({workspaces.length})
              </button>
              <button
                onClick={() => setActiveTab('agents')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'agents'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Agents ({agents.length})
              </button>
            </nav>
          </div>
        </div>

        {/* Content */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {activeTab === 'overview' && (
            <div className="space-y-8">
              {/* Stats Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="bg-white p-6 rounded-lg shadow">
                  <div className="flex items-center">
                    <div className="p-3 bg-blue-100 rounded-lg">
                      <FolderOpen className="w-6 h-6 text-blue-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Total Workspaces</p>
                      <p className="text-2xl font-bold text-gray-900">{workspaces.length}</p>
                    </div>
                  </div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow">
                  <div className="flex items-center">
                    <div className="p-3 bg-green-100 rounded-lg">
                      <Bot className="w-6 h-6 text-green-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Total Agents</p>
                      <p className="text-2xl font-bold text-gray-900">{agents.length}</p>
                    </div>
                  </div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow">
                  <div className="flex items-center">
                    <div className="p-3 bg-purple-100 rounded-lg">
                      <Zap className="w-6 h-6 text-purple-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Active Workflows</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {agents.filter(a => a.is_active).length}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow">
                  <div className="flex items-center">
                    <div className="p-3 bg-orange-100 rounded-lg">
                      <Users className="w-6 h-6 text-orange-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Team Members</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {workspaces.reduce((total, ws) => total + ws.member_count, 0)}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Recent Workspaces */}
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-medium text-gray-900">Recent Workspaces</h2>
                  <button
                    onClick={() => setActiveTab('workspaces')}
                    className="text-sm text-primary hover:text-primary/80"
                  >
                    View all
                  </button>
                </div>
                
                {recentWorkspaces.length === 0 ? (
                  <div className="bg-white p-8 rounded-lg shadow text-center">
                    <FolderOpen className="mx-auto h-12 w-12 text-gray-400" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No workspaces yet</h3>
                    <p className="mt-1 text-sm text-gray-500">Create your first workspace to get started</p>
                    <div className="mt-6">
                      <button
                        onClick={handleCreateWorkspace}
                        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary hover:bg-primary/90"
                      >
                        Create Workspace
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {recentWorkspaces.map((workspace) => (
                      <WorkspaceCard
                        key={workspace.id}
                        workspace={workspace}
                        onClick={() => handleWorkspaceClick(workspace.id)}
                      />
                    ))}
                  </div>
                )}
              </div>

              {/* Recent Agents */}
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-medium text-gray-900">Recent Agents</h2>
                  <button
                    onClick={() => setActiveTab('agents')}
                    className="text-sm text-primary hover:text-primary/80"
                  >
                    View all
                  </button>
                </div>
                
                {recentAgents.length === 0 ? (
                  <div className="bg-white p-8 rounded-lg shadow text-center">
                    <Bot className="mx-auto h-12 w-12 text-gray-400" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No agents yet</h3>
                    <p className="mt-1 text-sm text-gray-500">Create your first AI agent to get started</p>
                    <div className="mt-6">
                      <button
                        onClick={handleCreateAgent}
                        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary hover:bg-primary/90"
                      >
                        Create Agent
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {recentAgents.map((agent) => (
                      <AgentCard
                        key={agent.id}
                        agent={agent}
                        onClick={() => handleAgentClick(agent.id)}
                      />
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'workspaces' && (
            <div>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-gray-900">All Workspaces</h2>
                <button
                  onClick={handleCreateWorkspace}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary hover:bg-primary/90"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Create Workspace
                </button>
              </div>
              
              {workspaces.length === 0 ? (
                <div className="bg-white p-8 rounded-lg shadow text-center">
                  <FolderOpen className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No workspaces yet</h3>
                  <p className="mt-1 text-sm text-gray-500">Create your first workspace to get started</p>
                  <div className="mt-6">
                    <button
                      onClick={handleCreateWorkspace}
                      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary hover:bg-primary/90"
                    >
                      Create Workspace
                    </button>
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {workspaces.map((workspace) => (
                    <WorkspaceCard
                      key={workspace.id}
                      workspace={workspace}
                      onClick={() => handleWorkspaceClick(workspace.id)}
                    />
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'agents' && (
            <div>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-gray-900">All Agents</h2>
                <button
                  onClick={handleCreateAgent}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary hover:bg-primary/90"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Create Agent
                </button>
              </div>
              
              {agents.length === 0 ? (
                <div className="bg-white p-8 rounded-lg shadow text-center">
                  <Bot className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No agents yet</h3>
                  <p className="mt-1 text-sm text-gray-500">Create your first AI agent to get started</p>
                  <div className="mt-6">
                    <button
                      onClick={handleCreateAgent}
                      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary hover:bg-primary/90"
                    >
                      Create Agent
                    </button>
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {agents.map((agent) => (
                    <AgentCard
                      key={agent.id}
                      agent={agent}
                      onClick={() => handleAgentClick(agent.id)}
                    />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
}