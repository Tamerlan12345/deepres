/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Corporate palette "Enterprise Blue"
        brand: {
          900: '#0f172a', // Main sidebar background (Deep Navy)
          800: '#1e293b', // Secondary background / active elements
          700: '#334155', // Borders and dividers
          600: '#475569', // Headers text
          500: '#64748b', // Main text
          400: '#94a3b8', // Added for scrollbar hover / icons
          300: '#cbd5e1', // Added for scrollbar / borders
          200: '#e2e8f0', // Added for card borders / light backgrounds
          100: '#f1f5f9', // Workspace background (Light Slate)
          50: '#f8fafc',  // Card background
        },
        accent: {
          DEFAULT: '#2563eb', // Corporate blue (for buttons)
          hover: '#1d4ed8',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'], // Strict font
      },
      boxShadow: {
        'card': '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)', // Subtle shadow
      }
    },
  },
  plugins: [],
}
