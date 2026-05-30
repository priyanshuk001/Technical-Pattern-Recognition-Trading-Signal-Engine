/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bullish: '#10b981',
        bearish: '#ef4444',
      }
    },
  },
  plugins: [],
}
