/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Deep noir foundation - 深邃的黑色基底
        noir: {
          950: '#07080a',
          900: '#0c0e12',
          850: '#111418',
          800: '#171b20',
          750: '#1d2228',
          700: '#242a31',
          600: '#333b45',
          500: '#4a5565',
          400: '#6b7a8a',
          300: '#95a3b3',
          200: '#c8d1db',
          100: '#e8ecf1',
        },
        // Warm brass accent - 黃銅色強調
        brass: {
          50: '#fefbeb',
          100: '#fdf4c7',
          200: '#fbe88f',
          300: '#f9d652',
          400: '#f5c023',
          500: '#d4a012',
          600: '#b8860b',
          700: '#926a0c',
          800: '#785511',
          900: '#654614',
        },
        // Jade for success - 翡翠色成功狀態
        jade: {
          50: '#f0fdf5',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
        },
        // Vermilion for errors - 朱紅色錯誤狀態
        vermilion: {
          400: '#fb7185',
          500: '#f43f5e',
          600: '#e11d48',
        },
        // Azure for info - 天藍色資訊狀態
        azure: {
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
        },
      },
      fontFamily: {
        // Display font - 優雅的襯線字體用於標題
        display: ['"Cormorant Garamond"', 'Georgia', 'serif'],
        // Body font - 清晰的無襯線字體
        sans: ['"Plus Jakarta Sans"', '"Noto Sans TC"', 'system-ui', 'sans-serif'],
        // Mono font - 等寬字體用於代碼和引用
        mono: ['"JetBrains Mono"', '"Fira Code"', 'Consolas', 'monospace'],
      },
      fontSize: {
        '2xs': ['0.65rem', { lineHeight: '0.875rem' }],
        'xs': ['0.75rem', { lineHeight: '1rem' }],
        'sm': ['0.875rem', { lineHeight: '1.25rem' }],
        'base': ['1rem', { lineHeight: '1.625rem' }],
        'lg': ['1.125rem', { lineHeight: '1.75rem' }],
        'xl': ['1.25rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['2rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.5rem', { lineHeight: '2.75rem' }],
        '5xl': ['3.25rem', { lineHeight: '1.15' }],
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '112': '28rem',
        '128': '32rem',
      },
      borderRadius: {
        '4xl': '2rem',
        '5xl': '2.5rem',
      },
      boxShadow: {
        'glow-brass': '0 0 30px -8px rgba(212, 160, 18, 0.25)',
        'glow-brass-lg': '0 0 50px -10px rgba(212, 160, 18, 0.35)',
        'inner-highlight': 'inset 0 1px 0 0 rgba(255, 255, 255, 0.06)',
        'card': '0 4px 32px -8px rgba(0, 0, 0, 0.5)',
        'card-hover': '0 8px 48px -12px rgba(0, 0, 0, 0.6)',
        'float': '0 20px 60px -20px rgba(0, 0, 0, 0.7)',
        'input': 'inset 0 2px 4px rgba(0, 0, 0, 0.2)',
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(var(--tw-gradient-stops))',
        'mesh': 'radial-gradient(at 40% 20%, rgba(212, 160, 18, 0.04) 0px, transparent 50%), radial-gradient(at 80% 80%, rgba(34, 197, 94, 0.03) 0px, transparent 50%), radial-gradient(at 0% 100%, rgba(59, 130, 246, 0.03) 0px, transparent 50%)',
        'noise': "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 512 512' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.7' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E\")",
      },
      animation: {
        'fade-in': 'fadeIn 0.4s ease-out forwards',
        'fade-in-up': 'fadeInUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'fade-in-down': 'fadeInDown 0.4s ease-out forwards',
        'slide-in-left': 'slideInLeft 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'slide-in-right': 'slideInRight 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'scale-in': 'scaleIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'pulse-soft': 'pulseSoft 2s ease-in-out infinite',
        'shimmer': 'shimmer 2.5s linear infinite',
        'thinking-dot': 'thinkingDot 1.4s ease-in-out infinite',
        'float': 'float 6s ease-in-out infinite',
        'glow-pulse': 'glowPulse 2s ease-in-out infinite',
        'spin-slow': 'spin 3s linear infinite',
        'bounce-subtle': 'bounceSubtle 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeInDown: {
          '0%': { opacity: '0', transform: 'translateY(-12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideInLeft: {
          '0%': { opacity: '0', transform: 'translateX(-24px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        slideInRight: {
          '0%': { opacity: '0', transform: 'translateX(24px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.92)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.6' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        thinkingDot: {
          '0%, 80%, 100%': { transform: 'scale(0.6)', opacity: '0.4' },
          '40%': { transform: 'scale(1)', opacity: '1' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-8px)' },
        },
        glowPulse: {
          '0%, 100%': { boxShadow: '0 0 20px -5px rgba(212, 160, 18, 0.3)' },
          '50%': { boxShadow: '0 0 40px -5px rgba(212, 160, 18, 0.5)' },
        },
        bounceSubtle: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-4px)' },
        },
      },
      transitionTimingFunction: {
        'out-expo': 'cubic-bezier(0.16, 1, 0.3, 1)',
        'out-back': 'cubic-bezier(0.34, 1.56, 0.64, 1)',
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
}
