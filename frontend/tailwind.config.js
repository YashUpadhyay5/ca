/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ca: {
          navy: "#1E3A8A",
          dark: "#0F172A",
          card: "#1E293B",
          border: "#334155",
          accent: "#2563EB",
          emerald: "#059669",
          amber: "#D97706",
          rose: "#DC2626"
        }
      }
    },
  },
  plugins: [],
}
