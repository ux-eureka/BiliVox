#!/usr/bin/env node
/**
 * Vue 文件语法检查脚本
 * 运行方式: node scripts/check-vue-syntax.cjs
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
  let hasError = false
  
  console.log(`\n🔍 检查: ${filePath}`)
  
  // 提取 <script> 或 <script setup> 块内容进行检查
  const scriptMatch = content.match(/<script[^>]*>[\s\S]*?<\/script>/)
  if (!scriptMatch) {
    console.log(`  ℹ️ 未找到 <script> 块`)
    return true
  }
  
  const scriptContent = scriptMatch[0]
  
  // 检查方括号闭合
  const openBrackets = (scriptContent.match(/\[/g) || []).length
  const closeBrackets = (scriptContent.match(/\]/g) || []).length
  if (openBrackets !== closeBrackets) {
    console.error(`  ❌ 方括号: 开启${openBrackets} != 关闭${closeBrackets}`)
    hasError = true
  }
  
  // 检查圆括号闭合
  const openParens = (scriptContent.match(/\(/g) || []).length
  const closeParens = (scriptContent.match(/\)/g) || []).length
  if (openParens !== closeParens) {
    console.error(`  ❌ 圆括号: 开启${openParens} != 关闭${closeParens}`)
    hasError = true
  }
  
  // 检查花括号闭合
  const openBraces = (scriptContent.match(/\{/g) || []).length
  const closeBraces = (scriptContent.match(/\}/g) || []).length
  if (openBraces !== closeBraces) {
    console.error(`  ❌ 花括号: 开启${openBraces} != 关闭${closeBraces}`)
    hasError = true
  }
  
  // 检查模板字符串闭合
  const backticks = (scriptContent.match(/`/g) || []).length
  if (backticks % 2 !== 0) {
    console.error(`  ❌ 模板字符串: 数量${backticks}不是偶数`)
    hasError = true
  }
  
  if (!hasError) {
    console.log(`  ✅ 语法检查通过`)
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
