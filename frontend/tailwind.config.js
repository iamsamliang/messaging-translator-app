/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Helvetica', 'Arial', 'sans-serif'],
      },
      backgroundImage: {
        hero: "url('/images/bg-image.webp')",
      },
    },
  },
  plugins: [],
}

