<template>
  <t-card :bordered="false" class="w-full rounded-lg overflow-hidden shrink-0 mb-6">
    <div class="flex items-center gap-3">
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
      <t-button theme="default" variant="outline" @click="updateStatus">
        <template #icon><t-icon name="refresh" /></template>
        刷新状态
      </t-button>
      <t-button
        theme="primary"
        variant="base"
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
    </div>
  </t-card>

  <div class="control-panel-grid h-full">
    <t-card :bordered="false" class="grid-card">
      <div class="card-container">
        <div class="card-header">
          <span class="text-base font-bold text-gray-900">运行状态</span>
          <span class="text-xs text-gray-500">CPU {{ cpuUsage }}% · 内存 {{ memoryUsage }}%</span>
        </div>
        <div class="card-body">
          <div class="status-content flex items-center gap-6">
            <div class="flex flex-col items-center justify-center min-w-[120px]">
              <t-progress
                theme="circle"
                :percentage="progress"
                :status="status === '运行中' ? 'active' : (progress >= 100 ? 'success' : undefined)"
                size="large"
              />
              <div class="mt-3 font-bold text-base text-gray-900">{{ status }}</div>
            </div>
            <div class="flex flex-col gap-4">
              <div>
                <div class="flex justify-between text-xs mb-1 w-48">
                  <span class="text-gray-500">CPU</span>
                  <span class="font-bold">{{ cpuUsage }}%</span>
                </div>
                <t-progress :percentage="cpuUsage" :color="{ from: '#0052D9', to: '#00A870' }" />
              </div>
              <div>
                <div class="flex justify-between text-xs mb-1 w-48">
                  <span class="text-gray-500">内存</span>
                  <span class="font-bold">{{ memoryUsage }}%</span>
                </div>
                <t-progress :percentage="memoryUsage" :color="{ from: '#722ED1', to: '#E37318' }" />
              </div>
              <div class="text-xs text-gray-500">
                <t-tag size="small" variant="light" theme="default">GPU</t-tag>
                <span class="ml-1">{{ hasGpu ? `占用 ${gpuUsage}% · ${gpuMemory} MB` : '无 GPU 数据' }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </t-card>

    <t-card :bordered="false" class="grid-card">
      <div class="card-container">
        <div class="card-header">
          <span class="text-base font-bold text-gray-900">待处理任务</span>
          <div class="flex items-center gap-2">
            <t-tag variant="light" theme="primary" size="small">{{ taskStore.tasks.length }}</t-tag>
            <t-button
              v-if="taskStore.tasks.length > 0"
              variant="text"
              size="small"
              theme="danger"
              :loading="clearingAll"
              :disabled="clearingAll"
              @click="onClearAllClick"
            >
              <t-icon name="delete" />
            </t-button>
          </div>
        </div>
        <div class="card-body card-body--scroll">
          <div class="task-list-compact scroll-container">
            <div v-if="taskStore.tasks.length === 0" class="empty-state-compact">
              <t-icon name="link-unlink" size="32px" class="mb-2 text-gray-300" />
              <p class="text-gray-500 text-sm">暂无待处理</p>
            </div>
            <div v-else class="space-y-2">
              <div
                v-for="task in taskStore.tasks.slice(0, 4)"
                :key="task.id"
                class="task-item-compact"
              >
                <div class="flex items-center justify-between gap-2">
                  <div class="flex items-center gap-1.5 min-w-0">
                    <t-icon v-if="task.status === 'running'" name="loading" class="text-gray-400 animate-spin" size="14" />
                    <t-tag size="small" variant="light" :theme="statusTheme(task.status)">{{ statusLabel(task.status) }}</t-tag>
                    <span class="text-sm text-gray-900 truncate">{{ task.name || task.displayText || task.url }}</span>
                  </div>
                  <div class="flex items-center gap-0.5 flex-shrink-0">
                    <t-button size="small" variant="text" shape="square" @click="goFilesForUp(task)">
                      <t-icon name="folder-open" size="14" />
                    </t-button>
                    <t-button
                      size="small"
                      variant="text"
                      shape="square"
                      @click="toggleSingleTask(task)"
                      :disabled="task.status === 'running'"
                    >
                      <t-icon :name="task.status === 'done' ? 'refresh' : 'play-circle'" size="14" />
                    </t-button>
                    <t-button
                      size="small"
                      variant="text"
                      theme="danger"
                      shape="square"
                      :loading="terminatingIds.has(task.id)"
                      :disabled="terminatingIds.has(task.id)"
                      @click="onCancelTaskClick(task)"
                    >
                      <t-icon name="close" size="14" />
                    </t-button>
                  </div>
                </div>
                <t-progress v-if="task.status === 'running'" :percentage="taskProgress(task)" size="small" class="mt-1" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </t-card>

    <t-card :bordered="false" class="grid-card">
      <div class="card-container">
        <div class="card-header">
          <span class="text-base font-bold text-gray-900">系统实时日志</span>
          <t-button variant="text" shape="square" @click="clearLogs">
            <t-icon name="delete" />
          </t-button>
        </div>
        <div class="card-body">
          <SystemLogs
            :logs="logs"
            empty-text="等待系统输出..."
            :padding-size="12"
            persist-scroll-key="system-logs"
          />
        </div>
      </div>
    </t-card>

    <t-card :bordered="false" class="grid-card">
      <div class="card-container">
        <div class="card-header">
          <span class="text-base font-bold text-gray-900">最近活动</span>
          <t-button variant="text" size="small" @click="goHistory">全部</t-button>
        </div>
        <div class="card-body card-body--scroll">
          <div class="activity-grid-compact scroll-container">
            <div
              v-for="item in activities"
              :key="item.title"
              class="activity-item-compact"
              @click="onActivityClick(item)"
            >
              <div class="flex items-center gap-2 min-w-0">
                <t-icon :name="item.icon" :class="`text-${item.color}-600`" size="16" />
                <span class="text-sm text-gray-900 truncate flex-1">{{ item.title }}</span>
              </div>
              <span class="text-xs text-gray-400 flex-shrink-0">{{ item.time }}</span>
            </div>
            <div v-if="activities.length === 0" class="activity-empty-compact">
              <t-icon name="time" size="28px" class="mb-2 text-gray-300" />
              <p class="text-gray-400 text-sm">暂无活动</p>
            </div>
          </div>
        </div>
      </div>
    </t-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { MessagePlugin, DialogPlugin } from 'tdesign-vue-next'
import { useTaskStore } from '../store/task'
import { http } from '../api/http'
import { terminateTask, batchTerminateTasks } from '../api/tasks'
import { useRouter } from 'vue-router'
import SystemLogs from '../components/SystemLogs.vue'

interface Task {
  id: string
  name?: string
  type?: string
  status?: string
  extra?: Record<string, unknown>
  displayText?: string
  url?: string
  outputPath?: string
  outputName?: string
}

interface BilibiliVideoItem {
  bvId: string
  url: string
}

interface ActivityItem {
  icon: string
  color: string
  title: string
  time: string
}

const taskStore = useTaskStore()
const router = useRouter()

const status = ref<string>('就绪')
const logs = ref<string>('')
const cpuUsage = ref<number>(0)
const memoryUsage = ref<number>(0)
const gpuUsage = ref<number>(0)
const gpuMemory = ref<number>(0)
const progress = ref<number>(0)

const linkInput = ref<string>('')
const linkInputStatus = ref<'default' | 'success' | 'error'>('default')
const linkInputTips = ref<string>('')
const recognizing = ref<boolean>(false)
const linkInputRef = ref<unknown>(null)

const hasValidLinkInput = computed<boolean>(() => {
  const upUrls = extractBilibiliSpaceUrls(linkInput.value)
  if (upUrls.length > 0) return true
  
  const videoItems = extractBilibiliVideoItems(linkInput.value)
  return videoItems.length > 0
})

const formatHms = (totalSeconds: unknown): string => {
  const s = Math.max(0, Math.floor(Number(totalSeconds) || 0))
  const hh = String(Math.floor(s / 3600)).padStart(2, '0')
  const mm = String(Math.floor((s % 3600) / 60)).padStart(2, '0')
  const ss = String(s % 60).padStart(2, '0')
  return `${hh}:${mm}:${ss}`
}

const formatUploadDate = (v: unknown): string => {
  const s = String(v || '')
  if (/^\d{8}$/.test(s)) return `${s.slice(0, 4)}-${s.slice(4, 6)}-${s.slice(6)}`
  return s
}

const truncate = (text: unknown, maxLen: number): string => {
  const t = String(text || '')
  if (t.length <= maxLen) return t
  return `${t.slice(0, Math.max(0, maxLen - 1))}…`
}

const statusLabel = (s: string): string => {
  const labels: Record<string, string> = {
    running: '处理中',
    paused: '已暂停',
    done: '已完成',
    failed: '失败',
    waiting: '等待中',
    pending: '等待中'
  }
  return labels[s] || '等待中'
}

const statusTheme = (s: string): string => {
  const themes: Record<string, string> = {
    running: 'primary',
    paused: 'warning',
    done: 'success',
    failed: 'danger'
  }
  return themes[s] || 'default'
}

const focusLinkInput = async (): Promise<void> => {
  await nextTick()
  const maybeFocus = linkInputRef.value?.focus
  if (typeof maybeFocus === 'function') {
    maybeFocus()
    return
  }
  const el = (linkInputRef.value as { $el?: HTMLElement })?.$el
  if (el?.scrollIntoView) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
  const input = el?.querySelector?.('input')
  if (input) input.focus()
}

const extractBilibiliSpaceUrls = (text: string): string[] => {
  const normalized = String(text || '')
  const matches = normalized.match(/https?:\/\/(?:space|www)\.bilibili\.com\/\d+/g)
  if (matches && matches.length > 0) return Array.from(new Set(matches))
  const uidMatches = normalized.match(/\b\d{5,}\b/g)
  if (!uidMatches || uidMatches.length === 0) return []
  return Array.from(new Set(uidMatches)).map(uid => `https://space.bilibili.com/${uid}`)
}

const extractBilibiliVideoItems = (text: string): BilibiliVideoItem[] => {
  const normalized = String(text || '')
  const items: BilibiliVideoItem[] = []

  const videoUrlRegex = /https?:\/\/(?:www\.)?bilibili\.com\/video\/(BV[0-9A-Za-z]+)[^]*/g
  let match: RegExpExecArray | null
  while ((match = videoUrlRegex.exec(normalized)) !== null) {
    const bvId = match[1]
    const fullUrl = match[0].split('#')[0]
    if (!items.find(i => i.bvId === bvId)) {
      items.push({ bvId, url: fullUrl })
    }
  }

  const bvOnlyRegex = /\b(BV[0-9A-Za-z]{8,})\b/g
  while ((match = bvOnlyRegex.exec(normalized)) !== null) {
    const bvId = match[1]
    const url = `https://www.bilibili.com/video/${bvId}`
    if (!items.find(i => i.bvId === bvId)) {
      items.push({ bvId, url })
    }
  }

  return items
}

const recognizeLinks = async (): Promise<void> => {
  const raw = linkInput.value.trim()
  if (!raw) {
    linkInputStatus.value = 'error'
    linkInputTips.value = '请输入链接或 UID 后再识别'
    MessagePlugin.warning('请先输入链接或 UID')
    await focusLinkInput()
    return
  }

  const urls = extractBilibiliSpaceUrls(raw)

  if (urls.length > 0) {
    recognizing.value = true
    linkInputStatus.value = 'default'
    linkInputTips.value = ''

    let successCount = 0
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

  const videoItems = extractBilibiliVideoItems(raw)
  if (videoItems.length > 0) {
    recognizing.value = true
    linkInputStatus.value = 'default'
    linkInputTips.value = ''
    
    let successCount = 0
    try {
      for (const item of videoItems) {
        let title = `视频 ${item.bvId}`
        try {
           const metaResp = await http.get('/api/video_meta', { params: { bvid: item.bvId } })
           if (metaResp.data?.title) {
             title = metaResp.data.title
           }
        } catch (e) {
           console.warn('获取视频详情失败，将使用默认信息', e)
        }
        
        taskStore.addVideoTask({
          bvId: item.bvId,
          title,
          url: item.url
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

  linkInputStatus.value = 'error'
  linkInputTips.value = '请输入有效的 B 站 UP 主主页链接、UID 或视频链接'
  MessagePlugin.error('未识别到可用链接')
  await focusLinkInput()
}

const terminatingIds = ref<Set<string>>(new Set())
const clearingAll = ref<boolean>(false)

const debounce = <T extends (...args: unknown[]) => unknown>(
  fn: T, 
  delay: number
): ((...args: Parameters<T>) => void) => {
  let t: ReturnType<typeof setTimeout> | null = null
  return (...args: Parameters<T>) => {
    if (t) clearTimeout(t)
    t = setTimeout(() => fn(...args), delay)
  }
}

const showFixedError = (msg: string): void => {
  MessagePlugin.error({ content: msg, duration: 5000 })
}

const onCancelTaskClick = debounce(async (task: Task): Promise<void> => {
  const confirmDialog = DialogPlugin.confirm({
    header: '确认取消',
    body: '确定要取消并移除此任务吗？',
    confirmBtn: '取消任务',
    cancelBtn: '返回',
    onConfirm: async () => {
      terminatingIds.value.add(task.id)
      try {
        await terminateTask(task.id)
        taskStore.markTaskTerminated(task.id)
        taskStore.removeTask(task.id)
        const poll = async (): Promise<void> => {
          try {
            const r = await http.get(`/api/task/${encodeURIComponent(task.id)}/status`)
            if (String(r.data?.status || '') !== 'terminated') {
              await new Promise(res => setTimeout(res, 500))
              return poll()
            }
          } catch (e) {}
        }
        await poll()
        MessagePlugin.success('任务已终止')
      } catch (e) {
        showFixedError('任务终止失败，请刷新后重试')
      } finally {
        terminatingIds.value.delete(task.id)
        confirmDialog.destroy()
      }
    },
    onClose: () => {
      confirmDialog.destroy()
    },
  })
}, 300)

const hydrateEstimatedDurations = async (): Promise<void> => {}

const goFilesForUp = (task: Task): void => {
  if (task.type === 'video') {
    const keyword = task.name || ''
    if (keyword) {
      router.push({ path: '/files', query: { keyword: encodeURIComponent(keyword) } })
    } else {
      router.push({ path: '/files' })
    }
  } else {
    const up = task.name
    if (up) {
      router.push({ path: '/files', query: { up: encodeURIComponent(up) } })
    } else {
      router.push({ path: '/files' })
    }
  }
}

const onClearAllClick = debounce((): void => {
  const list = Array.isArray(taskStore.tasks) ? taskStore.tasks : []
  const pendingIds = list
    .filter((t): t is Task => t && (t.status === 'waiting' || t.status === 'pending'))
    .map(t => t.id)
  if (pendingIds.length === 0) return
  const instance = DialogPlugin.confirm({
    header: '确认清空',
    body: '确定要清空待处理任务列表吗？',
    confirmBtn: '清空列表',
    cancelBtn: '返回',
    onConfirm: async () => {
      clearingAll.value = true
      try {
        await batchTerminateTasks(pendingIds)
        for (const id of pendingIds) {
          taskStore.markTaskTerminated(id)
          taskStore.removeTask(id)
        }
        MessagePlugin.success('已清空待处理任务')
      } catch (e) {
        showFixedError('任务终止失败，请刷新后重试')
      } finally {
        clearingAll.value = false
        instance.destroy()
      }
    },
    onClose: () => {
      instance.destroy()
    },
  })
}, 300)

const downloadTaskDoc = async (task: Task): Promise<void> => {
  try {
    let outputPath = task.outputPath
    let outputName = task.outputName

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

const currentTaskId = ref<string | null>(null)
const autoStarting = ref<boolean>(false)

const taskProgress = (task: Task): number => {
  if (task?.status === 'done') return 100
  if (task?.status === 'running' && currentTaskId.value && task.id === currentTaskId.value) {
    return Math.max(0, Math.min(100, Number(progress.value) || 0))
  }
  return 0
}

const findNextWaitingTask = (): Task | null => {
  const list = Array.isArray(taskStore.tasks) ? taskStore.tasks : []
  const waiting = list
    .filter((t): t is Task => t && t.status === 'waiting' && t.type === 'up' && t.uid && t.name)
    .slice()
    .sort((a, b) => Number(a.createdAt || 0) - Number(b.createdAt || 0))
  return waiting[0] || null
}

const maybeMarkOrphanRunningAsFailed = (): void => {
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

const startTaskBackend = async (
  task: Task, 
  force: boolean, 
  silent: boolean
): Promise<boolean> => {
  try {
    if (task.type === 'video') {
      const videoInfo = task.extra || {}
      const payload = {
        taskId: task.id,
        upName: '独立视频',
        force: !!force,
        video: {
          bvId: videoInfo.bvId || (task.id.startsWith('video::') ? task.id.split('::')[1] : ''),
          title: task.name,
          url: task.sourceUrl,
          uploadDate: videoInfo.uploadDate || null,
          duration: task.totalSeconds || null,
          uploader: videoInfo.uploader || null
        }
      }
      await http.post('/api/video/start', payload)
    } else {
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

const maybeAutoStartNext = async (silent: boolean): Promise<void> => {
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

const toggleSingleTask = (task: Task): void => {
  if (task.status === 'running') return

  const force = task.status === 'done'
  if (force) taskStore.resetTask(task.id)

  logs.value += `[${new Date().toLocaleTimeString()}] ${force ? '重新处理' : '开始'}任务: ${task?.name || 'UP'}\n`
  startTaskBackend(task, force, false)
}

const recentHistory = ref<unknown[]>([])
const activities = computed<ActivityItem[]>(() => {
  return recentHistory.value.slice(0, 4).map((h: unknown) => {
    const historyItem = h as { status?: string; title?: string; timestamp?: string }
    const ok = historyItem?.status === '成功'
    return {
      icon: ok ? 'check-circle' : 'close-circle',
      color: ok ? 'green' : 'red',
      title: `${ok ? '完成' : '失败'}：${historyItem?.title || '未知视频'}`,
      time: historyItem?.timestamp || '',
    }
  })
})

let statusPollInterval: ReturnType<typeof setInterval> | null = null
let historyPollCounter = 4

const updateStatus = async (): Promise<void> => {
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
      const data = Array.isArray(hr.data) ? hr.data : []
      recentHistory.value = data.sort((a, b) => {
        const timeA = new Date(a.createdAt || a.timestamp || 0).getTime()
        const timeB = new Date(b.createdAt || b.timestamp || 0).getTime()
        return timeB - timeA
      })
    }
    maybeMarkOrphanRunningAsFailed()
    maybeAutoStartNext(true)
  } catch (error) {
    console.error('获取状态失败:', error)
  }
}

const goHistory = (): void => {
  router.push('/history')
}

const onActivityClick = ({ item }: { item: ActivityItem }): void => {
  console.log('Activity clicked:', item)
}

const stopProcess = async (): Promise<void> => {
  try {
    await http.post('/api/stop')
    status.value = '已停止'
    MessagePlugin.success('已停止任务')
  } catch (error) {
    const msg = error?.userMessage || error?.message || '停止失败'
    MessagePlugin.error(msg)
  }
}

const clearLogs = (): void => {
  logs.value = ''
}

const hasGpu = computed<boolean>(() => gpuUsage.value > 0 || gpuMemory.value > 0)

const formatNumber = (num: number): string => {
  if (!num) return '未知'
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  }
  return String(num)
}

onMounted(() => {
  updateStatus()
  hydrateEstimatedDurations()
  statusPollInterval = setInterval(updateStatus, 1000)
})

onUnmounted(() => {
  if (statusPollInterval) {
    clearInterval(statusPollInterval)
  }
})
</script>

<style scoped>
.control-panel-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  gap: 24px;
  min-height: 0;
  height: 100%;
  width: 100%;
  box-sizing: border-box;
}

.grid-card {
  min-height: 0;
  height: 100%;
}

.grid-card :deep(.t-card__body) {
  flex: 1 !important;
  min-height: 0 !important;
  max-height: 100% !important;
  height: auto !important;
  display: flex !important;
  flex-direction: column !important;
  padding: 0 16px !important;
  overflow: hidden !important;
}

.grid-card :deep(.t-card__header) {
  padding: 12px 16px !important;
  flex-shrink: 0 !important;
  border-bottom: 1px solid #f0f0f0;
}

.card-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: 100%;
  overflow: hidden;
}

.card-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.card-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.card-body--scroll {
  overflow-y: auto;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
}

.scroll-container::-webkit-scrollbar {
  width: 4px;
  height: 4px;
}

.scroll-container::-webkit-scrollbar-track {
  background: transparent;
}

.scroll-container::-webkit-scrollbar-thumb {
  background-color: rgba(148, 163, 184, 0.4);
  border-radius: 2px;
}

.task-list-compact,
.activity-grid-compact {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
}

.empty-state-compact {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
}

.task-item-compact {
  padding: 10px 12px;
  border-radius: 6px;
  background-color: #f8fafc;
  transition: all 0.15s ease;
  animation: slideIn 0.2s ease-out;
}

.task-item-compact:hover {
  background-color: #f1f5f9;
}

.activity-item-compact {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
  min-width: 0;
  animation: fadeIn 0.2s ease-out;
}

.activity-item-compact:hover {
  background-color: #f8fafc;
}

.activity-empty-compact {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
}

.status-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  width: 100%;
  height: 100%;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@media (max-width: 1023px) {
  .control-panel-grid {
    grid-template-columns: 1fr;
    grid-template-rows: repeat(4, minmax(200px, auto));
    gap: 16px;
  }
}

@media (max-width: 639px) {
  .control-panel-grid {
    gap: 12px;
  }

  .grid-card :deep(.t-card__header) {
    padding: 10px 12px !important;
  }

  .grid-card :deep(.t-card__body) {
    padding: 12px !important;
  }
}
</style>
