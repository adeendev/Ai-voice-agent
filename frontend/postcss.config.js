// Added so Tailwind actually compiles: the project ships tailwind.config.js and
// the tailwindcss dependency, but no PostCSS config, so the styles never build.
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
