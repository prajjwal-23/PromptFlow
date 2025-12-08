/**
 * Premium Landing Page with Hero Section
 *
 * Modern landing page with hero section, smooth animations, and premium UI components.
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Brain, Zap, Workflow, Sparkles, ArrowRight, Play } from 'lucide-react';
import { HeroSection, Navigation } from '@/src/components/ui';

export default function HomePage() {
  const router = useRouter();
  const [isLoaded, setIsLoaded] = useState(false);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    setIsLoaded(true);
    
    // Mouse tracking for interactive effects
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({
        x: (e.clientX / window.innerWidth) * 100,
        y: (e.clientY / window.innerHeight) * 100
      });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  const handleStartBuilding = () => {
    router.push('/register');
  };

  const handleWatchDemo = () => {
    // Open demo modal or navigate to demo page
    console.log('Opening demo...');
  };

  const features = [
    {
      icon: Brain,
      title: "AI-Powered Intelligence",
      description: "Build agents that learn, adapt, and make intelligent decisions using cutting-edge AI models.",
      color: "from-yellow-400 to-yellow-500",
      stats: "10K+ agents deployed"
    },
    {
      icon: Workflow,
      title: "Visual Workflow Builder",
      description: "Create complex automation workflows with our intuitive drag-and-drop interface. No coding required.",
      color: "from-gray-600 to-gray-700",
      stats: "50K+ workflows created"
    },
    {
      icon: Zap,
      title: "Real-time Execution",
      description: "Watch your agents execute in real-time with live streaming, monitoring, and instant feedback.",
      color: "from-yellow-500 to-yellow-600",
      stats: "1M+ executions completed"
    },
    {
      icon: Sparkles,
      title: "Premium Experience",
      description: "Enjoy a premium, polished interface with smooth animations, glass effects, and modern design.",
      color: "from-gray-700 to-black",
      stats: "99.9% uptime"
    }
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <HeroSection />
      
      {/* Features Section */}
      <section className="py-20 bg-gradient-to-br from-gray-50 via-white to-yellow-50 dark:from-gray-900 dark:via-gray-800 dark:to-yellow-900">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <motion.h2
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
              className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-yellow-400 to-yellow-500 bg-clip-text text-transparent"
            >
              Why Choose PromptFlow?
            </motion.h2>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              viewport={{ once: true }}
              className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto"
            >
              Experience the power of intelligent automation with our cutting-edge platform designed for modern businesses.
            </motion.p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="group relative"
              >
                <div className="relative p-8 bg-white dark:bg-gray-800 rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 border border-gray-100 dark:border-gray-700 hover:border-yellow-200 dark:hover:border-yellow-800">
                  {/* Background gradient */}
                  <div className={`absolute inset-0 bg-gradient-to-br ${feature.color} opacity-0 group-hover:opacity-10 rounded-2xl transition-opacity duration-300`} />
                  
                  {/* Icon */}
                  <div className={`inline-flex p-3 bg-gradient-to-br ${feature.color} rounded-xl mb-6`}>
                    <feature.icon className="w-6 h-6 text-white" />
                  </div>
                  
                  {/* Content */}
                  <h3 className="text-xl font-semibold mb-3 text-gray-900 dark:text-white">
                    {feature.title}
                  </h3>
                  <p className="text-gray-600 dark:text-gray-300 mb-4 leading-relaxed">
                    {feature.description}
                  </p>
                  
                  {/* Stats */}
                  <div className="flex items-center text-sm font-medium text-yellow-600 dark:text-yellow-400">
                    <span>{feature.stats}</span>
                    <ArrowRight className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform duration-300" />
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Quick Start Section */}
      <section className="py-20 bg-white dark:bg-gray-900">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <motion.div
              initial={{ opacity: 0, x: -50 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
            >
              <h2 className="text-3xl md:text-4xl font-bold mb-6 text-gray-900 dark:text-white">
                Get Started in Minutes
              </h2>
              <p className="text-lg text-gray-600 dark:text-gray-300 mb-8">
                Create your first AI agent with our intuitive visual builder. No coding required.
              </p>
              <div className="space-y-4">
                {[
                  { step: "1", title: "Sign up for free", description: "Create your account in seconds" },
                  { step: "2", title: "Choose a template", description: "Start with pre-built agent templates" },
                  { step: "3", title: "Customize & Deploy", description: "Tailor your agent and deploy instantly" }
                ].map((item, index) => (
                  <div key={index} className="flex items-start space-x-4">
                    <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-r from-yellow-400 to-yellow-500 rounded-full flex items-center justify-center text-black font-semibold text-sm">
                      {item.step}
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900 dark:text-white">{item.title}</h3>
                      <p className="text-gray-600 dark:text-gray-300">{item.description}</p>
                    </div>
                  </div>
                ))}
              </div>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleStartBuilding}
                className="mt-8 inline-flex items-center px-6 py-3 bg-gradient-to-r from-yellow-400 to-yellow-500 text-black font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300"
              >
                Get Started Now
                <ArrowRight className="w-5 h-5 ml-2" />
              </motion.button>
            </motion.div>
            
            <motion.div
              initial={{ opacity: 0, x: 50 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              viewport={{ once: true }}
              className="relative"
            >
              <div className="relative bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-800 dark:to-black rounded-2xl p-8 shadow-xl">
                <div className="absolute inset-0 bg-gradient-to-br from-yellow-400/20 to-yellow-500/20 rounded-2xl"></div>
                <div className="relative z-10">
                  <div className="aspect-video bg-white dark:bg-gray-900 rounded-lg shadow-inner flex items-center justify-center">
                    <div className="text-center">
                      <Brain className="w-16 h-16 text-yellow-600 dark:text-yellow-400 mx-auto mb-4" />
                      <p className="text-gray-600 dark:text-gray-300">Interactive Agent Builder Preview</p>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-yellow-400 to-yellow-500 relative overflow-hidden">
        {/* Background pattern */}
        <div className="absolute inset-0 opacity-10">
          <div
            className="absolute inset-0 bg-repeat"
            style={{
              backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.4'%3E%3Ccircle cx='30' cy='30' r='4'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`
            }}
          />
        </div>
        
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center max-w-4xl mx-auto">
            <motion.h2
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
              className="text-4xl md:text-5xl font-bold mb-6 text-white"
            >
              Ready to Transform Your Workflow?
            </motion.h2>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              viewport={{ once: true }}
              className="text-xl text-white/90 mb-8 max-w-2xl mx-auto"
            >
              Join thousands of teams already using PromptFlow to automate their workflows and boost productivity.
            </motion.p>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              viewport={{ once: true }}
              className="flex flex-col sm:flex-row gap-4 justify-center items-center"
            >
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleStartBuilding}
                className="inline-flex items-center px-8 py-4 bg-black text-yellow-400 font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300"
              >
                Start Building Free
                <ArrowRight className="w-5 h-5 ml-2" />
              </motion.button>
              
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleWatchDemo}
                className="inline-flex items-center px-8 py-4 bg-black/20 backdrop-blur-md border border-black/30 text-yellow-400 font-semibold rounded-xl hover:bg-black/30 transition-all duration-300"
              >
                View Demo
                <Play className="w-5 h-5 ml-2" />
              </motion.button>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-gray-50 dark:bg-black">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {[
              { icon: Brain, value: "10K+", label: "AI Agents Built" },
              { icon: Workflow, value: "50K+", label: "Workflows Created" },
              { icon: Zap, value: "1M+", label: "Executions Completed" },
              { icon: Sparkles, value: "99.9%", label: "Uptime" }
            ].map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                viewport={{ once: true }}
                className="text-center group"
              >
                <div className="flex flex-col items-center space-y-2">
                  <div className="p-3 bg-white dark:bg-gray-800 rounded-xl shadow-md group-hover:shadow-lg transition-all duration-300">
                    <stat.icon className="w-6 h-6 text-yellow-600 dark:text-yellow-400" />
                  </div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">{stat.value}</div>
                  <div className="text-sm text-gray-600 dark:text-gray-300">{stat.label}</div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
