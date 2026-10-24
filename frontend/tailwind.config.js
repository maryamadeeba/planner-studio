/** @type {import('tailwindcss').Config} */
// Productivity Shop by M brand palette
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1D4E5F",
        copy: "#35535E",
        cream: "#FFFCF8",
        sky: { DEFAULT: "#93E2F0", deep: "#2A93B3", soft: "#EAF8FC" },
        blush: { DEFAULT: "#F7C6D2", soft: "#FFF1F4" },
        butter: { DEFAULT: "#FFE59A", soft: "#FFF8E0" },
        sand: { 50: "#FFFCF8", 100: "#F8F4EE", 200: "#ECE5DC", 300: "#DCD3C8", 400: "#B3ABA2", 500: "#5E7A84" },
        brand: { 50: "#EAF8FC", 100: "#CDEFF6", 400: "#93E2F0", 500: "#2A93B3", 600: "#237F9C", 700: "#1D4E5F" },
        rose: { 50: "#FFF1F4", 500: "#B4596B" },
      },
      fontFamily: {
        sans: ["Poppins", "system-ui", "sans-serif"],
        display: ["'Playfair Display'", "serif"],
        hand: ["Caveat", "cursive"],
      },
    },
  },
  plugins: [],
};
