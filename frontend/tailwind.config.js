/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'brand-red': { DEFAULT: '#E52320', dark: '#B91C1C' },
        'brand-yellow': { DEFAULT: '#FFC72C', dark: '#D99E00' },
        'brand-green': { DEFAULT: '#16A34A', dark: '#15803D' },
        'brand-dark': '#1C1C1A',
        'brand-bg': '#F8FAFC',
      },
    },
  },
  plugins: [],
}
