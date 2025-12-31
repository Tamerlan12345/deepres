/** @type {import('tailwindcss').Config} */
import typography from '@tailwindcss/typography';

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class', // Enable class-based dark mode
  theme: {
    extend: {
      colors: {
        // Professional Dark Mode Palette
        // Using Slate for a neutral, high-quality dark theme
        brand: {
          950: '#020617', // Very deep background
          900: '#0f172a', // Sidebar / Card background
          800: '#1e293b', // Hover states / Secondary cards
          700: '#334155', // Borders / Dividers
          600: '#475569', // Subtle text
          500: '#64748b', // Main text
          400: '#94a3b8', // Light text
          300: '#cbd5e1', // Lighter text
          200: '#e2e8f0', // Very light text
          100: '#f1f5f9', // Highlights
          50: '#f8fafc',  // White text equivalent
        },
        accent: {
          DEFAULT: '#3b82f6', // Bright Blue (easier to read on dark)
          hover: '#2563eb',   // Darker Blue hover
          glow: 'rgba(59, 130, 246, 0.5)', // Glow effect
        },
        success: {
          DEFAULT: '#10b981', // Emerald
          bg: 'rgba(16, 185, 129, 0.1)',
        },
        warning: {
          DEFAULT: '#f59e0b', // Amber
          bg: 'rgba(245, 158, 11, 0.1)',
        },
        error: {
          DEFAULT: '#ef4444', // Red
          bg: 'rgba(239, 68, 68, 0.1)',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Menlo', 'monospace'], // For data/code
      },
      boxShadow: {
        'card': '0 4px 6px -1px rgba(0, 0, 0, 0.5), 0 2px 4px -1px rgba(0, 0, 0, 0.3)', // Deeper shadow for dark mode
        'glow': '0 0 15px rgba(59, 130, 246, 0.3)', // Accent glow
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        }
      }
    },
  },
  plugins: [
    typography,
  ],
}
