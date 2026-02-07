#!/usr/bin/env node
/**
 * Vue 文件语法检查脚本
 * 运行方式: node scripts/check-vue-syntax.js
 */

const fs = require('fs')
const path = require('path')

const VUE_FILES = [
  'src/views/ControlPanel.vue',
  'src/views/Files.vue',
  'src/views/History.vue',
  'src/views/Config.vue',
  'src/components/VirtualScrollList.vue',
  'src/components/SystemLogs.vue',
  'src/App.vue'
]

function checkVueSyntax(filePath) {
  const fullPath = path.resolve(__dirname, '..', filePath)
  
  if (!fs.existsSync(fullPath)) {
    console.error(`❌ 文件不存在: ${filePath}`)
    return false
  }
  
  const content = fs.readFileSync(fullPath, 'utf8')
  const lines = content.split('\n')
  let hasError = false
  
  // 检查常见的Vue/Script语法错误
  const checks = [
    {
      name: 'computed函数闭合',
      pattern: /const \w+ = computed\(\(\) => \[/g,
      check: (matches) => {
        const openCount = (content.match(/const \w+ = computed\(\(\) => \[/g) || []).length
        const closeCount = (content.match(/\]\)/g) || []).length
        if (openCount !== closeCount) {
          console.error(`  ❌ computed函数数组: 开启${openCount} != 关闭${closeCount}`)
          return false
        }
        return true
      }
    },
    {
      name: '箭头函数闭合',
      pattern: /\([^)]*\) => \{/g,
      check: (matches) => {
        const opens = (content.match(/\([^)]*\) => \{/g) || []).length
        const closes = (content.match(/\}\)/g) || []).length
        if (opens !== closes) {
          console.error(`  ❌ 箭头函数: 开启${opens} != 关闭${closes}`)
          return false
        }
        return true
      }
    },
    {
      name: '模板字符串闭合',
      pattern: /`/g,
      check: () => {
        const count = (content.match(/`/g) || []).length
        if (count % 2 !== 0) {
          console.error(`  ❌ 模板字符串: 数量${count}不是偶数`)
          return false
        }
        return true
      }
    },
    {
      name: '括号闭合',
      pattern: /\(/g,
      check: () => {
        const opens = (content.match(/\(/g) || []).length
        const closes = (content.match(/\)/g) || []).length
        if (opens !== closes) {
          console.error(`  ❌ 括号: 开启${opens} != 关闭${closes}`)
          return false
        }
        return true
      }
    },
    {
      name: '方括号闭合',
      pattern: /\[/g,
      check: () => {
        const opens = (content.match(/\[/g) || []).length
        const closes = (content.match(/\]/g) || []).length
        if (opens !== closes) {
          console.error(`  ❌ 方括号: 开启${opens} != 关闭${closes}`)
          return false
        }
        return true
      }
    },
    {
      name: '花括号闭合',
      pattern: /\{/g,
      check: () => {
        const opens = (content.match(/\{/g) || []).length
        const closes = (content.match(/\}/g) || []).length
        if (opens !== closes) {
          console.error(`  ❌ 花括号: 开启${opens} != 关闭${closes}`)
          return false
        }
        return true
      }
    }
  ]
  
  console.log(`\n🔍 检查: ${filePath}`)
  
  for (const check of checks) {
    if (!check.check()) {
      hasError = true
    }
  }
  
  if (!hasError) {
    console.log(`  ✅ ${filePath} 语法检查通过`)
  }
  
  return !hasError
}

function main() {
  console.log('='.repeat(60))
  console.log('Vue 文件语法检查')
  console.log('='.repeat(60))
  
  let allPassed = true
  
  for (const file of VUE_FILES) {
    if (!checkVueSyntax(file)) {
      allPassed = false
    }
  }
  
  console.log('\n' + '='.repeat(60))
  if (allPassed) {
    console.log('✅ 所有文件语法检查通过!')
    process.exit(0)
  } else {
    console.log('❌ 发现语法错误，请修复后重试')
    process.exit(1)
  }
}

main()
