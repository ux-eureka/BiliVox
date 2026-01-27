import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 10086,
    strictPort: true,
    open: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
    }
  },
  css: {
    preprocessorOptions: {
      sass: {
        additionalData: `@import "vuetify/styles"`
      }
    }
  }
})
