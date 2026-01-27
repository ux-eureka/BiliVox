# BiliVox UI 审计与体验优化报告（本地版）

目标地址：`http://localhost:3000/`

## 0. 结论摘要（可执行）

当前 UI 的“看起来没变化/改不动”的核心原因并不是某一个卡片样式，而是 **样式体系不闭环 + 设计语言未统一**：

- **Tailwind 依赖已安装，但缺少 PostCSS/Tailwind 配置闭环**，导致大量 utility class 在不同环境下无法稳定产出，出现“改了 class 但页面不变”的体验。
- **TDesign + Tailwind + Vuetify 三套体系混用**：断点、栅格、间距、圆角、阴影都各自为政；同一页面不同模块出现不一致。
- **全局 Layout 侧栏/内容区存在重复 padding 与 max-width 逻辑漂移**，导致可用空间计算、对齐与“层级/嵌套”难以稳定。

已做的“立即修复”见本报告第 4 节（会让样式变化可见、可控、可复用）。

---

## 1. 现状 UI 设计语言盘点

### 1.1 组件体系与技术栈

- 组件库：TDesign（主要）、Vuetify（配置页大量使用）、自定义 Tailwind utility（跨页面）
- 样式入口：`src/style.css`（Tailwind 指令 + 少量全局重置）
- 主要页面：
  - 控制面板：`src/views/ControlPanel.vue`
  - 配置中心：`src/views/Config.vue`（Vuetify 重度）
  - 历史记录：`src/views/History.vue`（TDesign Grid 重度）
  - 文件管理：`src/views/Files.vue`

### 1.2 色彩系统（实际使用）

现状：
- 品牌蓝：TDesign 默认蓝（多处硬编码/变量）
- 背景灰：`#f3f4f5`
- 语义色：成功/警告/危险在 TDesign 与 Tailwind 之间混用（同语义多色值）

问题：
- 颜色来源不统一：TDesign token、Tailwind class、硬编码颜色同时存在。
- 深浅层级不稳定：卡片/容器/页面背景经常同色，导致“嵌套层级”不明显。

### 1.3 排版规范

现状：
- 字体：`Inter, system-ui...`（全局 `:root`）
- 字号：页面内直接用 Tailwind `text-xs/text-sm/text-lg/text-3xl` 混搭

问题：
- 缺少“标题阶梯（H1/H2/正文/说明/标签）”的统一规范，页面看起来“每块都很重要/都很响”。

### 1.4 间距与栅格

现状（混用）：
- TDesign：`t-row/t-col` 的 gutter、xs/sm/md/lg
- Tailwind：`gap-6/p-6/p-8/md:...`
- Vuetify：`v-row/v-col`（sm/md/lg/xl）

问题：
- 三套断点并存：同一屏宽下不同模块换行策略不一致。
- 16/24/32 间距在页面中无规则出现，缺少基准与比例尺。

### 1.5 圆角与阴影

现状：
- `rounded-lg/rounded-xl` 并存
- 阴影：`shadow-sm/shadow-lg` 并存

问题：
- 缺少统一“Surface 规则”：哪些层级使用哪种 radius/shadow。

---

## 2. 信息架构与导航体验

现状导航：
- 左侧固定菜单（控制面板/文件管理/配置中心/历史记录）
- 移动端需要抽屉式导航以避免侧栏挤压

主要问题：
- 配置中心与其他页面的组件体系不同（Vuetify），造成体验割裂（按钮、输入、对话框、间距都不同）。
- 顶部输入框属于跨页面的“全局动作”，但反馈/状态展示在不同页面不一致（任务列表与解析入口割裂）。

---

## 3. 响应式与可访问性审计

### 3.1 响应式（320 → 1920）

高风险点：
- 固定宽度侧栏（420px 面板）在 768~1024 的平板宽度下容易挤压主内容。
- 同一页面使用 Grid + TDesign Row/Col 混搭，某些断点下会出现“看似 3 列，实则换行/压缩”的错觉。

