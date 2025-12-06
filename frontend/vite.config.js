import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        // Use IPv4 loopback to avoid IPv6 (::1) connection issues on some systems
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
})
