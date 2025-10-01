import type { Config } from "tailwindcss";
import typography from "@tailwindcss/typography";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./content/**/*.{md,mdx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#5CE1E6",
          dark: "#2C8F93"
        },
        accent: "#FFD166",
        surface: "#0B101B",
        'surface-muted': "#151B2D"
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"]
      }
    }
  },
  plugins: [typography]
};

export default config;