建议：
- 页面级布局统一用 CSS Grid，组件内部用 Flex。
- 固定宽侧栏仅在 `xl` 以上生效；以下自动堆叠为单列。

### 3.2 可访问性（WCAG 2.1 AA 视角）

发现的问题（样式层面）：
- 灰字（`text-gray-500`）在浅灰底上可能对比不足（尤其是小字标签）。
- 一些 icon-only 按钮缺少可读 label（ARIA 或 tooltip）。

建议：
- 定义 `--ui-muted` 并限制用于正文/标签的最浅灰度范围。
- icon-only 按钮统一加 `aria-label` / `title`。

---

## 4. 已实施的“立即修复”（让变化可见、可控）

### 4.1 Tailwind 构建链补齐（解决“UI 不变化”）

已补齐：
- `postcss.config.cjs`：启用 Tailwind + Autoprefixer
- `tailwind.config.cjs`：统一 content 扫描范围与可扩展 token
- `src/styles/tokens.css`：新增 UI token（颜色/圆角/阴影）
- `src/style.css`：引入 tokens，并将页面背景/文本色改为 token 驱动

### 4.2 统计区域视觉重做（小白卡嵌套 + 大横向区域）

- 外层为浅色大容器，三张“小白卡”作为子层级，使用一致的 `rounded-xl + shadow-sm + border`。
- 第三个指标从“运行时长”调整为更符合仪表盘语义的“运行状态”。

---

## 5. 问题清单（优先级矩阵）

说明：优先级依据【影响面 × 发生频率 × 修复成本】综合判断。

### P0（高优先级）

1) 样式链路不闭环导致“改了不生效”
- 现象：页面 class 改动后视觉无变化或仅局部变化
- 影响：开发效率和 UI 一致性全面下降
- 修复：补齐 PostCSS/Tailwind 配置闭环（已做）

2) 多组件库并存导致一致性断裂（TDesign vs Vuetify）
- 现象：配置中心与其他页面按钮/输入/卡片差异明显
- 修复：短期通过 token 统一颜色/圆角；中长期选定单一组件体系或封装桥接层

### P1（中优先级）

3) 页面级布局层级不清（容器/卡片/卡片组的层级难分）
- 修复：引入“Surface 规则”，统一 `canvas/surface/panel` 三层背景与阴影

4) 响应式策略混乱（多断点体系）
- 修复：页面级统一 Grid（`xl` 双栏、以下单栏），组件内 Flex；减少 `t-row/t-col` 与 Tailwind grid 混搭

### P2（低优先级）

5) 图标按钮的可访问性 label 缺失
- 修复：统一加 `aria-label` 与 tooltip

---

## 6. 大刀阔斧的设计系统提案（摘要）

详见：`docs/design-system.md`

- 色彩：`brand/surface/canvas/text/muted/border/semantic`
- 字体阶梯：H1/H2/正文/说明/标签统一
- 间距：以 8px 为基数，常用 16/24/32 作为布局主尺度
- 圆角：12 / 16 两档
- 阴影：`shadow-ui` / `shadow-ui-lg` 两档
- 组件：Button/Input/Card/Nav/Dialog/Table 的统一 API/行为规范

---

## 7. 实施路线图（建议）

### 立即修复（1–2 周）
- 统一 Tailwind/TDesign token，消除硬编码色值
- 统一页面 padding/容器宽度策略，保证“导航右侧起始”与 24px 边距一致
- 修复移动端导航抽屉与顶部全局操作区的可用性（触达面积/折叠策略）

### 短期优化（1 个季度）
- 将配置中心从 Vuetify 迁移至 TDesign（或相反），实现组件一致性
- 引入“Design System Showcase”页面，作为组件回归测试与视觉基线

### 长期重构（战略）
- 建立完整设计令牌体系（颜色/排版/间距/动效），并在 Tailwind theme 中映射
- 增加可访问性自动化检查（对比度、可聚焦、ARIA）

