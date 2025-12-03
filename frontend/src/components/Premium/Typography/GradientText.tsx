/**
 * Gradient Text Component
 * 
 * Premium typography with animated gradient effects
 */

import { motion } from 'framer-motion';
import { ReactNode } from 'react';
// import { cn } from '@/lib/utils';
import { cn } from '../../../lib/utils';

interface GradientTextProps {
  children: ReactNode;
  gradient?: string;
  className?: string;
  animate?: boolean;
  as?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6' | 'p' | 'span';
}

export function GradientText({
  children,
  gradient = 'from-blue-600 via-purple-600 to-indigo-600',
  className,
  animate = false,
  as = 'span'
}: GradientTextProps) {
  const Component = motion[as] as React.ComponentType<any>;
  
  const gradientClasses = `bg-gradient-to-r ${gradient} bg-clip-text text-transparent`;
  
  const animationProps = animate ? {
    initial: { backgroundPosition: '0% 50%' },
    animate: { backgroundPosition: ['0% 50%', '100% 50%', '0% 50%'] },
    transition: { duration: 3, repeat: Infinity, ease: 'linear' }
  } : {};

  return (
    <Component
      className={cn(gradientClasses, className)}
      style={{
        backgroundSize: animate ? '200% 200%' : '100% 100%',
      }}
      {...animationProps}
    >
      {children}
    </Component>
  );
}

// Predefined gradient presets
export const gradientPresets = {
  primary: 'from-blue-600 via-purple-600 to-indigo-600',
  secondary: 'from-pink-500 via-red-500 to-yellow-500',
  accent: 'from-green-400 via-blue-500 to-purple-600',
  premium: 'from-violet-600 via-pink-600 to-orange-600',
  dark: 'from-gray-700 via-gray-800 to-gray-900',
  light: 'from-white via-gray-100 to-gray-200',
  sunset: 'from-orange-400 via-pink-500 to-purple-600',
  ocean: 'from-blue-400 via-cyan-500 to-teal-600',
  forest: 'from-green-400 via-emerald-500 to-teal-600',
  fire: 'from-red-500 via-orange-500 to-yellow-500'
};