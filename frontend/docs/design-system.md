# BiliVox 设计系统规范（提案）

本规范的目标是：在 TDesign 组件库之上，建立一套可复用、可扩展、可主题化的视觉与交互规则，使所有页面在不同尺寸下都保持一致。

## 1. 设计原则

- 清晰层级：页面背景（canvas）→ 面板（panel）→ 卡片（card）
- 少即是多：减少不必要的阴影、过度动效与装饰色
- 一致可预测：同语义同颜色，同层级同圆角/阴影
- 可访问性优先：对比度、键盘可达、状态反馈不依赖颜色单一表达

## 2. 设计令牌（Tokens）

建议以 CSS 变量作为“单一事实来源”，并在 Tailwind 中映射。

文件：`src/styles/tokens.css`

### 2.1 颜色

- `--ui-canvas`：页面底色（浅灰）
- `--ui-surface`：卡片/面板底色（白）
- `--ui-text`：正文主色（近黑）
- `--ui-muted`：弱化文字（中灰，注意对比度）
- `--ui-border`：分割线/边框（浅灰）
- `--ui-brand`：品牌色（蓝）
- `--ui-success/warning/danger`：语义色

### 2.2 圆角与阴影

- `--ui-radius`：常规卡片（12px）
- `--ui-radius-lg`：大面板/抽屉（16px）
- `--ui-shadow`：常规阴影（轻）
- `--ui-shadow-lg`：浮层阴影（重）

## 3. 排版体系

建议固定以下 5 档：

- H1：32/40，bold（页面标题）
- H2：20/28，bold（模块标题）
- Body：14/22，regular（正文）
- Caption：12/18，regular（辅助说明）
- Tag/Label：12/16，bold + tracking（标签、统计项标题）

## 4. 间距与栅格（布局规则）

### 4.1 间距基准

- 以 8px 为基数：8/16/24/32/48
- 页面 padding：24（右侧内容区默认）
- 卡片内 padding：24（内容密度适中），紧凑卡片 16
- 卡片间距：24（同级模块），16（卡片组内部）

### 4.2 页面级布局（推荐）

页面级使用 CSS Grid：

- 桌面（≥1280）：`grid-cols-[1fr_420px]`（主内容 + 右侧工具面板）
- 平板/手机：单列，右侧面板下移

组件内部使用 Flex：

- 按钮组：`flex gap-2/3`
- 表单行：`flex flex-col sm:flex-row gap-3`

## 5. 核心组件规范（行为统一）

### 5.1 Button

- 尺寸：默认高度 32–36，触达面积不小于 40×40（移动端）
- 语义：primary/secondary/danger
- 状态：hover/active/disabled/loading 一致

### 5.2 Input

- 校验：错误提示与边框状态一致，避免仅依赖颜色
- suffix icon：用于搜索/解析等“快速动作”，保持 icon-only 但有 `aria-label`

### 5.3 Card

- 普通卡片：`surface + radius + shadow-ui + border`
- 卡片组：外层 panel（可用浅底），内部多张 card

### 5.4 Navigation

- 桌面：固定宽侧栏，可折叠
- 移动：抽屉导航，路由切换自动关闭

## 6. 可访问性（WCAG 2.1 AA）

- 文本对比度：正文 ≥4.5:1，小字避免用过浅的灰
- 键盘导航：可聚焦元素必须可见焦点
- 非文本信息：icon-only 按钮提供 `aria-label` / `title`
- 状态提示：成功/失败除颜色外应有文案或图标辅助

## 7. 落地方式（工程侧）

建议顺序：

1) 令牌落地：`tokens.css` + Tailwind theme 映射
2) 页面级布局：统一 Grid（ControlPanel/History/Files）
3) 组件复用：抽出 `CardGroup / StatCard / PanelSection` 等基础组件
4) 视觉回归：新增“设计系统展示页”作为视觉基线

