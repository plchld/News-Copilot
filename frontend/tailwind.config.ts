import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Premium Color System - Refined aesthetics
        black: '#0F0F10', // Rich textured dark
        gray: {
          950: '#0A0A0B', // Deep shadow
          900: '#1A1A1B', // Cards
          800: '#2A2A2B', // Borders
          700: '#3A3A3B', // Hover states
          600: '#4A4A4B', // Subtle elements
          500: '#6B7280', // Secondary text
          400: '#8B8B8D', // Premium gray for taglines
          300: '#9CA3AF', // Tertiary text
          200: '#E5E7EB', // Light elements
          100: '#F3F4F6', // Very light
          50: '#F9FAFB', // Nearly white
        },
        white: '#FFFFFF',

        // Category colors
        tech: '#3B82F6',
        politics: '#EF4444',
        business: '#10B981',
        world: '#8B5CF6',
        culture: '#F59E0B',
        health: '#EC4899',
        science: '#06B6D4',
        // Existing colors
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93bbfd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
          950: '#172554',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        serif: ['Fraunces', 'Crimson Pro', 'serif'],
      },
      fontSize: {
        xs: ['0.75rem', { lineHeight: '1rem' }], // 12px - Metadata
        sm: ['0.875rem', { lineHeight: '1.25rem' }], // 14px - Category tags
        base: ['1rem', { lineHeight: '1.5rem' }], // 16px - Body text
        lg: ['1.125rem', { lineHeight: '1.75rem' }], // 18px - Card summaries
        xl: ['1.5rem', { lineHeight: '2rem' }], // 24px - Card headlines
        '2xl': ['2rem', { lineHeight: '2.5rem' }], // 32px - Expanded headlines
        '3xl': ['3rem', { lineHeight: '3.5rem' }], // 48px - Hero text
        '4xl': ['4.5rem', { lineHeight: '5rem' }], // 72px - Landing page
      },
      lineHeight: {
        tight: '1.25', // Headlines
        normal: '1.5', // Body text
        relaxed: '1.75', // Card summaries
      },
      spacing: {
        '180': '180px', // Exact card height specification
      },
      borderRadius: {
        sm: '8px', // buttons
        md: '12px', // cards
        lg: '16px', // modals
      },
      zIndex: {
        base: '10',
        elevated: '20',
        modal: '30',
        tooltip: '40',
        top: '50',
      },
      animation: {
        'spin-slow': 'spin 3s linear infinite',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'fade-in-up': 'fadeInUp 0.5s ease-out',
        glow: 'glow 3s ease-in-out infinite',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        glow: {
          '0%, 100%': {
            boxShadow:
              '0 0 20px rgba(59, 130, 246, 0.3), inset 0 0 20px rgba(59, 130, 246, 0.1)',
          },
          '50%': {
            boxShadow:
              '0 0 30px rgba(59, 130, 246, 0.4), inset 0 0 30px rgba(59, 130, 246, 0.2)',
          },
        },
        slideUp: {
          '0%': { transform: 'translateY(100%)' },
          '100%': { transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [require('@tailwindcss/forms'), require('@tailwindcss/typography')],
};

export default config;
