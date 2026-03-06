/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        display: ['JetBrains Mono', 'monospace'],
        body: ['IBM Plex Sans', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        surface: {
          primary: 'var(--bg-primary)',
          secondary: 'var(--bg-secondary)',
          tertiary: 'var(--bg-tertiary)',
          elevated: 'var(--bg-elevated)',
        },
        border: {
          subtle: 'var(--border-subtle)',
          DEFAULT: 'var(--border-default)',
          focus: 'var(--border-focus)',
        },
        content: {
          primary: 'var(--text-primary)',
          secondary: 'var(--text-secondary)',
          tertiary: 'var(--text-tertiary)',
        },
        accent: {
          indigo: 'var(--accent-indigo)',
          emerald: 'var(--accent-emerald)',
          amber: 'var(--accent-amber)',
          red: 'var(--accent-red)',
          cyan: 'var(--accent-cyan)',
          purple: 'var(--accent-purple)',
        },
        event: {
          llm: 'var(--event-llm)',
          tool: 'var(--event-tool)',
          decision: 'var(--event-decision)',
          memory: 'var(--event-memory)',
          error: 'var(--event-error)',
          user: 'var(--event-user)',
        },
      },
      animation: {
        'pulse-slow': 'pulse 3s ease-in-out infinite',
        'slide-in': 'slideIn 0.25s ease-out',
        'fade-in': 'fadeIn 0.2s ease-out',
      },
      keyframes: {
        slideIn: {
          '0%': { transform: 'translateX(20px)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(4px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
};
