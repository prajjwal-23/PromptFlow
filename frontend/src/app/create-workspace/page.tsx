/**
 * Premium Create Workspace Page
 * 
 * Industry-standard workspace creation page with glass morphism,
 * team collaboration features, and smooth animations.
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { useAuthStore } from '../../store/authStore';
import { useWorkspaceStore } from '../../store/workspaceStore';
import { ProtectedRoute } from '../../components/ProtectedRoute';
import { Users, Building, Globe, Shield, Sparkles, ArrowRight, Check } from 'lucide-react';

export default function CreateWorkspacePage() {
  const router = useRouter();
  const { user } = useAuthStore();
  const { createWorkspace } = useWorkspaceStore();
  const [isCreating, setIsCreating] = useState(false);
  const [workspaceData, setWorkspaceData] = useState({
    name: '',
    description: '',
    visibility: 'private' as 'private' | 'public',
    memberLimit: 10
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsCreating(true);

    try {
      const newWorkspace = await createWorkspace({
        name: workspaceData.name,
        description: workspaceData.description,
      });
      router.push(`/workspaces/${newWorkspace.id}`);
    } catch (error) {
      console.error('Failed to create workspace:', error);
      setIsCreating(false);
    }
  };

  const features = [
    { icon: Users, title: 'Team Collaboration', description: 'Invite team members and collaborate on AI agents' },
    { icon: Shield, title: 'Secure Environment', description: 'Your data is protected with enterprise-grade security' },
    { icon: Building, title: 'Organization Ready', description: 'Perfect for teams and organizations of any size' },
    { icon: Globe, title: 'Global Access', description: 'Access your workspace from anywhere in the world' }
  ];

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black relative overflow-hidden">
        {/* Animated background particles */}
        <div className="absolute inset-0 pointer-events-none">
          {[...Array(10)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-1 h-1 bg-white/20 rounded-full"
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
              }}
              animate={{
                y: [0, -50],
                opacity: [0, 0.3, 0]
              }}
              transition={{
                duration: 3 + Math.random() * 2,
                repeat: Infinity,
                delay: Math.random() * 2
              }}
            />
          ))}
        </div>

        {/* Glass morphism overlay */}
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-black/10 to-black/30" />

        <div className="relative z-10 container mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-8"
          >
            <div className="flex justify-center mb-4">
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-yellow-400 to-yellow-500 rounded-full blur-xl opacity-50" />
                <Building className="w-12 h-12 text-white relative z-10" />
              </div>
            </div>
            <h1 className="text-4xl font-bold text-white mb-2">Create Workspace</h1>
            <p className="text-white/70">Set up your collaborative environment for AI agents</p>
          </motion.div>

          <div className="max-w-4xl mx-auto">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Left Column - Form */}
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 }}
              >
                <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-8">
                  <form onSubmit={handleSubmit} className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium text-white/80 mb-2">
                        Workspace Name
                      </label>
                      <input
                        type="text"
                        value={workspaceData.name}
                        onChange={(e) => setWorkspaceData({ ...workspaceData, name: e.target.value })}
                        className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/50 focus:ring-2 focus:ring-yellow-400 focus:border-transparent transition-all duration-300"
                        placeholder="e.g., Marketing Team"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-white/80 mb-2">
                        Description
                      </label>
                      <textarea
                        value={workspaceData.description}
                        onChange={(e) => setWorkspaceData({ ...workspaceData, description: e.target.value })}
                        className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/50 focus:ring-2 focus:ring-yellow-400 focus:border-transparent transition-all duration-300 resize-none"
                        placeholder="Describe the purpose of this workspace..."
                        rows={3}
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-white/80 mb-2">
                        Visibility
                      </label>
                      <div className="space-y-3">
                        <label className="flex items-center space-x-3">
                          <input
                            type="radio"
                            name="visibility"
                            value="private"
                            checked={workspaceData.visibility === 'private'}
                            onChange={(e) => setWorkspaceData({ ...workspaceData, visibility: e.target.value as 'private' | 'public' })}
                            className="w-4 h-4 text-yellow-600 bg-white/10 border-white/20 focus:ring-yellow-400"
                          />
                          <div>
                            <span className="text-white font-medium">Private</span>
                            <p className="text-white/60 text-sm">Only invited members can access this workspace</p>
                          </div>
                        </label>
                        <label className="flex items-center space-x-3">
                          <input
                            type="radio"
                            name="visibility"
                            value="public"
                            checked={workspaceData.visibility === 'public'}
                            onChange={(e) => setWorkspaceData({ ...workspaceData, visibility: e.target.value as 'private' | 'public' })}
                            className="w-4 h-4 text-yellow-600 bg-white/10 border-white/20 focus:ring-yellow-400"
                          />
                          <div>
                            <span className="text-white font-medium">Public</span>
                            <p className="text-white/60 text-sm">Anyone can discover and join this workspace</p>
                          </div>
                        </label>
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-white/80 mb-2">
                        Member Limit
                      </label>
                      <select
                        value={workspaceData.memberLimit}
                        onChange={(e) => setWorkspaceData({ ...workspaceData, memberLimit: parseInt(e.target.value) })}
                        className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white focus:ring-2 focus:ring-yellow-400 focus:border-transparent transition-all duration-300"
                      >
                        <option value={5}>5 members</option>
                        <option value={10}>10 members</option>
                        <option value={25}>25 members</option>
                        <option value={50}>50 members</option>
                        <option value={100}>100 members</option>
                      </select>
                    </div>

                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      type="submit"
                      disabled={isCreating || !workspaceData.name.trim()}
                      className="w-full bg-gradient-to-r from-yellow-400 via-yellow-500 to-yellow-600 text-black font-semibold py-3 px-4 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                    >
                      {isCreating ? (
                        <div className="flex items-center">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                          Creating workspace...
                        </div>
                      ) : (
                        <>
                          Create Workspace
                          <Sparkles className="ml-2 h-4 w-4" />
                        </>
                      )}
                    </motion.button>
                  </form>
                </div>
              </motion.div>

              {/* Right Column - Features */}
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 }}
              >
                <div className="space-y-6">
                  <h3 className="text-xl font-semibold text-white mb-4">Workspace Features</h3>
                  
                  {features.map((feature, index) => (
                    <motion.div
                      key={feature.title}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.1 * index }}
                      className="flex items-start space-x-4 p-4 bg-white/5 backdrop-blur-md border border-white/10 rounded-xl"
                    >
                      <div className="p-2 bg-gradient-to-r from-yellow-400 to-yellow-500 rounded-lg">
                        <feature.icon className="w-5 h-5 text-white" />
                      </div>
                      <div>
                        <h4 className="text-white font-medium">{feature.title}</h4>
                        <p className="text-white/70 text-sm">{feature.description}</p>
                      </div>
                    </motion.div>
                  ))}
                </div>

                {/* Tips Section */}
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.6 }}
                  className="mt-8 p-6 bg-gradient-to-r from-yellow-500/20 to-yellow-600/20 border border-yellow-500/30 rounded-xl"
                >
                  <h4 className="text-white font-medium mb-2">Pro Tips</h4>
                  <ul className="space-y-2 text-white/70 text-sm">
                    <li className="flex items-start space-x-2">
                      <Check className="w-4 h-4 text-green-400 mt-0.5" />
                      <span>Choose a descriptive name that reflects your team's purpose</span>
                    </li>
                    <li className="flex items-start space-x-2">
                      <Check className="w-4 h-4 text-green-400 mt-0.5" />
                      <span>Set appropriate member limits based on your team size</span>
                    </li>
                    <li className="flex items-start space-x-2">
                      <Check className="w-4 h-4 text-green-400 mt-0.5" />
                      <span>Use private visibility for sensitive projects</span>
                    </li>
                  </ul>
                </motion.div>
              </motion.div>
            </div>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}