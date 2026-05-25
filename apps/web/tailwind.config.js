/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        card: "var(--card)",
        border: "var(--border)",
        primary: "var(--primary)",
        success: "var(--success)",
        warning: "var(--warning)",
        danger: "var(--danger)",
        muted: "var(--muted)",
        "hero-bg": "#141414",
        sentinel: {
          background: "hsl(0 0% 10%)",
          foreground: "hsl(0 0% 96%)",
          primary: "hsl(119 99% 46%)",
          "primary-foreground": "hsl(0 0% 4%)",
          secondary: "hsl(0 0% 18%)",
          muted: "hsl(0 0% 16%)",
          "muted-foreground": "hsl(0 0% 60%)",
          border: "hsl(0 0% 20%)",
          input: "hsl(0 0% 20%)",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "Inter", "sans-serif"],
        sora: ["var(--font-sora)", "Sora", "sans-serif"],
      },
    },
  },
  plugins: [],
}
