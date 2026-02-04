<template>
  <div class="control-panel-container grid grid-cols-1 xl:grid-cols-[1fr_420px] gap-6">
    <!-- 左侧主要内容区 -->
    <div class="main-content flex flex-col gap-6 min-w-0">
      <!-- 欢迎卡片 -->
      <t-card :bordered="false" class="rounded-lg overflow-hidden bg-gradient-to-r from-blue-600 to-blue-500 text-white relative shadow-ui">
        <!-- <div class="absolute right-0 top-0 h-full w-1/2 bg-[url('https://cdn.vuetifyjs.com/images/parallax/material.jpg')] bg-cover opacity-10 mix-blend-overlay z-0"></div> -->
        <div class="relative z-10 p-2">
          <t-row align="middle" justify="space-between">
            <t-col :span="6" :xs="24" :sm="8">
              <h1 class="text-3xl font-bold mb-2">控制面板</h1>
              <p class="text-blue-100 text-lg opacity-90">欢迎回来，系统运行正常。</p>
            </t-col>
            <t-col :span="18" :xs="24" :sm="16" class="flex flex-col sm:flex-row items-stretch gap-3 justify-end mt-4 sm:mt-0 h-full">
              <div class="flex-1 w-full flex items-center" style="min-width: 0;">
                <t-input
                  ref="linkInputRef"
                  v-model="linkInput"
                  placeholder="输入 B 站 UP 主主页链接或 UID"
                  :status="linkInputStatus"
                  :tips="linkInputTips"
                  @enter="recognizeLinks"
                  style="width: 100%; min-width: 100%;"
                >
                  <template #prefix-icon>
                    <t-icon name="link" />
                  </template>
                </t-input>
              </div>
              <t-button theme="default" variant="base" @click="updateStatus">
                <template #icon><t-icon name="refresh" /></template>
                刷新状态
              </t-button>
              <t-button
                theme="primary"
                variant="base"
                class="bg-white/20 border-white/30 text-white hover:bg-white/30"
                :loading="recognizing"
                :disabled="!hasValidLinkInput || recognizing"
                @click="recognizeLinks"
              >
                <template #icon><t-icon name="search" /></template>
                解析链接
              </t-button>
              <t-button v-if="status === '运行中'" theme="danger" variant="base" @click="stopProcess">
                <template #icon><t-icon name="stop-circle" /></template>
                停止任务
              </t-button>
            </t-col>
          </t-row>
        </div>
      </t-card>

      <!-- 统计数据看板 -->
      <div class="rounded-2xl bg-[#f8fafc] border border-border p-6">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="bg-surface rounded-xl shadow-ui border border-border p-5 cursor-pointer hover:shadow-md transition-all hover:-translate-y-0.5">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
                <t-icon name="video" size="20px" />
              </div>
              <div class="min-w-0">
                <div class="text-gray-500 text-xs font-bold uppercase tracking-wider">处理视频</div>
                <div class="text-2xl font-extrabold text-gray-900 mt-1">{{ videoCount }}</div>
              </div>
            </div>
          </div>

          <div class="bg-surface rounded-xl shadow-ui border border-border p-5 cursor-pointer hover:shadow-md transition-all hover:-translate-y-0.5">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-green-50 text-green-600 flex items-center justify-center">
                <t-icon name="file" size="20px" />
              </div>
              <div class="min-w-0">
                <div class="text-gray-500 text-xs font-bold uppercase tracking-wider">生成笔记</div>
                <div class="text-2xl font-extrabold text-gray-900 mt-1">{{ noteCount }}</div>
              </div>
            </div>
          </div>

          <div class="bg-surface rounded-xl shadow-ui border border-border p-5 cursor-pointer hover:shadow-md transition-all hover:-translate-y-0.5">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-orange-50 text-orange-600 flex items-center justify-center">
                <t-icon name="play-circle" size="20px" />
              </div>
              <div class="min-w-0">
                <div class="text-gray-500 text-xs font-bold uppercase tracking-wider">运行状态</div>
                <div class="text-2xl font-extrabold text-gray-900 mt-1">{{ status }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 系统状态 -->
      <div class="bg-surface rounded-xl shadow-ui border border-border p-6 flex flex-col md:flex-row items-center gap-8">
        <div class="flex flex-col items-center justify-center min-w-[160px]">
          <t-progress theme="circle" :percentage="progress" :status="status === '运行中' ? 'active' : 'default'" size="large" />
          <div class="mt-4 font-bold text-lg text-gray-800">{{ status }}</div>
        </div>
        <div class="flex-1 w-full space-y-6">
          <div>
            <div class="flex justify-between text-sm mb-2">
              <span class="text-gray-500 flex items-center"><t-icon name="cpu" class="mr-2"/>CPU 使用率</span>
              <span class="font-bold">{{ cpuUsage }}%</span>
            </div>
            <t-progress :percentage="cpuUsage" :color="{ from: '#0052D9', to: '#00A870' }" />
          </div>
          <div>
            <div class="flex justify-between text-sm mb-2">
              <span class="text-gray-500 flex items-center"><t-icon name="layers" class="mr-2"/>内存使用率</span>
              <span class="font-bold">{{ memoryUsage }}%</span>
            </div>
            <t-progress :percentage="memoryUsage" :color="{ from: '#722ED1', to: '#E37318' }" />
          </div>
          <div class="flex items-center justify-between text-xs text-gray-500">
            <div class="flex items-center gap-2">
              <t-tag size="small" variant="light" theme="default">GPU</t-tag>
              <span v-if="hasGpu">占用 {{ gpuUsage }}% · 显存 {{ gpuMemory }} MB</span>
              <span v-else>无 GPU 数据</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 系统日志 -->
      <t-card title="系统实时日志" :bordered="false" class="h-[400px] flex flex-col shadow-ui">
        <template #actions>
          <t-button variant="text" shape="square" @click="clearLogs">
            <t-icon name="delete" />
          </t-button>
        </template>
        <div class="bg-gray-900 text-gray-300 font-mono text-sm p-4 rounded h-full overflow-auto custom-scrollbar">
          <div v-if="!logs" class="h-full flex flex-col items-center justify-center text-gray-600">
            <t-icon name="code" size="32px" class="mb-2" />
            <span>等待系统输出...</span>
          </div>
          <div v-else class="whitespace-pre-wrap">{{ logs }}</div>
        </div>
      </t-card>
    </div>

    <!-- 右侧辅助面板 -->
    <div class="side-panel flex flex-col gap-6 w-full xl:w-[420px]">
      <!-- 待处理任务 -->
      <div>
      <t-card title="待处理任务" :bordered="false" class="h-[500px] flex flex-col shadow-ui">
        <template #actions>
          <div class="flex items-center gap-2">
            <t-tag variant="light" theme="primary">{{ taskStore.tasks.length }} 个任务</t-tag>
            <t-button
              v-if="taskStore.tasks.length > 0"
              variant="text"
              size="small"
              theme="danger"
              @click="confirmClearAllTasks"
            >
              <template #icon><t-icon name="delete" /></template>
              清空
            </t-button>
          </div>
        </template>

        <div class="flex-1 overflow-auto -mx-2 px-2 custom-scrollbar">
          <div v-if="taskStore.tasks.length === 0" class="h-full flex flex-col items-center justify-center text-gray-400">
            <t-icon name="link-unlink" size="48px" class="mb-4 opacity-50" />
            <p>暂无待处理链接</p>
            <p class="text-xs mt-2">请在上方控制面板中识别链接</p>
          </div>

          <div v-else class="space-y-3">
            <div
              v-for="task in taskStore.tasks"
              :key="task.id"
              class="bg-surface rounded-xl border border-border p-3"
            >
              <div class="flex items-start gap-3">
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <!-- 优先显示 displayText (任务名/标题)，如果未定义才显示 URL -->
                    <div class="text-sm font-bold text-gray-900 truncate" :title="task.name || task.displayText || task.url">
                      {{ task.name || task.displayText || task.url }}
                    </div>
                    <t-icon v-if="task.status === 'running'" name="loading" class="text-gray-400 animate-spin" />
                    <t-tag size="small" variant="light" :theme="statusTheme(task.status)">{{ statusLabel(task.status) }}</t-tag>
                  </div>
                  <div class="mt-1 text-xs text-gray-500 flex flex-wrap gap-x-4 gap-y-1">
                    <span class="truncate" :title="task.type === 'video' ? task.url : task.name">
                       <!-- 如果是单视频，第二行显示 BV 号或 URL；如果是 UP 主任务，显示 UP 主名称 -->
                      {{ task.type === 'video' ? (task.id.startsWith('video::') ? task.id.split('::')[1] : task.url) : `UP：${truncate(task.name, 16)}` }}
                    </span>
                    <span v-if="task.videoCount">视频数：{{ task.videoCount }}</span>
                    <span v-if="task.totalSeconds">合计：{{ formatHms(task.totalSeconds) }}</span>
                  </div>

                  <div v-if="task.status === 'running' || task.status === 'done'" class="mt-2">
                    <t-progress :percentage="taskProgress(task)" />
                  </div>
                </div>

                <div class="flex items-center gap-1 flex-shrink-0">
                  <t-button
                    size="small"
                    theme="default"
                    variant="outline"
                    @click="goFilesForUp(task)"
                  >
                    <template #icon><t-icon name="folder-open" /></template>
                    查看文件
                  </t-button>
                  <t-button
                    size="small"
                    theme="primary"
                    variant="outline"
                    @click="toggleSingleTask(task)"
                    :disabled="task.status === 'running'"
                  >
                    <template #icon>
                      <t-icon :name="task.status === 'done' ? 'refresh' : 'play-circle'" />
                    </template>
                    {{ task.status === 'running' ? '处理中' : (task.status === 'done' ? '重新处理' : '开始') }}
                  </t-button>
                  <t-button
                    size="small"
                    theme="danger"
                    variant="text"
                    shape="square"
                    aria-label="取消任务"
                    @click="confirmCancelTask(task)"
                  >
                    <t-icon name="close" />
                  </t-button>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="pt-4 mt-auto border-t border-border" />
      </t-card>
      </div>

      <!-- 最近活动 -->
      <t-card title="最近活动" :bordered="false" class="shadow-ui">
        <template #actions>
          <t-button variant="text" size="small" @click="goHistory">查看全部</t-button>
        </template>
        <t-list :split="false">
          <t-list-item v-for="(activity, i) in activities" :key="i">
            <template #action>
              <t-icon name="chevron-right" />
            </template>
            <div class="flex items-center w-full">
              <div :class="`w-8 h-8 rounded flex items-center justify-center mr-3 bg-${activity.color}-50 text-${activity.color}-600`">
                <t-icon :name="activity.icon" />
              </div>
              <div class="flex-1">
                <div class="text-sm font-bold text-gray-900">{{ activity.title }}</div>
                <div class="text-xs text-gray-500">{{ activity.time }}</div>
              </div>
            </div>
          </t-list-item>
        </t-list>
      </t-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { MessagePlugin, DialogPlugin } from 'tdesign-vue-next'
import { useTaskStore } from '../store/task'
import { http } from '../api/http'
import { useRouter } from 'vue-router'

const taskStore = useTaskStore()
const router = useRouter()
const status = ref('就绪')
const logs = ref('')
const cpuUsage = ref(0)
const memoryUsage = ref(0)
const gpuUsage = ref(0)
const gpuMemory = ref(0)
const progress = ref(0)

const videoCount = ref(0)
const noteCount = ref(0)

const linkInput = ref('')
const linkInputStatus = ref('default')
const linkInputTips = ref('')
const recognizing = ref(false)
const linkInputRef = ref(null)

const hasValidLinkInput = computed(() => {
  // 同时检查 UP 主主页链接和视频链接 (BV号)
  const upUrls = extractBilibiliSpaceUrls(linkInput.value)
  if (upUrls.length > 0) return true
  
  const videoItems = extractBilibiliVideoItems(linkInput.value)
  return videoItems.length > 0
})

const formatHms = (totalSeconds) => {
  const s = Math.max(0, Math.floor(Number(totalSeconds) || 0))
  const hh = String(Math.floor(s / 3600)).padStart(2, '0')
  const mm = String(Math.floor((s % 3600) / 60)).padStart(2, '0')
  const ss = String(s % 60).padStart(2, '0')
  return `${hh}:${mm}:${ss}`
}

const formatUploadDate = (v) => {
  const s = String(v || '')
  if (/^\d{8}$/.test(s)) return `${s.slice(0, 4)}-${s.slice(4, 6)}-${s.slice(6)}`
  return s
}

const truncate = (text, maxLen) => {
  const t = String(text || '')
  if (t.length <= maxLen) return t
  return `${t.slice(0, Math.max(0, maxLen - 1))}…`
}

const statusLabel = (s) => {
  if (s === 'running') return '处理中'
  if (s === 'paused') return '已暂停'
  if (s === 'done') return '已完成'
  if (s === 'failed') return '失败'
  return '等待中'
}

const statusTheme = (s) => {
  if (s === 'running') return 'primary'
  if (s === 'paused') return 'warning'
  if (s === 'done') return 'success'
  if (s === 'failed') return 'danger'
  return 'default'
}

const focusLinkInput = async () => {
  await nextTick()
  const maybeFocus = linkInputRef.value?.focus
  if (typeof maybeFocus === 'function') {
    maybeFocus()
    return
  }
  const el = linkInputRef.value?.$el
  if (el?.scrollIntoView) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
  const input = el?.querySelector?.('input')
  if (input) input.focus()
}

const extractBilibiliSpaceUrls = (text) => {
  const normalized = String(text || '')
  const matches = normalized.match(/https?:\/\/(?:space|www)\.bilibili\.com\/\d+/g)
  if (matches && matches.length > 0) return Array.from(new Set(matches))
  const uidMatches = normalized.match(/\b\d{5,}\b/g)
  if (!uidMatches || uidMatches.length === 0) return []
  return Array.from(new Set(uidMatches)).map(uid => `https://space.bilibili.com/${uid}`)
}

const extractBilibiliVideoItems = (text) => {
  const normalized = String(text || '')
  const matches = normalized.match(/https?:\/\/(?:www\.)?bilibili\.com\/video\/(BV[0-9A-Za-z]+)/g)
  const bvMatches = normalized.match(/\b(BV[0-9A-Za-z]{8,})\b/g)
  const items = []
  if (matches && matches.length > 0) {
    for (const m of matches) {
      const mm = m.match(/\/video\/(BV[0-9A-Za-z]+)/)
      if (!mm) continue
      items.push({ bvId: mm[1], url: `https://www.bilibili.com/video/${mm[1]}` })
    }
  }
  if (bvMatches && bvMatches.length > 0) {
    for (const bvId of bvMatches) {
      items.push({ bvId, url: `https://www.bilibili.com/video/${bvId}` })
    }
  }
  const seen = new Set()
  const deduped = []
  for (const it of items) {
    const key = it?.bvId || it?.url
    if (!key || seen.has(key)) continue
    seen.add(key)
    deduped.push(it)
  }
  return deduped
}

const recognizeLinks = async () => {
  const raw = linkInput.value.trim()
  if (!raw) {
    linkInputStatus.value = 'error'
    linkInputTips.value = '请输入链接或 UID 后再识别'
    MessagePlugin.warning('请先输入链接或 UID')
    await focusLinkInput()
    return
  }

  const urls = extractBilibiliSpaceUrls(raw) // 提取 UP 主链接

  if (urls.length > 0) {
    // 优先处理 UP 主主页链接
    recognizing.value = true
    linkInputStatus.value = 'default'
    linkInputTips.value = ''

    let successCount = 0
    let lastErrorMessage = ''
    try {
      for (const url of urls) {
        try {
          const response = await http.get('/api/up_info', { params: { url } })
          const uid = response.data?.uid
          const videosResp = await http.get('/api/videos', { params: { uid } })
          const videos = Array.isArray(videosResp.data?.videos) ? videosResp.data.videos : []
          taskStore.addUpTaskFromUpVideos(response.data, url, videos)
          successCount += 1
        } catch (e) {
          lastErrorMessage = e?.userMessage || e?.message || lastErrorMessage
          continue
        }
      }

      if (successCount > 0) {
        linkInputStatus.value = 'success'
        linkInput.value = ''
        MessagePlugin.success(`解析成功：已添加 ${successCount} 个 UP 主任务`)
        setTimeout(() => {
          linkInputStatus.value = 'default'
        }, 1500)
        setTimeout(() => {
          maybeAutoStartNext(true)
        }, 0)
        return
      }
    } finally {
      recognizing.value = false
    }
  }

  // 如果没有识别到 UP 主链接，尝试识别单个视频链接
  const videoItems = extractBilibiliVideoItems(raw)
  if (videoItems.length > 0) {
    recognizing.value = true
    linkInputStatus.value = 'default'
    linkInputTips.value = ''
    
    let successCount = 0
    try {
      for (const item of videoItems) {
        let title = `视频 ${item.bvId}`
        let duration = 0
        let uploadDate = null
        try {
           const metaResp = await http.get('/api/video_meta', { params: { bvid: item.bvId } })
           if (metaResp.data?.title) {
             title = metaResp.data.title
             duration = metaResp.data.duration || 0
           }
        } catch (e) {
           console.warn('获取视频详情失败，将使用默认信息', e)
        }
        
        taskStore.addVideoTask({
          bvId: item.bvId,
          title: title,
          url: item.url,
          duration: duration,
        }, item.url)
        successCount += 1
      }
      
      if (successCount > 0) {
        linkInputStatus.value = 'success'
        linkInput.value = ''
        MessagePlugin.success(`解析成功：已添加 ${successCount} 个视频任务`)
        setTimeout(() => {
          linkInputStatus.value = 'default'
        }, 1500)
        setTimeout(() => {
          maybeAutoStartNext(true)
        }, 0)
        return
      }
    } finally {
      recognizing.value = false
    }
  }

  // 既不是 UP 主也不是视频链接
  linkInputStatus.value = 'error'
  linkInputTips.value = '请输入有效的 B 站 UP 主主页链接、UID 或视频链接'
  MessagePlugin.error('未识别到可用链接')
  await focusLinkInput()
}

const confirmCancelTask = (task) => {
  const instance = DialogPlugin.confirm({
    header: '确认取消',
    body: '确定要取消并移除此任务吗？',
    confirmBtn: '取消任务',
    cancelBtn: '返回',
    onConfirm: () => {
      taskStore.removeTask(task.id)
      MessagePlugin.success('已取消')
      instance.destroy()
    },
    onClose: () => {
      instance.destroy()
    },
  })
}

const hydratingDurations = ref(false)

const hydrateEstimatedDurations = async () => {}

const goFilesForUp = (task) => {
  const up = task?.name
  router.push({ path: '/files', query: { up } })
}

const confirmClearAllTasks = () => {
  if (taskStore.tasks.length === 0) return
  const instance = DialogPlugin.confirm({
    header: '确认清空',
    body: '确定要清空待处理任务列表吗？（不会停止后台正在运行的任务）',
    confirmBtn: '清空列表',
    cancelBtn: '返回',
    onConfirm: () => {
      taskStore.clearTasks()
      MessagePlugin.success('已清空待处理任务')
      instance.destroy()
    },
    onClose: () => {
      instance.destroy()
    },
  })
}

const downloadTaskDoc = async (task) => {
  try {
    let outputPath = task?.outputPath
    let outputName = task?.outputName

    if (!outputPath) {
      const outResp = await http.get('/api/task/output', { params: { taskId: task.id } })
      outputPath = outResp.data?.path
      outputName = outResp.data?.name
      if (outputPath) {
        taskStore.setTaskOutput(task.id, { path: outputPath, name: outputName, at: Date.now() / 1000 })
      }
    }

    if (!outputPath) {
      MessagePlugin.warning('未找到该任务的产物文档，请先完成处理再下载')
      return
    }

    const resp = await http.get('/api/download', {
      params: { path: outputPath },
      responseType: 'blob',
    })
    const blobUrl = URL.createObjectURL(resp.data)
    const a = document.createElement('a')
    a.href = blobUrl
    a.download = outputName || 'document.md'
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(blobUrl)
  } catch (e) {
    MessagePlugin.error(e?.userMessage || '下载失败')
  }
}

const currentTaskId = ref(null)
const autoStarting = ref(false)

const taskProgress = (task) => {
  if (task?.status === 'done') return 100
  if (task?.status === 'running' && currentTaskId.value && task.id === currentTaskId.value) {
    return Math.max(0, Math.min(100, Number(progress.value) || 0))
  }
  return 0
}

const findNextWaitingTask = () => {
  const list = Array.isArray(taskStore.tasks) ? taskStore.tasks : []
  const waiting = list
    .filter(t => t && t.status === 'waiting' && t.type === 'up' && t.uid && t.name)
    .slice()
    .sort((a, b) => Number(a.createdAt || 0) - Number(b.createdAt || 0))
  return waiting[0] || null
}

const maybeMarkOrphanRunningAsFailed = () => {
  if (status.value === '运行中') return
  if (currentTaskId.value) return
  const now = Date.now()
  for (const t of taskStore.tasks) {
    if (!t || t.status !== 'running') continue
    const startedAt = Number(t.lastStartedAt || 0)
    if (startedAt && now - startedAt < 8000) continue
    taskStore.markTaskFailed(t.id, '任务已结束或启动失败')
  }
}

const startTaskBackend = async (task, force, silent) => {
  try {
    if (task.type === 'video') {
      const videoInfo = task.extra || {}
      // 构造视频任务请求
      const payload = {
        taskId: task.id,
        upName: '独立视频', // 单视频任务默认存放目录
        force: !!force,
        video: {
          bvId: videoInfo.bvId || (task.id.startsWith('video::') ? task.id.split('::')[1] : ''),
          title: task.name,
          url: task.sourceUrl,
          uploadDate: videoInfo.uploadDate || null,
          duration: task.totalSeconds || null,
          uploader: videoInfo.uploader || null // 传递 UP 主名称
        }
      }
      await http.post('/api/video/start', payload)
    } else {
      // UP 主任务请求
      await http.post('/api/task/start', { taskId: task.id, name: task.name, uid: task.uid, force: !!force })
    }
    
    taskStore.startTask(task.id)
    if (!silent) MessagePlugin.success(force ? '已开始重新处理' : '已开始处理')
    return true
  } catch (e) {
    taskStore.markTaskFailed(task.id, e?.userMessage || '启动失败')
    if (!silent) MessagePlugin.error(e?.userMessage || '启动失败')
    return false
  }
}

const maybeAutoStartNext = async (silent) => {
  if (autoStarting.value) return
  if (recognizing.value) return
  if (status.value === '运行中') return

  const next = findNextWaitingTask()
  if (!next) return
  autoStarting.value = true
  try {
    await startTaskBackend(next, false, !!silent)
  } finally {
    autoStarting.value = false
  }
}

const toggleSingleTask = (task) => {
  if (task.status === 'running') return

  const force = task.status === 'done'
  if (force) taskStore.resetTask(task.id)

  logs.value += `[${new Date().toLocaleTimeString()}] ${force ? '重新处理' : '开始'}任务: ${task?.name || 'UP'}\n`
  startTaskBackend(task, force, false)
}

const recentHistory = ref([])
const activities = computed(() => {
  return recentHistory.value.slice(0, 6).map((h) => {
    const ok = h?.status === '成功'
    return {
      icon: ok ? 'check-circle' : 'close-circle',
      color: ok ? 'green' : 'red',
      title: `${ok ? '完成' : '失败'}：${h?.title || '未知视频'}`,
      time: h?.timestamp || '',
    }
  })
})

let statusPollInterval = null
let historyPollCounter = 4

const updateStatus = async () => {
  try {
    const prevCurrentTaskId = currentTaskId.value
    const response = await http.get('/api/status')
    status.value = response.data.status || '就绪'
    progress.value = Number(response.data.progress) || 0
    cpuUsage.value = Number(response.data.cpuUsage) || 0
    memoryUsage.value = Number(response.data.memoryUsage) || 0
    gpuUsage.value = Number(response.data.gpuUsage) || 0
    gpuMemory.value = Number(response.data.gpuMemory) || 0
    const logLines = Array.isArray(response.data.logs) ? response.data.logs : []
    logs.value = logLines.join('\n')
    currentTaskId.value = response.data?.currentTaskId || null

    const lastSavedTaskId = response.data?.lastSavedTaskId
    const lastSavedPath = response.data?.lastSavedPath
    const lastSavedName = response.data?.lastSavedName
    const lastSavedAt = response.data?.lastSavedAt
    if (lastSavedTaskId && lastSavedPath) {
      const task = taskStore.tasks.find(t => t.id === lastSavedTaskId)
      if (task && task.lastOutputPath !== lastSavedPath) taskStore.setTaskLastOutput(lastSavedTaskId, { path: lastSavedPath, name: lastSavedName, at: lastSavedAt })
    }

    if (prevCurrentTaskId && !currentTaskId.value) {
      const finished = taskStore.tasks.find(t => t.id === prevCurrentTaskId)
      if (finished && finished.status === 'running') {
        if (status.value === '空闲') taskStore.markTaskDone(finished.id)
        else if (status.value === '错误') taskStore.markTaskFailed(finished.id, '任务执行出错')
      }
    }

    historyPollCounter += 1
    if (historyPollCounter % 5 === 0) {
      const hr = await http.get('/api/history')
      recentHistory.value = Array.isArray(hr.data) ? hr.data.slice().reverse() : []
      videoCount.value = Array.isArray(hr.data) ? hr.data.length : 0
      const fr = await http.get('/api/files')
      noteCount.value = Array.isArray(fr.data?.files) ? fr.data.files.length : 0
    }
    maybeMarkOrphanRunningAsFailed()
    maybeAutoStartNext(true)
  } catch (error) {
    console.error('获取状态失败:', error)
  }
}

const goHistory = () => {
  router.push('/history')
}

const stopProcess = async () => {
  try {
    await http.post('/api/stop')
    status.value = '已停止'
    MessagePlugin.success('已停止任务')
  } catch (error) {
    const msg = error?.userMessage || error?.message || '停止失败'
    MessagePlugin.error(msg)
  }
}

const clearLogs = () => {
  logs.value = ''
}

const hasGpu = computed(() => gpuUsage.value > 0 || gpuMemory.value > 0)

const formatNumber = (num) => {
  if (!num) return '未知'
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  }
  return num
}

 

onMounted(() => {
  updateStatus()
  hydrateEstimatedDurations()
  // 缩短刷新间隔以提高实时性 (2000ms -> 1000ms)
  statusPollInterval = setInterval(updateStatus, 1000)
})

onUnmounted(() => {
  if (statusPollInterval) {
    clearInterval(statusPollInterval)
  }
})
</script>
