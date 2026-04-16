/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        cyber: {
          dark: "#050505",
          card: "#0f0f12",
          cyan: "#00f3ff",
          magenta: "#ff00ff",
          red: "#ff003c",
          green: "#00ff9f",
        },
      },
      boxShadow: {
        'neon-cyan': '0 0 10px #00f3ff, 0 0 20px #00f3ff',
        'neon-red': '0 0 10px #ff003c, 0 0 20px #ff003c',
      }
    },
  },
  plugins: [],
};