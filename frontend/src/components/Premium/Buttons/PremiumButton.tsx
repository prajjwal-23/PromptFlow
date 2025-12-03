/**
 * Premium Button Component
 * 
 * Industry-standard button with glass morphism, gradients, and smooth animations
 */

import { useState } from 'react';
import { motion, MotionProps } from 'framer-motion';
// import { cn } from '@/lib/utils';
import { cn } from '../../../lib/utils';

interface PremiumButtonProps extends MotionProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'glass' | 'gradient';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  onClick?: () => void;
  disabled?: boolean;
  loading?: boolean;
  className?: string;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
  glow?: boolean;
}

export function PremiumButton({
  children,
  variant = 'primary',
  size = 'md',
  onClick,
  disabled = false,
  loading = false,
  className,
  icon,
  iconPosition = 'left',
  fullWidth = false,
  glow = false,
  ...motionProps
}: PremiumButtonProps) {
  const [isHovered, setIsHovered] = useState(false);

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
    xl: 'px-8 py-4 text-xl'
  };

  const variantClasses = {
    primary: `
      bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600
      hover:from-blue-500 hover:via-purple-500 hover:to-indigo-500
      text-white shadow-lg shadow-blue-500/25
      hover:shadow-xl hover:shadow-purple-500/40
      active:scale-95
    `,
    secondary: `
      bg-white/10 backdrop-blur-md border border-white/20
      hover:bg-white/20 hover:border-white/30
      text-white shadow-lg
      active:scale-95
    `,
    glass: `
      bg-white/5 backdrop-blur-xl border border-white/10
      hover:bg-white/10 hover:border-white/20
      text-white shadow-2xl
      active:scale-95
    `,
    gradient: `
      bg-gradient-to-r from-emerald-500 via-teal-500 to-cyan-500
      hover:from-emerald-400 hover:via-teal-400 hover:to-cyan-400
      text-white shadow-lg shadow-emerald-500/25
      hover:shadow-xl hover:shadow-teal-500/40
      active:scale-95
    `
  };

  const glowClasses = glow ? `
    before:content-[''] before:absolute before:inset-0 before:rounded-xl
    before:bg-gradient-to-r before:from-blue-500 before:via-purple-500 before:to-indigo-500
    before:opacity-0 before:blur-xl before:transition-all before:duration-500
    hover:before:opacity-30
  ` : '';

  return (
    <motion.button
      onClick={onClick}
      disabled={disabled || loading}
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      className={cn(
        'relative inline-flex items-center justify-center',
        'font-semibold rounded-xl transition-all duration-300',
        'focus:outline-none focus:ring-2 focus:ring-offset-2',
        'focus:ring-blue-500 focus:ring-offset-gray-900',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        'overflow-hidden group',
        sizeClasses[size],
        variantClasses[variant],
        glowClasses,
        fullWidth ? 'w-full' : '',
        className
      )}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      {...motionProps}
    >
      {/* Loading overlay */}
      {loading && (
        <motion.div
          className="absolute inset-0 bg-white/20 backdrop-blur-sm"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          </div>
        </motion.div>
      )}

      {/* Gradient overlay for glass effect */}
      {variant === 'glass' && (
        <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent opacity-50" />
      )}

      {/* Icon and content */}
      <div className={cn(
        'flex items-center gap-2',
        'transition-all duration-300',
        loading && 'opacity-0'
      )}>
        {icon && iconPosition === 'left' && (
          <motion.span
            animate={{ rotate: isHovered ? 360 : 0 }}
            transition={{ duration: 0.5 }}
          >
            {icon}
          </motion.span>
        )}
        
        <span className="relative z-10">{children}</span>
        
        {icon && iconPosition === 'right' && (
          <motion.span
            animate={{ rotate: isHovered ? -360 : 0 }}
            transition={{ duration: 0.5 }}
          >
            {icon}
          </motion.span>
        )}
      </div>

      {/* Ripple effect on click */}
      <motion.span
        className="absolute inset-0 bg-white/20 rounded-xl"
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 2, opacity: 0 }}
        transition={{ duration: 0.6 }}
        onAnimationComplete={() => {}}
      />
    </motion.button>
  );
}

// Premium button variants for common use cases
export const PremiumButtonPrimary = (props: Omit<PremiumButtonProps, 'variant'>) => (
  <PremiumButton variant="primary" {...props} />
);

export const PremiumButtonGlass = (props: Omit<PremiumButtonProps, 'variant'>) => (
  <PremiumButton variant="glass" {...props} />
);

export const PremiumButtonGradient = (props: Omit<PremiumButtonProps, 'variant'>) => (
  <PremiumButton variant="gradient" {...props} />
);