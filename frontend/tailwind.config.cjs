/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        surface: 'rgb(var(--ui-surface) / <alpha-value>)',
        canvas: 'rgb(var(--ui-canvas) / <alpha-value>)',
        text: 'rgb(var(--ui-text) / <alpha-value>)',
        muted: 'rgb(var(--ui-muted) / <alpha-value>)',
        border: 'rgb(var(--ui-border) / <alpha-value>)',
        brand: {
          DEFAULT: 'rgb(var(--ui-brand) / <alpha-value>)',
          50: 'rgb(var(--ui-brand-50) / <alpha-value>)',
        },
        success: 'rgb(var(--ui-success) / <alpha-value>)',
        warning: 'rgb(var(--ui-warning) / <alpha-value>)',
        danger: 'rgb(var(--ui-danger) / <alpha-value>)',
      },
      borderRadius: {
        ui: 'var(--ui-radius)',
        'ui-lg': 'var(--ui-radius-lg)',
      },
      boxShadow: {
        ui: 'var(--ui-shadow)',
        'ui-lg': 'var(--ui-shadow-lg)',
      },
      spacing: {
        18: '72px',
      },
    },
  },
  plugins: [],
}
