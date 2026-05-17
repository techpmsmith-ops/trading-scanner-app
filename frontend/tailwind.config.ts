import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: "#121721",
        panel: "#18202d",
        panelSoft: "#202a38",
        border: "#2d3747",
        ink: "#edf2f7",
        muted: "#9aa7b8",
        positive: "#2fd17c",
        caution: "#f5b84b",
        danger: "#ff6b6b"
      }
    }
  },
  plugins: [],
};

export default config;
