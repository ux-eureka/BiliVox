import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 10086,
    strictPort: false,
    open: false,
    onListening(server) {
      console.log(`\n🚀 开发服务器已启动`)
      console.log(`   本地: http://localhost:${server.config.server.port}`)
      console.log(`   网络: http://${server.config.server.host}:${server.config.server.port}`)
      console.log(`\n💡 如果页面没有更新，请:`)
      console.log(`   1. 关闭旧的标签页`)
      console.log(`   2. 清除浏览器缓存 (Ctrl+Shift+R)`)
      console.log(`   3. 或者运行: npx kill-port 10086\n`)
    },
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
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['tests/setup/vitest.setup.js']
  }
})
