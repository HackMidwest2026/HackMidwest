import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// In dev, Vite proxies API calls to the Node server (API_URL, default localhost:8080).
const target = process.env.API_URL || 'http://localhost:8080'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: true,
    port: 5173,
    // In Docker Desktop (Mac/Windows), file events from bind mounts often don't reach the
    // container, so Vite would miss edits and new files in public/ (which it only learns about
    // from those events). docker-compose.dev.yml sets VITE_USE_POLLING to check files on a timer.
    watch: process.env.VITE_USE_POLLING === 'true' ? { usePolling: true, interval: 500 } : undefined,
    proxy: {
      '/api': { target, changeOrigin: true },
      '/uploads': { target, changeOrigin: true },
    },
  },
})
