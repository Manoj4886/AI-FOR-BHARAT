import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Proxy API calls to FastAPI in dev
      '/ask': 'http://localhost:8000',
      '/quiz': 'http://localhost:8000',
      '/progress': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    }
  }
})
