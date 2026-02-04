import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173, // 前端开发服务器端口，与后端分开
    strictPort: false,
    open: true,
    proxy: {
      '/api': {
        target: 'http://localhost:10086', // 统一后端端口为 10086
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
