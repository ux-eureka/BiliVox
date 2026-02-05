import { execSync } from 'child_process'
import os from 'os'

const PORT = process.argv[2] || 10086

function killPort(port) {
  try {
    if (os.platform() === 'win32') {
      const result = execSync(`netstat -ano | findstr :${port}`).toString()
      if (result.includes('LISTENING')) {
        const lines = result.split('\n').filter(l => l.includes('LISTENING'))
        const match = lines[0].trim().match(/LISTENING\s+(\d+)/)
        if (match) {
          const pid = match[1]
          console.log(`正在关闭端口 ${port} (PID: ${pid})...`)
          execSync(`taskkill /F /PID ${pid}`)
          console.log(`✅ 端口 ${port} 已关闭`)
          return
        }
      }
      console.log(`⚠️ 端口 ${port} 未被占用`)
    }
  } catch (e) {
    if (e.message.includes('no such process')) {
      console.log(`⚠️ 端口 ${port} 未被占用`)
    } else {
      console.error(`❌ 关闭失败:`, e.message)
    }
  }
}

killPort(PORT)
