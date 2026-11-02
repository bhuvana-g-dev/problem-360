/** Problem 360 design tokens — palette is fixed by the master prompt. */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        brand: '#0F6B4E',   // primary deep green
        leaf: '#22C55E',    // secondary green (fills/accents; not for text on white)
        gold: '#F59E0B',    // accent golden yellow (highlights; pair with ink text)
        info: '#1D4ED8',    // information blue
        surface: '#F5FAF7', // page background
        ink: '#172B24',     // main text
      },
      fontFamily: {
        heading: ['Poppins', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      borderRadius: { card: '1rem' },
      boxShadow: { card: '0 1px 2px rgba(23,43,36,.06), 0 4px 16px rgba(23,43,36,.06)' },
    },
  },
  plugins: [],
}
