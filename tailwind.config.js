/** @type {import('tailwindcss').Config} */

export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    container: {
      center: true,
    },
    extend: {
      colors: {
        // 品牌主色：深森林绿
        forest: {
          50: "#ECFDF3",
          100: "#D1FAE0",
          200: "#A7F3C8",
          300: "#6EE7A3",
          400: "#34D27E",
          500: "#16A34A",
          600: "#0F7A3D",
          700: "#0F5132",
          800: "#0A3D26",
          900: "#062B1A",
        },
        // 能源/电费 - 暖琥珀
        energy: {
          50: "#FFFBEB",
          100: "#FEF3C7",
          400: "#FBBF24",
          500: "#D97706",
          600: "#B45309",
          700: "#92400E",
        },
        // 水务/水费 - 湖水蓝
        aqua: {
          50: "#ECFEFF",
          100: "#CFFAFE",
          400: "#22D3EE",
          500: "#0E7490",
          600: "#0E6A7F",
          700: "#155E75",
        },
        // 燃气 - 陶土红
        clay: {
          50: "#FEF3EC",
          100: "#FDE4D0",
          400: "#F59E5C",
          500: "#B45309",
          600: "#9A3F08",
          700: "#7C3308",
        },
        // 背景米白
        cream: "#FAF7F2",
        ink: {
          DEFAULT: "#1A2421",
          soft: "#3D4A45",
          muted: "#6B7670",
        },
      },
      fontFamily: {
        serif: ['"Noto Serif SC"', "Georgia", "serif"],
        sans: ['"Noto Sans SC"', "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 3px rgba(15,81,50,0.06), 0 8px 24px rgba(15,81,50,0.06)",
        cardHover: "0 4px 12px rgba(15,81,50,0.10), 0 16px 40px rgba(15,81,50,0.10)",
      },
      borderRadius: {
        xl: "12px",
        "2xl": "16px",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "scale-in": {
          "0%": { opacity: "0", transform: "scale(0.96)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.5s ease-out both",
        "scale-in": "scale-in 0.3s ease-out both",
      },
    },
  },
  plugins: [],
};
