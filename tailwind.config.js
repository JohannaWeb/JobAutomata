/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./templates/**/*.{html,js}",
    "./static/js/**/*.js",
    "./src/**/*.{html,js}",
  ],
  theme: {
    extend: {
      colors: {
        // Pastel pink + white theme
        primary: {
          50: '#fdf2f8',
          100: '#fce7f3',
          200: '#fbcfe8',
          300: '#f9a8d4',
          400: '#f472b6',
          500: '#ec4899',
          600: '#db2777',
          700: '#be185d',
          800: '#9d174d',
          900: '#831843',
        },
        // Neutral grays for text
        neutral: {
          50: '#faf7f5',
          100: '#f5f3f0',
          200: '#e8e4e0',
          300: '#d7cfc8',
          400: '#a39e96',
          500: '#6b6560',
          600: '#4a4440',
          700: '#3a3530',
          800: '#2d2824',
          900: '#1a1815',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
        display: ['Poppins', 'sans-serif'],
      },
      spacing: {
        '4.5': '1.125rem',
        '13': '3.25rem',
        '15': '3.75rem',
      },
      boxShadow: {
        subtle: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        sm: '0 2px 4px 0 rgba(0, 0, 0, 0.08)',
        md: '0 4px 8px 0 rgba(236, 72, 153, 0.08)',
        lg: '0 8px 16px 0 rgba(236, 72, 153, 0.12)',
        pink: '0 4px 12px 0 rgba(236, 72, 153, 0.2)',
      },
      animation: {
        'spin-slow': 'spin 1.5s linear infinite',
        'fade-in': 'fadeIn 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          'from': { opacity: '0', transform: 'translateY(4px)' },
          'to': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
