/**
 * Premium Dashboard Page with Three.js Animation
 * 
 * Industry-standard dashboard with immersive 3D background,
 * glass morphism effects, and smooth animations.
 */

'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { useAuthStore } from '../../store/authStore';
import { useWorkspaceStore } from '../../store/workspaceStore';
import { useAgentStore } from '../../store/agentStore';
import { ProtectedRoute } from '../../components/ProtectedRoute';
import { WorkspaceCard } from '../../components/Workspace/WorkspaceCard';
import { AgentCard } from '../../components/Agent/AgentCard';
// import { ThreeScene } from '@/components/Premium/Three/ThreeScene';
import { ThreeScene } from '../../components/Premium/Three/ThreeScene';
import {
  Plus,
  User,
  LogOut,
  ChevronDown,
  FolderOpen,
  Bot,
  Zap,
  Users,
  TrendingUp,
  Activity,
  Settings,
  BarChart3
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
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    fetchWorkspaces();
    fetchAgents();
    
    // Mouse tracking for interactive effects
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({
        x: (e.clientX / window.innerWidth) * 100,
        y: (e.clientY / window.innerHeight) * 100
      });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
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
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400 mx-auto"></div>
            <p className="mt-2 text-white/70">Loading premium dashboard...</p>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 relative overflow-hidden">
        {/* Three.js Background - Commented out for now due to TypeScript issues */}
        <ThreeScene />
        
        {/* Interactive background gradient */}
        <div 
          className="absolute inset-0 z-10 opacity-20"
          style={{
            background: `radial-gradient(circle at ${mousePosition.x}% ${mousePosition.y}%, rgba(79, 70, 229, 0.3) 0%, transparent 50%)`
          }}
        />

        {/* Glass morphism overlay */}
        <div className="absolute inset-0 z-20 bg-gradient-to-b from-transparent via-black/10 to-black/30" />

        {/* Header with glass effect */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="relative z-30"
        >
          <div className="bg-white/5 backdrop-blur-xl border-b border-white/10">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex items-center justify-between h-16">
                <div>
                  <h1 className="text-2xl font-bold text-white">Dashboard</h1>
                  <p className="text-sm text-white/70">Welcome back, {user?.full_name}</p>
                </div>
                
                <div className="flex items-center space-x-4">
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={handleCreateWorkspace}
                    className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white text-sm font-medium rounded-lg shadow-lg hover:shadow-xl transition-all duration-300"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    New Workspace
                  </motion.button>
                    
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={handleCreateAgent}
                    className="inline-flex items-center px-4 py-2 bg-white/10 backdrop-blur-md border border-white/20 text-white text-sm font-medium rounded-lg hover:bg-white/20 transition-all duration-300"
                  >
                    <Bot className="w-4 h-4 mr-2" />
                    New Agent
                  </motion.button>
                   
                  {/* Profile Dropdown with glass effect */}
                  <div className="relative">
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      className="flex items-center p-2 rounded-lg bg-white/10 backdrop-blur-md border border-white/20 hover:bg-white/20 transition-all duration-300"
                      onClick={() => setShowProfileDropdown(!showProfileDropdown)}
                    >
                      <div className="h-8 w-8 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center">
                        <span className="text-sm font-medium text-white">
                          {user?.full_name?.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <ChevronDown className="ml-2 h-4 w-4 text-white/70" />
                    </motion.button>
                    
                    {showProfileDropdown && (
                      <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: -10 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        transition={{ duration: 0.2 }}
                        className="absolute right-0 mt-2 w-48 bg-white/10 backdrop-blur-xl rounded-lg shadow-2xl border border-white/20 z-50"
                      >
                        <div className="py-2">
                          <div className="px-4 py-2 border-b border-white/10">
                            <div className="flex items-center px-2 py-1">
                              <User className="h-5 w-5 text-white/70" />
                              <span className="ml-3 text-sm font-medium text-white">Profile</span>
                            </div>
                          </div>
                          
                          <motion.div
                            whileHover={{ scale: 1.02 }}
                            className="px-4 py-2 hover:bg-white/10 cursor-pointer transition-all duration-200"
                          >
                            <button
                              onClick={() => router.push('/profile')}
                              className="flex items-center w-full text-left text-sm text-white hover:text-blue-400 transition-colors"
                            >
                              <User className="mr-3 h-4 w-4 text-white/70" />
                              View Profile
                            </button>
                          </motion.div>
                          
                          <motion.div
                            whileHover={{ scale: 1.02 }}
                            className="px-4 py-2 hover:bg-white/10 cursor-pointer transition-all duration-200"
                          >
                            <button
                              onClick={handleLogout}
                              className="flex items-center w-full text-left text-sm text-white hover:text-red-400 transition-colors"
                            >
                              <LogOut className="mr-3 h-4 w-4 text-white/70" />
                              Logout
                            </button>
                          </motion.div>
                        </div>
                      </motion.div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Navigation Tabs with glass effect */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.6 }}
          className="relative z-30"
        >
          <div className="bg-white/5 backdrop-blur-xl border-b border-white/10">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <nav className="flex space-x-8">
                {[
                  { key: 'overview', label: 'Overview', icon: Activity },
                  { key: 'workspaces', label: 'Workspaces', icon: FolderOpen },
                  { key: 'agents', label: 'Agents', icon: Bot }
                ].map((tab) => (
                  <motion.button
                    key={tab.key}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setActiveTab(tab.key as any)}
                    className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 transition-all duration-300 ${
                      activeTab === tab.key
                        ? 'border-blue-400 text-white'
                        : 'border-transparent text-white/60 hover:text-white hover:border-white/30'
                    }`}
                  >
                    <tab.icon className="w-4 h-4" />
                    <span>{tab.label}</span>
                    {tab.key === 'workspaces' && (
                      <span className="ml-1 px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded-full text-xs">
                        {workspaces.length}
                      </span>
                    )}
                    {tab.key === 'agents' && (
                      <span className="ml-1 px-2 py-0.5 bg-green-500/20 text-green-400 rounded-full text-xs">
                        {agents.length}
                      </span>
                    )}
                  </motion.button>
                ))}
              </nav>
            </div>
          </div>
        </motion.div>

        {/* Main Content with glass cards */}
        <div className="relative z-30 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {activeTab === 'overview' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="space-y-8"
            >
              {/* Premium Stats Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                {[
                  { icon: FolderOpen, value: workspaces.length, label: 'Total Workspaces', color: 'from-blue-500 to-cyan-500', bgColor: 'bg-blue-500/10' },
                  { icon: Bot, value: agents.length, label: 'Total Agents', color: 'from-green-500 to-emerald-500', bgColor: 'bg-green-500/10' },
                  { icon: Zap, value: agents.filter(a => a.is_active).length, label: 'Active Workflows', color: 'from-purple-500 to-pink-500', bgColor: 'bg-purple-500/10' },
                  { icon: Users, value: workspaces.reduce((total, ws) => total + ws.member_count, 0), label: 'Team Members', color: 'from-orange-500 to-red-500', bgColor: 'bg-orange-500/10' }
                ].map((stat, index) => (
                  <motion.div
                    key={stat.label}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 * index }}
                    whileHover={{ scale: 1.02, y: -2 }}
                    className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-6 shadow-2xl hover:shadow-blue-500/10 transition-all duration-300"
                  >
                    <div className="flex items-center">
                      <div className={`p-3 ${stat.bgColor} rounded-xl bg-gradient-to-br ${stat.color}`}>
                        <stat.icon className="w-6 h-6 text-white" />
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-white/70">{stat.label}</p>
                        <p className="text-3xl font-bold text-white">{stat.value}</p>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>

              {/* Recent Workspaces with glass cards */}
              <div>
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-semibold text-white">Recent Workspaces</h2>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setActiveTab('workspaces')}
                    className="text-sm text-blue-400 hover:text-blue-300 transition-colors"
                  >
                    View all →
                  </motion.button>
                </div>
                
                {recentWorkspaces.length === 0 ? (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-8 text-center"
                  >
                    <FolderOpen className="mx-auto h-12 w-12 text-white/50" />
                    <h3 className="mt-4 text-lg font-medium text-white">No workspaces yet</h3>
                    <p className="mt-2 text-white/60">Create your first workspace to get started</p>
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={handleCreateWorkspace}
                      className="mt-6 inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white font-medium rounded-lg hover:from-blue-600 hover:to-purple-600 transition-all duration-300"
                    >
                      Create Workspace
                    </motion.button>
                  </motion.div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {recentWorkspaces.map((workspace, index) => (
                      <motion.div
                        key={workspace.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 * index }}
                        whileHover={{ scale: 1.02, y: -2 }}
                      >
                        <WorkspaceCard
                          workspace={workspace}
                          onClick={() => handleWorkspaceClick(workspace.id)}
                        />
                      </motion.div>
                    ))}
                  </div>
                )}
              </div>

              {/* Recent Agents with glass cards */}
              <div>
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-semibold text-white">Recent Agents</h2>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setActiveTab('agents')}
                    className="text-sm text-blue-400 hover:text-blue-300 transition-colors"
                  >
                    View all →
                  </motion.button>
                </div>
                
                {recentAgents.length === 0 ? (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-8 text-center"
                  >
                    <Bot className="mx-auto h-12 w-12 text-white/50" />
                    <h3 className="mt-4 text-lg font-medium text-white">No agents yet</h3>
                    <p className="mt-2 text-white/60">Create your first AI agent to get started</p>
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={handleCreateAgent}
                      className="mt-6 inline-flex items-center px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-500 text-white font-medium rounded-lg hover:from-green-600 hover:to-emerald-600 transition-all duration-300"
                    >
                      Create Agent
                    </motion.button>
                  </motion.div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {recentAgents.map((agent, index) => (
                      <motion.div
                        key={agent.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 * index }}
                        whileHover={{ scale: 1.02, y: -2 }}
                      >
                        <AgentCard
                          agent={agent}
                          onClick={() => handleAgentClick(agent.id)}
                        />
                      </motion.div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {activeTab === 'workspaces' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-white">All Workspaces</h2>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleCreateWorkspace}
                  className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-500 text-white text-sm font-medium rounded-lg shadow-lg hover:shadow-xl transition-all duration-300"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Create Workspace
                </motion.button>
              </div>
              
              {workspaces.length === 0 ? (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-8 text-center"
                >
                  <FolderOpen className="mx-auto h-12 w-12 text-white/50" />
                  <h3 className="mt-4 text-lg font-medium text-white">No workspaces yet</h3>
                  <p className="mt-2 text-white/60">Create your first workspace to get started</p>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={handleCreateWorkspace}
                    className="mt-6 inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white font-medium rounded-lg hover:from-blue-600 hover:to-purple-600 transition-all duration-300"
                  >
                    Create Workspace
                  </motion.button>
                </motion.div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {workspaces.map((workspace, index) => (
                    <motion.div
                      key={workspace.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.1 * index }}
                      whileHover={{ scale: 1.02, y: -2 }}
                    >
                      <WorkspaceCard
                        workspace={workspace}
                        onClick={() => handleWorkspaceClick(workspace.id)}
                      />
                    </motion.div>
                  ))}
                </div>
              )}
            </motion.div>
          )}

          {activeTab === 'agents' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-white">All Agents</h2>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleCreateAgent}
                  className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-500 text-white text-sm font-medium rounded-lg shadow-lg hover:shadow-xl transition-all duration-300"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Create Agent
                </motion.button>
              </div>
              
              {agents.length === 0 ? (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-8 text-center"
                >
                  <Bot className="mx-auto h-12 w-12 text-white/50" />
                  <h3 className="mt-4 text-lg font-medium text-white">No agents yet</h3>
                  <p className="mt-2 text-white/60">Create your first AI agent to get started</p>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={handleCreateAgent}
                    className="mt-6 inline-flex items-center px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-500 text-white font-medium rounded-lg hover:from-green-600 hover:to-emerald-600 transition-all duration-300"
                  >
                    Create Agent
                  </motion.button>
                </motion.div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {agents.map((agent, index) => (
                    <motion.div
                      key={agent.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.1 * index }}
                      whileHover={{ scale: 1.02, y: -2 }}
                    >
                      <AgentCard
                        agent={agent}
                        onClick={() => handleAgentClick(agent.id)}
                      />
                    </motion.div>
                  ))}
                </div>
              )}
            </motion.div>
          )}
        </div>

        {/* Floating particles for extra premium feel */}
        <div className="absolute inset-0 pointer-events-none z-10">
          {[...Array(15)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-1 h-1 bg-white/20 rounded-full"
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
              }}
              animate={{
                y: [0, -100],
                opacity: [0, 0.5, 0]
              }}
              transition={{
                duration: 3 + Math.random() * 2,
                repeat: Infinity,
                delay: Math.random() * 2
              }}
            />
          ))}
        </div>
      </div>
    </ProtectedRoute>
  );
}