import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        cyber: {
          darkest: "#07090e",
          bg: "#0a0d14",
          card: "#10141f",
          cardHover: "#161c2b",
          border: "#1e2638",
          borderBright: "#2a3650",
          emerald: "#10b981",
          emeraldGlow: "rgba(16, 185, 129, 0.15)",
          cyan: "#06b6d4",
          cyanGlow: "rgba(6, 182, 212, 0.15)",
          amber: "#f59e0b",
          amberGlow: "rgba(245, 158, 11, 0.15)",
          violet: "#8b5cf6",
          violetGlow: "rgba(139, 92, 246, 0.15)",
          rose: "#f43f5e",
        },
      },
      fontFamily: {
        mono: ["var(--font-geist-mono)", "monospace"],
        sans: ["var(--font-geist-sans)", "system-ui", "sans-serif"],
      },
      animation: {
        "pulse-fast": "pulse 1.2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "glow-pulse": "glowPulse 3s ease-in-out infinite",
        "ticker-scroll": "ticker 35s linear infinite",
      },
      keyframes: {
        glowPulse: {
          "0%, 100%": { opacity: "0.4" },
          "50%": { opacity: "0.9" },
        },
        ticker: {
          "0%": { transform: "translateX(0%)" },
          "100%": { transform: "translateX(-50%)" },
        },
      },
    },
  },
  plugins: [],
};
export default config;
