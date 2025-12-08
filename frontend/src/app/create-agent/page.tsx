/**
 * Premium Create Agent Page
 * 
 * Industry-standard agent creation page with glass morphism,
 * step-by-step wizard, and smooth animations.
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { useAuthStore } from '../../store/authStore';
import { useWorkspaceStore } from '../../store/workspaceStore';
import { useAgentStore } from '../../store/agentStore';
import { ProtectedRoute } from '../../components/ProtectedRoute';
import { Brain, Zap, Sparkles, ArrowRight, ArrowLeft, Check, Settings, Code, Workflow } from 'lucide-react';

export default function CreateAgentPage() {
  const router = useRouter();
  const { user } = useAuthStore();
  const { workspaces } = useWorkspaceStore();
  const { createAgent } = useAgentStore();
  const [currentStep, setCurrentStep] = useState(1);
  const [isCreating, setIsCreating] = useState(false);
  const [agentData, setAgentData] = useState({
    name: '',
    description: '',
    workspaceId: workspaces[0]?.id || '',
    graphJson: null as any,
    isActive: true
  });

  const steps = [
    { 
      number: 1, 
      title: 'Basic Info', 
      icon: Settings,
      description: 'Name your agent and provide details'
    },
    { 
      number: 2, 
      title: 'Workspace', 
      icon: Code,
      description: 'Choose where your agent will live'
    },
    { 
      number: 3, 
      title: 'Finalize', 
      icon: Sparkles,
      description: 'Review and create your agent'
    }
  ];

  const handleNext = () => {
    if (currentStep < 3) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleCreate = async () => {
    setIsCreating(true);
    try {
      const newAgent = await createAgent({
        name: agentData.name,
        description: agentData.description,
        workspace_id: agentData.workspaceId,
        graph_json: agentData.graphJson,
      });
      router.push(`/agents/${newAgent.id}/edit`);
    } catch (error) {
      console.error('Failed to create agent:', error);
      setIsCreating(false);
    }
  };

  const isStepValid = (step: number) => {
    switch (step) {
      case 1:
        return agentData.name.trim().length >= 2;
      case 2:
        return agentData.workspaceId !== '';
      case 3:
        return true;
      default:
        return false;
    }
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black relative overflow-hidden">
        {/* Animated background particles */}
        <div className="absolute inset-0 pointer-events-none">
          {[...Array(12)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-1 h-1 bg-white/20 rounded-full"
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
              }}
              animate={{
                y: [0, -60],
                opacity: [0, 0.4, 0]
              }}
              transition={{
                duration: 2 + Math.random() * 2,
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
                <Brain className="w-12 h-12 text-white relative z-10" />
              </div>
            </div>
            <h1 className="text-4xl font-bold text-white mb-2">Create AI Agent</h1>
            <p className="text-white/70">Build an intelligent agent that thinks and acts</p>
          </motion.div>

          {/* Progress Steps */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="flex justify-center mb-12"
          >
            <div className="flex items-center space-x-4">
              {steps.map((step, index) => (
                <div key={step.number} className="flex items-center">
                  <motion.div
                    whileHover={{ scale: 1.05 }}
                    className={`flex items-center justify-center w-12 h-12 rounded-full border-2 transition-all duration-300 ${
                      currentStep >= step.number
                        ? 'bg-gradient-to-r from-yellow-400 to-yellow-500 border-transparent text-black'
                        : 'bg-white/10 border-white/30 text-white/60'
                    }`}
                  >
                    {currentStep > step.number ? (
                      <Check className="w-6 h-6" />
                    ) : (
                      <step.icon className="w-6 h-6" />
                    )}
                  </motion.div>
                  {index < steps.length - 1 && (
                    <div className={`w-16 h-0.5 mx-2 ${
                      currentStep > step.number
                        ? 'bg-gradient-to-r from-yellow-400 to-yellow-500'
                        : 'bg-white/20'
                    }`} />
                  )}
                </div>
              ))}
            </div>
          </motion.div>

          {/* Step Content */}
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
            className="max-w-2xl mx-auto"
          >
            {/* Step 1: Basic Info */}
            {currentStep === 1 && (
              <div className="space-y-8">
                <div className="text-center">
                  <h2 className="text-2xl font-semibold text-white mb-2">{steps[0].title}</h2>
                  <p className="text-white/70">{steps[0].description}</p>
                </div>

                <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-8 space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-white/80 mb-2">
                      Agent Name
                    </label>
                    <input
                      type="text"
                      value={agentData.name}
                      onChange={(e) => setAgentData({ ...agentData, name: e.target.value })}
                      className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/50 focus:ring-2 focus:ring-yellow-400 focus:border-transparent transition-all duration-300"
                      placeholder="e.g., Customer Support Bot"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-white/80 mb-2">
                      Description
                    </label>
                    <textarea
                      value={agentData.description}
                      onChange={(e) => setAgentData({ ...agentData, description: e.target.value })}
                      className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/50 focus:ring-2 focus:ring-yellow-400 focus:border-transparent transition-all duration-300 resize-none"
                      placeholder="Describe what this agent does..."
                      rows={3}
                    />
                  </div>

                  <div>
                    <label className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={agentData.isActive}
                        onChange={(e) => setAgentData({ ...agentData, isActive: e.target.checked })}
                        className="w-4 h-4 text-yellow-600 bg-white/10 border-white/20 rounded focus:ring-yellow-400"
                      />
                      <span className="text-white/80">Activate agent immediately</span>
                    </label>
                  </div>
                </div>
              </div>
            )}

            {/* Step 2: Workspace */}
            {currentStep === 2 && (
              <div className="space-y-8">
                <div className="text-center">
                  <h2 className="text-2xl font-semibold text-white mb-2">{steps[1].title}</h2>
                  <p className="text-white/70">{steps[1].description}</p>
                </div>

                <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-8">
                  <div>
                    <label className="block text-sm font-medium text-white/80 mb-2">
                      Select Workspace
                    </label>
                    <select
                      value={agentData.workspaceId}
                      onChange={(e) => setAgentData({ ...agentData, workspaceId: e.target.value })}
                      className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white focus:ring-2 focus:ring-yellow-400 focus:border-transparent transition-all duration-300"
                      required
                    >
                      {workspaces.map((workspace) => (
                        <option key={workspace.id} value={workspace.id} className="bg-gray-800">
                          {workspace.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  {workspaces.length === 0 && (
                    <div className="mt-4 p-4 bg-yellow-500/20 border border-yellow-500/30 rounded-xl">
                      <p className="text-yellow-300 text-sm">
                        You need to create a workspace first.{' '}
                        <Link href="/create-workspace" className="text-yellow-400 hover:text-yellow-300 font-medium">
                          Create a workspace
                        </Link>
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Step 3: Finalize */}
            {currentStep === 3 && (
              <div className="space-y-8">
                <div className="text-center">
                  <h2 className="text-2xl font-semibold text-white mb-2">{steps[2].title}</h2>
                  <p className="text-white/70">{steps[2].description}</p>
                </div>

                <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-8 space-y-6">
                  <div className="flex items-center justify-between">
                    <span className="text-white/70">Agent Name:</span>
                    <span className="text-white font-medium">{agentData.name}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-white/70">Description:</span>
                    <span className="text-white font-medium">{agentData.description || 'No description'}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-white/70">Workspace:</span>
                    <span className="text-white font-medium">
                      {workspaces.find(w => w.id === agentData.workspaceId)?.name || 'Unknown'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-white/70">Status:</span>
                    <span className="text-white font-medium">{agentData.isActive ? 'Active' : 'Inactive'}</span>
                  </div>
                </div>

                <div className="bg-gradient-to-r from-yellow-500/20 to-yellow-600/20 border border-yellow-500/30 rounded-xl p-6">
                  <div className="flex items-center space-x-3">
                    <Zap className="w-6 h-6 text-yellow-400" />
                    <div>
                      <h3 className="text-white font-medium">Ready to create!</h3>
                      <p className="text-white/70 text-sm">Your AI agent will be created and ready for configuration.</p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </motion.div>

          {/* Navigation Buttons */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="flex justify-between items-center mt-12"
          >
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handlePrevious}
              disabled={currentStep === 1}
              className="flex items-center px-6 py-3 bg-white/10 backdrop-blur-md border border-white/20 text-white rounded-xl hover:bg-white/20 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Previous
            </motion.button>

            <div className="flex space-x-3">
              {currentStep < 3 ? (
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleNext}
                  disabled={!isStepValid(currentStep)}
                  className="flex items-center px-6 py-3 bg-gradient-to-r from-yellow-400 to-yellow-500 text-black rounded-xl hover:from-yellow-500 hover:to-yellow-600 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                  <ArrowRight className="w-4 h-4 ml-2" />
                </motion.button>
              ) : (
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleCreate}
                  disabled={isCreating || !isStepValid(currentStep)}
                  className="flex items-center px-8 py-3 bg-gradient-to-r from-gray-600 to-gray-700 text-white rounded-xl hover:from-gray-700 hover:to-gray-800 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isCreating ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                      Creating...
                    </>
                  ) : (
                    <>
                      Create Agent
                      <Sparkles className="w-4 h-4 ml-2" />
                    </>
                  )}
                </motion.button>
              )}
            </div>
          </motion.div>
        </div>
      </div>
    </ProtectedRoute>
  );
}