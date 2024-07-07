/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/*"],
  theme: {
    extend: {},
  },
  plugins: [],
}

// npx tailwindcss -i ./static/src/input.css -o ./static/style/output.css --watch