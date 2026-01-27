# BiliVox 📺

BiliVox 是一个以 UP 主为维度的 Bilibili 视频内容分析与转录工具。它能够自动批量下载指定 UP 主的视频音频，使用 Faster-Whisper 进行高精度语音转录，并结合 LLM（大语言模型）自动整理生成结构化的 Markdown 笔记文档。

## ✨ 主要功能特性

*   **UP 主维度批量处理**：输入 UP 主主页链接或 UID，自动解析并列出所有投稿视频，支持批量加入处理队列。
*   **多模式转录**：
    *   **本地模式 (Local)**：利用本地 GPU (CUDA) 或 CPU 运行 Faster-Whisper 模型，隐私安全且免费。
    *   **云端模式 (BibiGPT)**：对接 BibiGPT API，无需本地算力，快速获取结果（需配置 Token）。
*   **智能文档生成**：集成 LLM（如 DeepSeek、OpenAI 等），将转录文本自动整理为包含摘要、关键点和时间戳导航的 Markdown 笔记。
*   **实时监控与状态展示**：
    *   内置系统监控，实时展示 CPU、内存及 GPU（显存/利用率）状态。
    *   支持多显卡环境，自动统计所有可见 CUDA 设备的显存占用。
    *   可视化任务进度条，实时反馈下载、转录及 LLM 处理阶段。
*   **灵活的配置管理**：
    *   支持自定义模型大小（tiny ~ large-v3）、量化精度（float16/int8）。
    *   支持动态调整 Batch Size（1~128）以适应不同显存环境。
    *   可配置系统提示词 (System Prompt) 与生成参数。
*   **文件管理**：提供文件列表视图，支持按 UP 主筛选、批量下载 Markdown 产物。

## 💻 系统环境要求

*   **操作系统**：Windows 10/11 (推荐), Linux, macOS (仅 CPU 或 MPS 模式)
*   **Python 版本**：Python 3.10+
*   **Node.js 版本**：Node.js 16+ (用于前端构建)
*   **硬件要求**：
    *   **推荐**：NVIDIA 显卡（6GB+ 显存），已安装 CUDA 12.x 驱动。
    *   **最低**：任意 CPU（转录速度较慢）。
*   **第三方依赖**：
    *   **FFmpeg**：必须安装并配置到系统 PATH，或在设置中指定路径。
    *   **CUDA Toolkit** (仅 GPU 模式)：需配合 cuBLAS/cuDNN 库文件（本项目默认不包含，需自行安装）。

## 🚀 安装部署步骤

### 1. 克隆项目

```bash
git clone https://github.com/ux-eureka/BiliVox.git
cd BiliVox
```

### 2. 后端环境配置

推荐使用 Conda 或 venv 创建虚拟环境：

```bash
# 创建并激活虚拟环境
python -m venv venv
# Windows
.\venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# 安装 Python 依赖
pip install -r requirements.txt
```

> **注意**：如果使用 GPU 模式，请确保安装了与您 CUDA 版本匹配的 `torch` 和 `torchaudio`。默认 `requirements.txt` 可能安装的是 CPU 版本或特定 CUDA 版本，建议参考 PyTorch 官网命令重新安装 GPU 版。

### 3. 前端环境配置

```bash
cd frontend
# 安装依赖
npm install
# 构建生产环境代码
npm run build
cd ..
```

### 4. 启动服务

**生产模式（推荐）**：
后端会自动托管前端构建产物，只需启动后端即可。

```bash
# 回到项目根目录
python -m uvicorn backend.main:app --host 0.0.0.0 --port 10086
```

访问浏览器：`http://localhost:10086`

**开发模式**：
需要分别启动前后端。

```bash
# 终端 1 (后端)
python -m uvicorn backend.main:app --reload --port 8000

# 终端 2 (前端)
cd frontend
npm run dev -- --port 10086
```

## 📖 基础使用示例

1.  **添加监控目标**：
    *   进入“配置”页面 -> “监控配置”。
    *   点击“添加 UP 主”，输入 B 站个人主页链接（如 `https://space.bilibili.com/123456`）。
2.  **启动任务**：
    *   在“待处理任务”列表中，点击单个任务的“开始”按钮，或点击“检查更新并加入待处理”批量获取新视频。
3.  **查看结果**：
    *   任务完成后，进入“文件列表”页面。
    *   点击“查看”可预览 Markdown 笔记，或点击“下载”获取文件。

## ⚙️ 配置文件指南

配置文件默认位于 `config.yaml`，也可在网页端“配置”页面可视化修改。

| 配置项 | 说明 | 默认值 |
| :--- | :--- | :--- |
| `download.temp_dir` | 临时音频下载目录 | `temp` |
| `download.output_dir` | 结果文档保存目录 | `output` |
| `transcribe.device` | 推理设备 (`cuda` / `cpu`) | `cuda` |
| `transcribe.model_name` | Whisper 模型大小 | `large-v3` |
| `transcribe.batch_size` | 批处理大小 (显存越大可设越大) | `24` |
| `llm.enabled` | 是否启用 LLM 总结 | `true` |

## ❓ 常见问题 (FAQ)

**Q: 启动时提示 `ffmpeg not found`？**
A: 请确保电脑已安装 FFmpeg 并添加到了系统环境变量 PATH 中。或者在“配置 -> 下载设置”中手动指定 `ffmpeg.exe` 的完整路径。

**Q: 为什么 GPU 占用率为 0？**
A: 1. 请检查“配置 -> 处理模式”中是否选择了 `cuda` 设备。2. 确保已正确安装 NVIDIA 驱动和 CUDA Toolkit。3. 检查 PyTorch 是否为 GPU 版本 (`import torch; torch.cuda.is_available()`)。

**Q: 下载视频失败，提示 403 或 352 错误？**
A: 这是 B 站的风控限制。建议在“配置 -> 下载设置”中配置 `Cookies 来源`（选择 Chrome/Edge）或手动上传 `cookies.txt` 文件。

**Q: 提交代码时提示文件过大？**
A: 本项目已配置 `.gitignore` 排除 `cublas*.dll` 等大型二进制文件。请确保不要手动强行添加这些文件到 Git 仓库中。依赖库应由用户自行安装。
