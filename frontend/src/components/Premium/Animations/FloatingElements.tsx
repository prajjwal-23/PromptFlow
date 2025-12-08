/**
 * Floating Elements Animation Component
 *
 * Creates floating UI elements that move smoothly across the screen
 */

import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';
import { Sparkles, Zap, Star, Diamond } from 'lucide-react';
// import { cn } from '@/lib/utils';
import { cn } from '../../../lib/utils';

interface FloatingElementsProps {
  count?: number;
  speed?: number;
  className?: string;
}

export function FloatingElements({
  count = 15,
  speed = 20,
  className
}: FloatingElementsProps) {
  const [elements, setElements] = useState<Array<{
    id: number;
    icon: React.ComponentType<{ className?: string }>;
    x: number;
    y: number;
    delay: number;
    duration: number;
    size: number;
  }>>(() => []);

  const icons = [Sparkles, Zap, Star, Diamond];

  useEffect(() => {
    const newElements = Array.from({ length: count }, (_, i) => ({
      id: i,
      icon: icons[i % icons.length],
      x: Math.random() * 100,
      y: Math.random() * 100,
      delay: Math.random() * speed,
      duration: speed + Math.random() * 10,
      size: 16 + Math.random() * 16
    }));
    
    setElements(newElements);
  }, [count, speed, icons]);

  const floatingVariants = {
    animate: (custom: { x: number; y: number; delay: number; duration: number }) => ({
      x: [custom.x + '%', (custom.x + 20) + '%', (custom.x - 20) + '%', custom.x + '%'],
      y: [custom.y + '%', (custom.y - 30) + '%', (custom.y + 30) + '%', custom.y + '%'],
      transition: {
        x: {
          duration: custom.duration,
          repeat: Infinity,
          ease: "easeInOut" as const,
          delay: custom.delay
        },
        y: {
          duration: custom.duration * 0.8,
          repeat: Infinity,
          ease: "easeInOut" as const,
          delay: custom.delay
        }
      }
    })
  };

  const opacityVariants = {
    animate: {
      opacity: [0.3, 0.8, 0.3],
      scale: [0.8, 1.2, 0.8],
      transition: {
        duration: 3,
        repeat: Infinity,
        ease: "easeInOut" as const
      }
    }
  };

  return (
    <div className={cn("absolute inset-0 pointer-events-none overflow-hidden", className)}>
      {elements.map((element) => (
        <motion.div
          key={element.id}
          className="absolute"
          custom={element}
          variants={floatingVariants}
          animate="animate"
          style={{
            left: `${element.x}%`,
            top: `${element.y}%`,
          }}
        >
          <motion.div
            variants={opacityVariants}
            animate="animate"
            className="relative"
          >
            <div className="text-primary/60" style={{
              filter: 'drop-shadow(0 0 10px hsl(var(--primary) / 0.3))',
              fontSize: `${element.size}px`
            }}>
              <element.icon className="w-full h-full" />
            </div>
            {/* Glow effect */}
            <div 
              className="absolute inset-0 bg-gradient-to-r from-primary to-accent rounded-full blur-xl opacity-30"
              style={{
                width: element.size * 2,
                height: element.size * 2,
                left: `-${element.size / 2}px`,
                top: `-${element.size / 2}px`,
              }}
            />
          </motion.div>
        </motion.div>
      ))}
    </div>
  );
}

// Simplified version for performance
export function FloatingElementsLite({ count = 8, className }: FloatingElementsProps) {
  return <FloatingElements count={count} speed={15} className={className} />;
}

// Minimal version for mobile
export function FloatingElementsMinimal({ count = 5, className }: FloatingElementsProps) {
  return <FloatingElements count={count} speed={25} className={className} />;
}