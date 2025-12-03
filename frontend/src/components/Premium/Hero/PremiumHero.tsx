/**
 * Premium Hero Component with Three.js Animation
 * 
 * Industry-standard hero section with immersive 3D background,
 * gradient text, and smooth animations.
 */

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ThreeScene } from '../Three/ThreeScene';
import { PremiumButton } from '../Buttons/PremiumButton';
import { GradientText } from '../Typography/GradientText';
import { FloatingElements } from '../Animations/FloatingElements';
import { Sparkles, ArrowRight, Zap, Brain, Workflow } from 'lucide-react';

interface PremiumHeroProps {
  title?: string;
  subtitle?: string;
  description?: string;
  primaryButtonText?: string;
  secondaryButtonText?: string;
  onPrimaryButtonClick?: () => void;
  onSecondaryButtonClick?: () => void;
  showStats?: boolean;
  className?: string;
}

export function PremiumHero({
  title = "Build AI Agents That Think",
  subtitle = "The Future of Automation",
  description = "Create intelligent AI agents with visual workflows, real-time execution, and seamless integration. Transform your ideas into powerful automation solutions.",
  primaryButtonText = "Start Building",
  secondaryButtonText = "Watch Demo",
  onPrimaryButtonClick,
  onSecondaryButtonClick,
  showStats = true,
  className
}: PremiumHeroProps) {
  const [isLoaded, setIsLoaded] = useState(false);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    setIsLoaded(true);
  }, []);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({
        x: (e.clientX / window.innerWidth) * 100,
        y: (e.clientY / window.innerHeight) * 100
      });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  const stats = [
    { icon: Brain, value: "10K+", label: "AI Agents Built" },
    { icon: Workflow, value: "50K+", label: "Workflows Created" },
    { icon: Zap, value: "1M+", label: "Executions Completed" },
    { icon: Sparkles, value: "99.9%", label: "Uptime" }
  ];

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.3
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 50 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        type: "spring" as const,
        stiffness: 100,
        damping: 10
      }
    }
  };

  const glowVariants = {
    initial: { opacity: 0, scale: 0.8 },
    animate: {
      opacity: [0.3, 0.6, 0.3],
      scale: [0.8, 1.2, 0.8],
      transition: {
        duration: 4,
        repeat: Infinity,
        ease: "easeInOut" as const
      }
    }
  };

  return (
    <section className={`relative min-h-screen overflow-hidden bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 ${className}`}>
      {/* Three.js Background */}
      <ThreeScene />
      
      {/* Animated gradient overlay */}
      <div 
        className="absolute inset-0 z-10 opacity-30"
        style={{
          background: `radial-gradient(circle at ${mousePosition.x}% ${mousePosition.y}%, rgba(79, 70, 229, 0.3) 0%, transparent 50%)`
        }}
      />
      
      {/* Floating elements */}
      <FloatingElements />
      
      {/* Main content */}
      <div className="relative z-20 container mx-auto px-4 sm:px-6 lg:px-8 min-h-screen flex items-center">
        <div className="max-w-4xl mx-auto text-center">
          <AnimatePresence>
            {isLoaded && (
              <motion.div
                variants={containerVariants}
                initial="hidden"
                animate="visible"
                className="space-y-8"
              >
                {/* Subtitle with animation */}
                <motion.div variants={itemVariants}>
                  <motion.div
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.1 }}
                    className="inline-flex items-center px-4 py-2 bg-white/10 backdrop-blur-md rounded-full border border-white/20 mb-6"
                  >
                    <Sparkles className="w-4 h-4 text-yellow-400 mr-2" />
                    <span className="text-sm font-medium text-white/90">{subtitle}</span>
                  </motion.div>
                </motion.div>

                {/* Main title with gradient effect */}
                <motion.div variants={itemVariants}>
                  <GradientText
                    className="text-5xl md:text-7xl font-bold mb-6"
                    gradient="from-white via-blue-200 to-purple-200"
                    animate
                  >
                    {title}
                  </GradientText>
                </motion.div>

                {/* Description with typewriter effect */}
                <motion.div variants={itemVariants}>
                  <motion.p
                    className="text-xl text-white/80 max-w-3xl mx-auto leading-relaxed"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.4 }}
                  >
                    {description}
                  </motion.p>
                </motion.div>

                {/* CTA Buttons */}
                <motion.div
                  variants={itemVariants}
                  className="flex flex-col sm:flex-row gap-4 justify-center items-center mt-8"
                >
                  <PremiumButton
                    variant="gradient"
                    size="lg"
                    icon={<ArrowRight />}
                    iconPosition="right"
                    onClick={onPrimaryButtonClick}
                    glow
                    className="px-8"
                  >
                    {primaryButtonText}
                  </PremiumButton>
                  
                  <PremiumButton
                    variant="glass"
                    size="lg"
                    onClick={onSecondaryButtonClick}
                    className="px-8"
                  >
                    {secondaryButtonText}
                  </PremiumButton>
                </motion.div>

                {/* Stats section */}
                {showStats && (
                  <motion.div
                    variants={itemVariants}
                    className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-16"
                  >
                    {stats.map((stat, index) => (
                      <motion.div
                        key={stat.label}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.6 + index * 0.1 }}
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
                )}

                {/* Animated glow effect */}
                <motion.div
                  variants={glowVariants}
                  initial="initial"
                  animate="animate"
                  className="absolute inset-0 bg-gradient-to-r from-blue-500/20 via-purple-500/20 to-pink-500/20 rounded-full blur-3xl -z-10"
                />
              </motion.div>
            )}
          </AnimatePresence>
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
    </section>
  );
}