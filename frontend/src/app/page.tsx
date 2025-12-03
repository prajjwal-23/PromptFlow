/**
 * Premium Landing Page with Three.js Animation
 * 
 * Industry-standard landing page with immersive 3D background,
 * smooth animations, and premium UI components.
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Brain, Zap, Workflow, Sparkles, ArrowRight, Play } from 'lucide-react';
// import { ThreeScene } from '@/components/Premium/Three/ThreeScene';
import { ThreeScene } from '../components/Premium/Three/ThreeScene';

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
      color: "from-blue-500 to-cyan-500",
      stats: "10K+ agents deployed"
    },
    {
      icon: Workflow,
      title: "Visual Workflow Builder",
      description: "Create complex automation workflows with our intuitive drag-and-drop interface. No coding required.",
      color: "from-purple-500 to-pink-500",
      stats: "50K+ workflows created"
    },
    {
      icon: Zap,
      title: "Real-time Execution",
      description: "Watch your agents execute in real-time with live streaming, monitoring, and instant feedback.",
      color: "from-green-500 to-emerald-500",
      stats: "1M+ executions completed"
    },
    {
      icon: Sparkles,
      title: "Premium Experience",
      description: "Enjoy a premium, polished interface with smooth animations, glass effects, and modern design.",
      color: "from-orange-500 to-red-500",
      stats: "99.9% uptime"
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 overflow-hidden">
      {/* Three.js Background - Commented out for now due to TypeScript issues */}
      <ThreeScene />
      
      {/* Interactive background gradient */}
      <div 
        className="fixed inset-0 z-0 opacity-30 pointer-events-none"
        style={{
          background: `radial-gradient(circle at ${mousePosition.x}% ${mousePosition.y}%, rgba(79, 70, 229, 0.4) 0%, transparent 60%)`
        }}
      />

      {/* Main content */}
      <div className="relative z-20 min-h-screen flex items-center">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-4xl mx-auto text-center">
            {isLoaded && (
              <motion.div
                initial={{ opacity: 0, y: 50 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, ease: "easeOut" }}
                className="space-y-8"
              >
                {/* Subtitle with animation */}
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.2 }}
                  className="inline-flex items-center px-4 py-2 bg-white/10 backdrop-blur-md rounded-full border border-white/20 mb-6"
                >
                  <Sparkles className="w-4 h-4 text-yellow-400 mr-2" />
                  <span className="text-sm font-medium text-white/90">The Future of Automation is Here</span>
                </motion.div>

                {/* Main title with gradient effect */}
                <motion.h1
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4, duration: 0.6 }}
                  className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-white via-blue-200 to-purple-200 bg-clip-text text-transparent"
                >
                  Build AI Agents That Think
                </motion.h1>

                {/* Description with typewriter effect */}
                <motion.p
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.6, duration: 0.6 }}
                  className="text-xl text-white/80 max-w-3xl mx-auto leading-relaxed"
                >
                  Create intelligent AI agents with visual workflows, real-time execution, and seamless integration. Transform your ideas into powerful automation solutions.
                </motion.p>

                {/* CTA Buttons */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.8 }}
                  className="flex flex-col sm:flex-row gap-4 justify-center items-center mt-8"
                >
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={handleStartBuilding}
                    className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-emerald-500 via-teal-500 to-cyan-500 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300"
                  >
                    Start Building Free
                    <ArrowRight className="w-5 h-5 ml-2" />
                  </motion.button>
                  
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={handleWatchDemo}
                    className="inline-flex items-center px-8 py-4 bg-white/10 backdrop-blur-md border border-white/20 text-white font-semibold rounded-xl hover:bg-white/20 transition-all duration-300"
                  >
                    Watch Demo
                    <Play className="w-5 h-5 ml-2" />
                  </motion.button>
                </motion.div>

                {/* Stats section */}
                <motion.div
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 1 }}
                  className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-16"
                >
                  {[
                    { icon: Brain, value: "10K+", label: "AI Agents Built" },
                    { icon: Workflow, value: "50K+", label: "Workflows Created" },
                    { icon: Zap, value: "1M+", label: "Executions Completed" },
                    { icon: Sparkles, value: "99.9%", label: "Uptime" }
                  ].map((stat, index) => (
                    <motion.div
                      key={stat.label}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 1 + index * 0.1 }}
                      className="text-center group"
                    >
                      <div className="flex flex-col items-center space-y-2">
                        <div className="p-3 bg-white/10 backdrop-blur-md rounded-xl border border-white/20 group-hover:bg-white/20 transition-all duration-300">
                          <stat.icon className="w-6 h-6 text-blue-400" />
                        </div>
                        <div className="text-2xl font-bold text-white">{stat.value}</div>
                        <div className="text-sm text-white/60">{stat.label}</div>
                      </div>
                    </motion.div>
                  ))}
                </motion.div>
              </motion.div>
            )}
          </div>
        </div>
      </div>

      {/* Scroll indicator */}
      <motion.div
        className="absolute bottom-8 left-1/2 transform -translate-x-1/2"
        animate={{ y: [0, 10, 0] }}
        transition={{ duration: 2, repeat: Infinity }}
      >
        <div className="w-6 h-10 border-2 border-white/30 rounded-full flex justify-center">
          <motion.div
            className="w-1 h-3 bg-white/60 rounded-full mt-2"
            animate={{ opacity: [0.3, 1, 0.3] }}
            transition={{ duration: 1.5, repeat: Infinity }}
          />
        </div>
      </motion.div>
    </div>
  );
}
