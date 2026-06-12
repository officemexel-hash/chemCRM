import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1d2730",
        graphite: "#394650",
        mint: "#1f9d7a",
        amber: "#c77700",
        danger: "#b42318"
      }
    }
  },
  plugins: []
};

export default config;
