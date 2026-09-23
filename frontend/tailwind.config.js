/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#0077ff',
          hover: '#0066dd',
          light: '#e8f3ff',
          lighter: '#f0f8ff',
        },
        'page-bg': '#f5f6f8',
        'panel-border': '#e5e6eb',
        'text-main': '#1d2129',
        'text-sub': '#4e5969',
        'text-hint': '#86909c',
      },
      boxShadow: {
        card: '0 1px 2px rgba(0,0,0,0.04), 0 2px 8px rgba(0,0,0,0.04)',
        'card-hover': '0 2px 6px rgba(0,0,0,0.06), 0 6px 20px rgba(0,0,0,0.08)',
        pop: '0 6px 16px rgba(0,0,0,0.08), 0 3px 6px -4px rgba(0,0,0,0.12)',
      },
      borderRadius: {
        panel: '8px',
        'panel-lg': '12px',
      },
    },
  },
  plugins: [],
};
