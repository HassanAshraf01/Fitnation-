/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./gymapp/templates/**/*.{html,js}",   // Django templates
    "./gymapp/templates/**/*.{html,js}" // app-level templates (adjust if needed)
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
