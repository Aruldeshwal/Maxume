/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: {
          deep: "var(--bg-deep)",
          card: "var(--bg-card)",
          hover: "var(--bg-hover)",
        },
        legion: {
          crimson: "var(--accent-crimson)",
          darkcrimson: "var(--accent-darkcrimson)",
          neon: "var(--accent-neon)",
        },
        text: {
          primary: "var(--text-primary)",
          secondary: "var(--text-secondary)",
          muted: "var(--text-muted)",
        },
        border: {
          subtle: "var(--border-subtle)",
          strong: "var(--border-strong)",
        },
        status: {
          info: "var(--status-info)",
          success: "var(--status-success)",
          warning: "var(--status-warning)",
          error: "var(--status-error)",
        }
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Consolas", "monospace"],
        sans: ["Inter", "system-ui", "Segoe UI", "sans-serif"],
      }
    },
  },
  plugins: [],
}
