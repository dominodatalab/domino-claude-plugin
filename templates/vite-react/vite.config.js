import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Domino-compatible Vite configuration
// See: https://github.com/dominodatalab/domino-blueprints/tree/main/React-app-deployment-with-CICD

export default defineConfig({
  plugins: [react()],

  // CRITICAL: Use relative base path for Domino proxy compatibility
  // Without this, assets will 404 behind Domino's reverse proxy
  base: './',

  server: {
    // Bind to all interfaces so Domino can reach the app
    host: '0.0.0.0',
    // Default port for Domino apps (flexible - can use other ports)
    port: 8888,
    // Fail if port is unavailable (don't silently switch)
    strictPort: true,
  },

  preview: {
    host: '0.0.0.0',
    port: 8888,
    strictPort: true,
  },

  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  },
})
