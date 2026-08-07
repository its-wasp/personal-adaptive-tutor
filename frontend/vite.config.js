import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.js',
    // Components are the point of this suite; config and entry files would
    // only dilute the coverage signal.
    coverage: {
      reporter: ['text', 'lcov'],
      include: ['src/**/*.{js,jsx}'],
      // Spec files would otherwise count themselves as covered source and
      // inflate the figure.
      exclude: ['src/main.jsx', 'src/test/**', '**/*.test.{js,jsx}'],
    },
  },
})
