/**
 * Design Tokens for AI Agent UI
 * 
 * These tokens provide TypeScript access to design values.
 * CSS variables are the source of truth (in globals.css).
 * Use these for programmatic access in components.
 */

export const tokens = {
  colors: {
    // Semantic colors (reference CSS variables)
    primary: 'hsl(var(--primary))',
    secondary: 'hsl(var(--secondary))',
    destructive: 'hsl(var(--destructive))',
    muted: 'hsl(var(--muted))',
    accent: 'hsl(var(--accent))',
    
    // Status colors
    status: {
      success: '#4caf50',
      warning: '#ff9800',
      error: '#f44336',
      info: '#2196f3',
    },
    
    // Background references
    background: {
      light: '#ffffff',
      dark: '#1a1a2e', // Not pure black - better for OLED
    },
  },

  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    '2xl': '48px',
    '3xl': '64px',
  },

  borderRadius: {
    sm: 'calc(var(--radius) - 4px)',
    md: 'calc(var(--radius) - 2px)',
    lg: 'var(--radius)',
    xl: 'calc(var(--radius) + 4px)',
    full: '9999px',
  },

  typography: {
    fontFamily: {
      sans: 'var(--font-geist-sans), system-ui, sans-serif',
      mono: 'var(--font-geist-mono), monospace',
    },
    fontSize: {
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
      '2xl': '1.5rem',
    },
  },

  animation: {
    duration: {
      fast: '150ms',
      normal: '300ms',
      slow: '500ms',
    },
    easing: {
      default: 'cubic-bezier(0.4, 0, 0.2, 1)',
      spring: 'cubic-bezier(0.175, 0.885, 0.32, 1.275)',
    },
  },

  // Layout constants
  layout: {
    sidebarWidth: '250px',
    contextPanelWidth: '300px',
    headerHeight: '56px',
    statusBarHeight: '32px',
  },
} as const;

export type Tokens = typeof tokens;
