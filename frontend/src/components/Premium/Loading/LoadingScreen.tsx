/**
 * Premium Loading Screen Component
 * 
 * Industry-standard loading screen with smooth animations and premium design
 */

import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';
import { Brain, Zap, Sparkles } from 'lucide-react';

interface LoadingScreenProps {
  duration?: number;
  onComplete?: () => void;
  showProgress?: boolean;
  message?: string;
}

export function LoadingScreen({ 
  duration = 2000, 
  onComplete, 
  showProgress = true,
  message = "Building your AI experience..."
}: LoadingScreenProps) {
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    { icon: Brain, text: "Initializing AI Engine", color: "from-primary to-accent" },
    { icon: Zap, text: "Loading Workflows", color: "from-primary to-accent/80" },
    { icon: Sparkles, text: "Preparing Interface", color: "from-success to-primary" }
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress((prev) => {
        const newProgress = prev + (100 / (duration / 50));
        if (newProgress >= 100) {
          clearInterval(interval);
          if (onComplete) onComplete();
          return 100;
        }
        return newProgress;
      });
    }, 50);

    return () => clearInterval(interval);
  }, [duration, onComplete]);

  useEffect(() => {
    // Update step based on progress
    const stepIndex = Math.floor((progress / 100) * steps.length);
    setCurrentStep(Math.min(stepIndex, steps.length - 1));
  }, [progress, steps.length]);

  const containerVariants = {
    hidden: { opacity: 0, scale: 0.9 },
    visible: {
      opacity: 1,
      scale: 1,
      transition: { duration: 0.6, ease: "easeOut" as const }
    },
    exit: {
      opacity: 0,
      scale: 1.1,
      transition: { duration: 0.4, ease: "easeIn" as const }
    }
  };

  const iconVariants = {
    initial: { scale: 0, rotate: -180 },
    animate: {
      scale: 1,
      rotate: 0,
      transition: {
        type: "spring" as const,
        stiffness: 200,
        damping: 15
      }
    }
  };

  const progressVariants = {
    initial: { width: "0%" },
    animate: {
      width: `${progress}%`,
      transition: { duration: 0.3, ease: "easeOut" as const }
    }
  };

  const currentStepData = steps[currentStep];

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      exit="exit"
      className="fixed inset-0 z-50 bg-gradient-to-br from-background via-muted to-accent flex items-center justify-center"
    >
      <div className="text-center max-w-md mx-auto px-6">
        {/* Animated icon */}
        <motion.div
          variants={iconVariants}
          initial="initial"
          animate="animate"
          className="mb-8"
        >
          <div className="relative inline-block">
            <div className="absolute inset-0 bg-gradient-to-r from-primary to-accent rounded-full blur-xl opacity-50 animate-pulse" />
            <currentStepData.icon className="w-16 h-16 text-foreground relative z-10" />
          </div>
        </motion.div>

        {/* Title */}
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="text-2xl font-bold text-foreground mb-2"
        >
          PromptFlow
        </motion.h2>

        {/* Step text */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="text-foreground/70 mb-8"
        >
          {currentStepData.text}
        </motion.p>

        {/* Progress bar */}
        {showProgress && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="w-full"
          >
            <div className="h-2 bg-muted/10 rounded-full overflow-hidden mb-4">
              <motion.div
                variants={progressVariants}
                initial="initial"
                animate="animate"
                className={`h-full bg-gradient-to-r ${currentStepData.color} rounded-full`}
              />
            </div>
            
            <div className="flex justify-between text-xs text-muted-foreground/50">
              <span>{Math.round(progress)}%</span>
              <span>{message}</span>
            </div>
          </motion.div>
        )}

        {/* Animated dots */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="flex justify-center space-x-2 mt-6"
        >
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              className="w-2 h-2 bg-muted-foreground/30 rounded-full"
              animate={{
                scale: [1, 1.5, 1],
                opacity: [0.3, 1, 0.3]
              }}
              transition={{
                duration: 1.5,
                repeat: Infinity,
                delay: i * 0.2
              }}
            />
          ))}
        </motion.div>
      </div>

      {/* Background particles */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {[...Array(20)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-1 h-1 bg-muted-foreground/20 rounded-full"
            style={{
              left: `${(i * 5) % 100}%`,
              top: `${(i * 7) % 100}%`,
            }}
            animate={{
              y: [0, -100],
              opacity: [0, 1, 0]
            }}
            transition={{
              duration: 3 + (i % 3),
              repeat: Infinity,
              delay: (i % 5)
            }}
          />
        ))}
      </div>
    </motion.div>
  );
}

// Minimal loading screen for quick transitions
export function LoadingScreenMinimal({ duration = 500, onComplete }: LoadingScreenProps) {
  useEffect(() => {
    const timer = setTimeout(() => {
      if (onComplete) onComplete();
    }, duration);
    return () => clearTimeout(timer);
  }, [duration, onComplete]);

  return (
    <motion.div
      initial={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 bg-background flex items-center justify-center"
    >
      <div className="w-8 h-8 border-4 border-foreground border-t-transparent rounded-full animate-spin" />
    </motion.div>
  );
}