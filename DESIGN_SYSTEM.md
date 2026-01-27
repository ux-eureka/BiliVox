# BiliVox 设计系统

## 1. 设计系统概述

BiliVox 设计系统基于 Google 的 Material 3 设计原则，结合 Vue 3 + Vuetify 3 组件库，为 BiliVox 项目提供一致、现代、直观的用户界面。

### 设计理念
- **以用户为中心**：优先考虑用户体验和可用性
- **现代美学**：遵循 Material 3 的现代设计语言
- **一致性**：在整个应用中保持视觉和交互的一致性
- **响应式**：确保在不同设备上都能提供良好的体验
- **可访问性**：遵循无障碍设计原则，确保所有用户都能使用

## 2. 色彩方案

### 主色调
- **Primary (主要色)**：蓝色系 (#3b82f6) - 用于主要按钮、强调元素
- **Secondary (次要色)**：紫色系 (#8b5cf6) - 用于次要按钮、辅助元素
- **Success (成功)**：绿色系 (#10b981) - 用于成功状态、确认按钮
- **Error (错误)**：红色系 (#ef4444) - 用于错误状态、删除按钮
- **Warning (警告)**：黄色系 (#f59e0b) - 用于警告状态
- **Info (信息)**：青色系 (#06b6d4) - 用于信息提示

### 中性色
- **Background (背景)**：#f8fafc
- **Surface (表面)**：#ffffff
- **Surface Variant (表面变体)**：#f1f5f9
- **Border (边框)**：#e2e8f0
- **Text Primary (主要文本)**：#1e293b
- **Text Secondary (次要文本)**：#64748b
- **Text Disabled (禁用文本)**：#94a3b8

## 3. 排版系统

### 字体
- **主要字体**：系统默认无衬线字体
- **代码字体**：Courier New, Courier, monospace

### 字号层级
- **h1 (大标题)**：2.5rem (40px) - 用于应用标题
- **h2 (中标题)**：2rem (32px) - 用于页面标题
- **h3 (小标题)**：1.5rem (24px) - 用于卡片标题
- **h4 (副标题)**：1.25rem (20px) - 用于区域标题
- **body-1 (正文)**：1rem (16px) - 用于主要文本
- **body-2 (次要文本)**：0.875rem (14px) - 用于次要文本
- **caption (说明文字)**：0.75rem (12px) - 用于说明、标签

### 字重
- **Bold (粗体)**：600 - 用于标题、强调文本
- **Medium (中等)**：500 - 用于按钮文本、重要信息
- **Regular (常规)**：400 - 用于正文、普通文本

## 4. 组件使用指南

### 按钮
- **主要按钮**：使用 `color="primary" variant="elevated"` - 用于主要操作
- **次要按钮**：使用 `color="secondary" variant="outlined"` - 用于次要操作
- **文本按钮**：使用 `color="primary" variant="text"` - 用于辅助操作
- **图标按钮**：使用 `icon` 属性 - 用于空间有限的场景

### 卡片
- **主要卡片**：使用 `variant="elevated"` - 用于主要内容区域
- **次要卡片**：使用 `variant="outlined"` - 用于次要内容区域
- **卡片阴影**：根据层级使用不同的 `elevation` 值
  - 常规：`elevation="2"`
  - 悬停：`elevation="8"` 或 `elevation="12"`

### 表单元素
- **输入框**：使用 `variant="outlined" density="comfortable"`
- **选择器**：使用 `variant="outlined" density="comfortable"`
- **滑块**：使用 `color="primary" density="comfortable"`

### 导航
- **面包屑**：使用 `<v-breadcrumbs>` 组件，显示当前页面路径
- **选项卡**：使用 `<v-tabs>` 组件，用于页面内导航
- **导航抽屉**：使用 `<v-navigation-drawer>` 组件，用于应用级导航

### 状态反馈
- **警告框**：使用 `<v-alert>` 组件，用于信息、警告、错误提示
- **对话框**：使用 `<v-dialog>` 组件，用于需要用户确认的操作
- **通知**：使用 `<v-snackbar>` 组件，用于操作结果反馈
- **加载状态**：使用 `<v-progress-circular>` 组件，用于加载过程

## 5. 响应式设计原则

### 断点系统
- **xs (超小)**：< 600px - 手机
- **sm (小)**：600px - 960px - 平板
- **md (中)**：960px - 1280px - 小型桌面
- **lg (大)**：1280px - 1920px - 中型桌面
- **xl (超大)**：> 1920px - 大型桌面

### 布局策略
- **移动优先**：从移动设备开始设计，然后扩展到更大的屏幕
- **弹性布局**：使用 Flexbox 和 Grid 系统
- **自适应组件**：根据屏幕尺寸调整组件大小和布局
- **内容优先级**：在小屏幕上优先显示重要内容

### 响应式网格
- **移动设备**：1 列布局
- **平板设备**：2 列布局
- **桌面设备**：3-4 列布局

## 6. 动画和交互规范

### 动画原则
- **目的明确**：动画应该有明确的目的，不是为了动画而动画
- **适度使用**：避免过度使用动画，以免分散用户注意力
- **平滑过渡**：确保动画过渡平滑自然
- **性能优化**：优先使用 CSS 动画，避免 JavaScript 动画影响性能

### 常用动画
- **页面过渡**：使用 `scale-transition` 或 `fade-transition`
- **卡片悬停**：使用 `transition-all duration-300 hover:elevation-8`
- **按钮交互**：使用 `transition-all duration-200 hover:scale-105`
- **加载动画**：使用 `v-progress-circular` 的旋转动画

### 交互反馈
- **点击反馈**：按钮点击时应有视觉反馈
- **悬停效果**：鼠标悬停在可交互元素上时应有状态变化
- **滚动效果**：平滑滚动，避免突兀的滚动行为
- **表单验证**：实时表单验证，提供清晰的错误提示

## 7. 可访问性标准

### 基本标准
- **键盘导航**：确保所有功能都可以通过键盘访问
- **屏幕阅读器**：确保屏幕阅读器可以正确解读内容
- **颜色对比度**：确保文本和背景的对比度符合 WCAG AA 标准
- **语义化 HTML**：使用正确的 HTML 元素和 ARIA 属性

### 实现指南
- **标签和说明**：为所有表单元素提供清晰的标签
- **焦点状态**：确保元素获得焦点时有明显的视觉指示
- **错误处理**：为错误提供清晰的文本说明
- **导航**：提供清晰的页面导航结构

## 8. 组件库

### 核心组件
- **App.vue**：主应用布局，包含导航抽屉和主内容区域
- **ControlPanel.vue**：控制面板，显示系统状态和操作按钮
- **Config.vue**：配置管理界面，包含 UP 主管理和工具设置
- **History.vue**：历史记录界面，显示处理记录和统计信息
- **Files.vue**：文件浏览界面，显示生成的 Markdown 文件

### 组件使用示例

#### 按钮组件
```vue
<v-btn
  color="primary"
  variant="elevated"
  icon="mdi-plus"
  class="transition-all duration-300 hover:scale-105"
  elevation="4"
>
  添加
</v-btn>
```

#### 卡片组件
```vue
<v-card
  variant="elevated"
  class="transition-all duration-300 hover:elevation-8"
  elevation="2"
>
  <v-card-title>卡片标题</v-card-title>
  <v-card-text>卡片内容</v-card-text>
  <v-card-actions>
    <v-btn color="primary" variant="text">操作</v-btn>
  </v-card-actions>
</v-card>
```

#### 表单组件
```vue
<v-text-field
  v-model="value"
  label="输入标签"
  density="comfortable"
  variant="outlined"
  prepend-inner-icon="mdi-magnify"
/>
```

## 9. 设计工具和资源

### 工具
- **Vue 3**：前端框架
- **Vuetify 3**：UI 组件库
- **Vite**：构建工具
- **Axios**：HTTP 客户端

### 图标
- **Material Design Icons**：使用 `mdi-` 前缀的图标
- **推荐图标尺寸**：
  - 小型：20px
  - 中型：24px
  - 大型：32px

### 设计参考
- [Material Design 3 官方文档](https://m3.material.io/)
- [Vuetify 3 官方文档](https://vuetifyjs.com/)
- [WCAG 2.1 可访问性标准](https://www.w3.org/TR/WCAG21/)

## 10. 开发规范

### 代码风格
- **组件命名**：使用 PascalCase（如 `ControlPanel.vue`）
- **变量命名**：使用 camelCase（如 `searchQuery`）
- **常量命名**：使用 UPPER_SNAKE_CASE（如 `MAX_BATCH_SIZE`）
- **缩进**：使用 2 个空格
- **引号**：使用双引号

### 组件结构
```vue
<template>
  <!-- 模板内容 -->
</template>

<script setup>
// 组件逻辑
</script>

<style scoped>
/* 组件样式 */
</style>
```

### 样式组织
- **全局样式**：放在 `src/styles` 目录
- **组件样式**：使用 `<style scoped>` 标签
- **变量**：使用 CSS 变量或 SCSS 变量
- **响应式**：使用媒体查询和 Vuetify 的断点系统

## 11. 维护和更新

### 版本控制
- 设计系统的变更应与代码变更同步
- 重大变更应在更新日志中记录

### 最佳实践
- **定期审查**：定期审查设计系统的使用情况
- **收集反馈**：收集用户和开发人员的反馈
- **持续改进**：根据反馈和新的设计趋势持续改进

### 资源管理
- **图标管理**：统一管理应用中使用的图标
- **颜色管理**：使用变量管理颜色，便于统一修改
- **组件库**：建立可复用的组件库，减少重复代码

---

## 结语

BiliVox 设计系统是一个活的文档，将随着项目的发展而不断演进。通过遵循这些设计规范，我们可以确保 BiliVox 应用具有一致、现代、用户友好的界面，同时提高开发效率和代码质量。