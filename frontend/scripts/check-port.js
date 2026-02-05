import { execSync } from 'child_process'
import os from 'os'

const PORT = 10086

function getPortInfo(port) {
  try {
    if (os.platform() === 'win32') {
      const result = execSync(`netstat -ano | findstr :${port}`).toString()
      if (result.includes('LISTENING')) {
        const lines = result.split('\n').filter(l => l.includes('LISTENING'))
        const match = lines[0].trim().match(/LISTENING\s+(\d+)/)
        if (match) {
          return { occupied: true, pid: match[1] }
        }
      }
    }
  } catch (e) {
    // 端口未被占用
  }
  return { occupied: false, pid: null }
}

const info = getPortInfo(PORT)

if (info.occupied) {
  console.log(`⚠️  端口 ${PORT} 已被占用 (PID: ${info.pid})`)
  console.log(`💡 解决方案:`)
  console.log(`   1. 如果 ${PORT} 端口的页面没更新，请关闭它:`)
  console.log(`      npx kill-port ${PORT}`)
  console.log(`   2. 或者使用新端口启动:`)
  console.log(`      vite --port ${PORT + 1}`)
  console.log(`\n🔍 检查旧端口页面是否有更新，请按 F12 打开控制台查看网络请求时间`)
} else {
  console.log(`✅ 端口 ${PORT} 未被占用，可以正常使用`)
}
