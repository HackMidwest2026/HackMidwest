import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// In dev, Vite proxies API calls to the Node server (API_URL, default localhost:8080).
const target = process.env.API_URL || 'http://localhost:8080'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/api': { target, changeOrigin: true },
      '/uploads': { target, changeOrigin: true },
    },
  },
})
