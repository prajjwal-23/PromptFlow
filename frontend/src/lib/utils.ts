/**
 * Utility functions for premium UI components
 */

import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Combines class names with Tailwind CSS merge
 * @param inputs - Array of class values
 * @returns Combined class string
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Debounce function for performance optimization
 * @param func - Function to debounce
 * @param wait - Wait time in milliseconds
 * @returns Debounced function
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

/**
 * Format number with commas
 * @param num - Number to format
 * @returns Formatted string
 */
export function formatNumber(num: number): string {
  return num.toLocaleString();
}

/**
 * Generate random ID
 * @param length - ID length
 * @returns Random ID string
 */
export function generateId(length: number = 8): string {
  return Math.random().toString(36).substring(2, length + 2);
}

/**
 * Check if element is in viewport
 * @param element - DOM element
 * @returns Boolean indicating if element is in viewport
 */
export function isInViewport(element: HTMLElement): boolean {
  const rect = element.getBoundingClientRect();
  return (
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
  );
}

/**
 * Smooth scroll to element
 * @param element - DOM element or selector
 * @param offset - Offset from top
 */
export function smoothScrollTo(element: HTMLElement | string, offset: number = 0) {
  const target = typeof element === 'string' ? document.querySelector(element) : element;
  if (target) {
    const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - offset;
    window.scrollTo({
      top: targetPosition,
      behavior: 'smooth'
    });
  }
}

/**
 * Get CSS custom property value
 * @param property - CSS custom property name
 * @returns Property value
 */
export function getCssVariable(property: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(property).trim();
}

/**
 * Set CSS custom property value
 * @param property - CSS custom property name
 * @param value - Property value
 */
export function setCssVariable(property: string, value: string) {
  document.documentElement.style.setProperty(property, value);
}

/**
 * Format file size
 * @param bytes - File size in bytes
 * @returns Formatted file size string
 */
export function formatFileSize(bytes: number): string {
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  if (bytes === 0) return '0 Bytes';
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Capitalize first letter
 * @param str - String to capitalize
 * @returns Capitalized string
 */
export function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Truncate text
 * @param str - String to truncate
 * @param length - Maximum length
 * @param suffix - Suffix to add
 * @returns Truncated string
 */
export function truncate(str: string, length: number, suffix = '...'): string {
  if (str.length <= length) return str;
  return str.slice(0, length) + suffix;
}

/**
 * Deep merge objects (simplified version)
 * @param target - Target object
 * @param source - Source object
 * @returns Merged object
 */
export function deepMerge(target: Record<string, any>, source: Record<string, any>): Record<string, any> {
  const result = { ...target };
  
  for (const key in source) {
    if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
      result[key] = deepMerge(result[key] || {}, source[key]);
    } else {
      result[key] = source[key];
    }
  }
  
  return result;
}

/**
 * Create animation variants for Framer Motion
 * @param type - Animation type
 * @returns Animation variants
 */
export function createAnimationVariants(type: 'fade' | 'slide' | 'scale' | 'bounce') {
  const variants = {
    fade: {
      initial: { opacity: 0 },
      animate: { opacity: 1 },
      exit: { opacity: 0 }
    },
    slide: {
      initial: { opacity: 0, y: 20 },
      animate: { opacity: 1, y: 0 },
      exit: { opacity: 0, y: -20 }
    },
    scale: {
      initial: { opacity: 0, scale: 0.9 },
      animate: { opacity: 1, scale: 1 },
      exit: { opacity: 0, scale: 0.9 }
    },
    bounce: {
      initial: { opacity: 0, y: -20 },
      animate: { opacity: 1, y: 0 },
      exit: { opacity: 0, y: 20 }
    }
  };
  
  return variants[type];
}

/**
 * Get responsive breakpoint
 * @returns Current breakpoint
 */
export function getBreakpoint(): 'sm' | 'md' | 'lg' | 'xl' | '2xl' {
  const width = window.innerWidth;
  if (width >= 1536) return '2xl';
  if (width >= 1280) return 'xl';
  if (width >= 1024) return 'lg';
  if (width >= 768) return 'md';
  return 'sm';
}

/**
 * Check if device is mobile
 * @returns Boolean indicating if device is mobile
 */
export function isMobile(): boolean {
  return window.innerWidth < 768;
}

/**
 * Check if device supports touch
 * @returns Boolean indicating if device supports touch
 */
export function isTouchDevice(): boolean {
  return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
}

/**
 * Generate gradient colors
 * @param type - Gradient type
 * @returns Gradient CSS
 */
export function getGradient(type: 'primary' | 'secondary' | 'accent' | 'premium'): string {
  const gradients = {
    primary: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    secondary: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    accent: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    premium: 'linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)'
  };
  
  return gradients[type];
}

/**
 * Generate glass morphism CSS
 * @param opacity - Glass opacity
 * @param blur - Blur amount
 * @returns Glass CSS properties
 */
export function getGlassMorphism(opacity: number = 0.1, blur: number = 10): string {
  return `
    background: rgba(255, 255, 255, ${opacity});
    backdrop-filter: blur(${blur}px);
    -webkit-backdrop-filter: blur(${blur}px);
    border: 1px solid rgba(255, 255, 255, ${opacity * 2});
  `;
}