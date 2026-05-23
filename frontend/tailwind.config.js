/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: "var(--ink)",
          soft: "var(--ink-soft)",
          mute: "var(--ink-mute)",
        },
        paper: "var(--paper)",
        line: "var(--line)",
        elev: "var(--elev)",
        frame: "var(--frame)",
        cat: {
          a: "#2743d6",
          b: "#d86b1f",
          c: "#111111",
          d: "#cfcfcf",
          e: "#2a8f4a",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
