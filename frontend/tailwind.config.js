/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        meesho: '#1E3A8A',
        offwhite: '#F8FAFC',
        success: '#10B981',
        underline: '#F59E0B',
      },
    },
  },
  plugins: [],
}