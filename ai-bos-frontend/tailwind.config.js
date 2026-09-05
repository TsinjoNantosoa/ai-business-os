/** @type {import('tailwindcss').Config} */
export default {
    content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
    darkMode: ['class', '[data-theme="dark"]'],
    theme: {
      extend: {
        colors: {
          border: 'hsl(var(--border))',
          input: 'hsl(var(--input))',
          ring: 'hsl(var(--ring))',
          background: 'hsl(var(--background))',
          foreground: 'hsl(var(--foreground))',
          primary: {
            DEFAULT: 'hsl(var(--primary))',
            foreground: 'hsl(var(--primary-foreground))',
            50: '#eef2ff',
            100: '#e0e7ff',
            200: '#c7d2fe',
            300: '#a5b4fc',
            400: '#818cf8',
            500: '#6366f1',
            600: '#4f46e5',
            700: '#4338ca',
            800: '#3730a3',
            900: '#312e81',
            950: '#1e1b4b',
          },
          secondary: {
            DEFAULT: 'hsl(var(--secondary))',
            foreground: 'hsl(var(--secondary-foreground))',
            50: '#f0fdfa',
            100: '#ccfbf1',
            200: '#99f6e4',
            300: '#5eead4',
            400: '#2dd4bf',
            500: '#14b8a6',
            600: '#0d9488',
            700: '#0f766e',
            800: '#115e59',
            900: '#134e4a',
          },
          accent: {
            DEFAULT: 'hsl(var(--accent))',
            foreground: 'hsl(var(--accent-foreground))',
          },
          muted: {
            DEFAULT: 'hsl(var(--muted))',
            foreground: 'hsl(var(--muted-foreground))',
          },
          destructive: {
            DEFAULT: 'hsl(var(--destructive))',
            foreground: 'hsl(var(--destructive-foreground))',
          },
          card: {
            DEFAULT: 'hsl(var(--card))',
            foreground: 'hsl(var(--card-foreground))',
          },
          popover: {
            DEFAULT: 'hsl(var(--popover))',
            foreground: 'hsl(var(--popover-foreground))',
          },
          success: {
            DEFAULT: '#19c891',
            foreground: '#ffffff',
          },
          warning: {
            DEFAULT: '#f59e0b',
            foreground: '#ffffff',
          },
          danger: {
            DEFAULT: '#ef4444',
            foreground: '#ffffff',
          },
          sidebar: {
            DEFAULT: 'hsl(var(--sidebar))',
            foreground: 'hsl(var(--sidebar-foreground))',
            muted: 'hsl(var(--sidebar-muted))',
            accent: 'hsl(var(--sidebar-accent))',
            border: 'hsl(var(--sidebar-border))',
          },
        },
        borderRadius: {
          sm: 'var(--radius-sm)',
          md: 'var(--radius-md)',
          lg: 'var(--radius-lg)',
          xl: 'var(--radius-xl)',
        },
        fontFamily: {
          sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        },
        fontSize: {
          '2xs': ['0.625rem', { lineHeight: '0.875rem' }],
        },
        boxShadow: {
          'soft': 'var(--shadow-soft)',
          'card': 'var(--shadow-card)',
          'elevated': 'var(--shadow-elevated)',
          'floating': 'var(--shadow-floating)',
          'ai': 'var(--shadow-ai)',
        },
        keyframes: {
          'fade-in': {
            from: { opacity: '0' },
            to: { opacity: '1' },
          },
          'fade-in-up': {
            from: { opacity: '0', transform: 'translateY(8px)' },
            to: { opacity: '1', transform: 'translateY(0)' },
          },
          'slide-in-right': {
            from: { transform: 'translateX(100%)' },
            to: { transform: 'translateX(0)' },
          },
          'scale-in': {
            from: { opacity: '0', transform: 'scale(0.96)' },
            to: { opacity: '1', transform: 'scale(1)' },
          },
          'shimmer': {
            '100%': { transform: 'translateX(100%)' },
          },
          'pulse-soft': {
            '0%, 100%': { opacity: '1' },
            '50%': { opacity: '0.6' },
          },
        },
        animation: {
          'fade-in': 'fade-in 0.2s ease-out',
          'fade-in-up': 'fade-in-up 0.3s ease-out',
          'slide-in-right': 'slide-in-right 0.3s ease-out',
          'scale-in': 'scale-in 0.15s ease-out',
          'shimmer': 'shimmer 1.5s infinite',
          'pulse-soft': 'pulse-soft 2s ease-in-out infinite',
        },
      },
    },
    plugins: [],
  };
  
