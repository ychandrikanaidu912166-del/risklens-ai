/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#0a0e13",
          900: "#0f141b",
          800: "#151c25",
          700: "#1c2531",
          600: "#25313f",
          500: "#3a4757",
          400: "#5c6b7d",
          300: "#8a97a9",
          200: "#c1cad4",
          100: "#e8edf2",
        },
        risk: {
          low: "#16a34a",
          medium: "#eab308",
          high: "#f97316",
          critical: "#dc2626",
        },
        brand: {
          500: "#3b82f6",
          600: "#2563eb",
        },
      },
      fontFamily: {
        sans: [
          "InterVariable",
          "Inter",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      fontSize: {
        "2xs": ["0.6875rem", "1rem"],
      },
      boxShadow: {
        card: "0 1px 2px 0 rgb(0 0 0 / 0.04), 0 1px 3px 0 rgb(0 0 0 / 0.05)",
      },
    },
  },
  plugins: [],
};
