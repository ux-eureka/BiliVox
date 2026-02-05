import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useTaskStore = defineStore('task', () => {
  const STORAGE_KEY = 'bilivox.tasks.v2'
  const tasks = ref([])

  const hashString = (s) => {
    const str = String(s || '')
    let h = 2166136261
    for (let i = 0; i < str.length; i += 1) {
      h ^= str.charCodeAt(i)
      h = Math.imul(h, 16777619)
    }
    return h >>> 0
  }

  const estimateVideoSeconds = (videoLike) => {
    const bvId = String(videoLike?.bvId || videoLike?.bv_id || '').trim()
    const title = String(videoLike?.title || '').trim()
    const uid = String(videoLike?.uid || '').trim()
    const baseKey = bvId || title || uid || String(Date.now())
    const h = hashString(baseKey)

    let minMinutes = 8
    let maxMinutes = 90
    if (title.includes('直播') || title.includes('回放')) {
      minMinutes = 20
      maxMinutes = 240
    } else if (title.includes('合集')) {
      minMinutes = 15
      maxMinutes = 180
    }

    const minutes = minMinutes + (h % (maxMinutes - minMinutes + 1))
    return Math.max(60, minutes * 60)
  }

  const save = () => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks.value))
    } catch (e) {
      // ignore
    }
  }

  const load = () => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (!raw) return
      const parsed = JSON.parse(raw)
      if (Array.isArray(parsed)) tasks.value = parsed
    } catch (e) {
      // ignore
    }
  }

  const normalizeAfterLoad = () => {
    const now = Date.now()
    tasks.value = tasks.value
      .filter(t => t && t.id)
      .map(t => ({
        id: t.id,
        type: t.type || 'up',
        sourceUrl: t.sourceUrl || t.url || '',
        uid: t.uid || '',
        name: t.name || '',
        videoCount: Number.isFinite(t.videoCount) ? t.videoCount : (Number.isFinite(t.count) ? t.count : 0),
        totalSeconds: Number.isFinite(t.totalSeconds) ? t.totalSeconds : 0,
        processedSeconds: Number.isFinite(t.processedSeconds) ? t.processedSeconds : 0,
        status: t.status || 'waiting',
        lastOutputPath: t.lastOutputPath || t.outputPath || '',
        lastOutputName: t.lastOutputName || t.outputName || '',
        lastOutputAt: Number.isFinite(t.lastOutputAt) ? t.lastOutputAt : (Number.isFinite(t.outputAt) ? t.outputAt : null),
        durationEstimated: !!t.durationEstimated,
        lastError: t.lastError || '',
        failCount: Number.isFinite(t.failCount) ? t.failCount : 0,
        failedAt: Number.isFinite(t.failedAt) ? t.failedAt : null,
        createdAt: t.createdAt || now,
        firstStartedAt: t.firstStartedAt || null,
        lastStartedAt: t.lastStartedAt || null,
        lastTickAt: t.lastTickAt || null,
      }))

    for (const task of tasks.value) {
      if (!task.totalSeconds || task.totalSeconds <= 0) {
        const h = hashString(`${task.uid}::${task.name}::${task.videoCount}`)
        const minutes = 30 + (h % 151)
        task.totalSeconds = minutes * 60
        task.durationEstimated = true
      }
    }
    save()
  }

  const addOrReplaceTask = (task) => {
    const idx = tasks.value.findIndex(t => t.id === task.id)
    if (idx >= 0) tasks.value.splice(idx, 1, task)
    else tasks.value.push(task)
    save()
    return task.id
  }

  const addVideoTask = (videoInfo, sourceUrl) => {
    const now = Date.now()
    const bvId = String(videoInfo?.bvId || videoInfo?.bvid || '').trim()
    const title = String(videoInfo?.title || '').trim()
    const duration = Number.isFinite(videoInfo?.duration) ? Number(videoInfo.duration) : 0
    
    // 估算时长
    let totalSeconds = duration
    let estimated = false
    if (totalSeconds <= 0) {
      totalSeconds = estimateVideoSeconds({ bvId, title })
      estimated = true
    }

    const id = bvId ? `video::${bvId}` : `video::manual::${now}`
    // 直接返回 task.id
    const task = {
      id,
      type: 'video',
      sourceUrl: sourceUrl || '',
      uid: '', // 单视频任务不绑定特定 UID 列表，或者后续可补充 UP 信息
      name: title || bvId || '未知视频',
      videoCount: 1,
      totalSeconds: Math.max(0, totalSeconds),
      processedSeconds: 0,
      status: 'waiting',
      lastOutputPath: '',
      lastOutputName: '',
      lastOutputAt: null,
      durationEstimated: estimated,
      lastError: '',
      failCount: 0,
      failedAt: null,
      createdAt: now,
      firstStartedAt: null,
      lastStartedAt: null,
      lastTickAt: null,
      // 保存完整的视频信息以便后端使用
      extra: { ...videoInfo } 
    }
    addOrReplaceTask(task)
    return id
  }

  const addUpTaskFromUpVideos = (upInfo, sourceUrl, videos) => {
    const now = Date.now()
    const uid = String(upInfo?.uid ?? '').trim()
    const name = String(upInfo?.name ?? '').trim()
    const list = Array.isArray(videos) ? videos : []

    let totalSeconds = 0
    let estimated = false
    for (const v of list) {
      const duration = Number.isFinite(v?.duration) ? Number(v.duration) : 0
      if (duration > 0) totalSeconds += Math.floor(duration)
      else {
        totalSeconds += estimateVideoSeconds({ bvId: v?.bvId || v?.bv_id, title: v?.title, uid })
        estimated = true
      }
    }

    const id = uid ? `up::${uid}` : `up::manual::${now}`
    // 直接返回 task.id
    const task = {
      id,
      type: 'up',
      sourceUrl: sourceUrl || '',
      uid,
      name,
      videoCount: list.length,
      totalSeconds: Math.max(0, totalSeconds),
      processedSeconds: 0,
      status: 'waiting',
      lastOutputPath: '',
      lastOutputName: '',
      lastOutputAt: null,
      durationEstimated: estimated || totalSeconds <= 0,
      lastError: '',
      failCount: 0,
      failedAt: null,
      createdAt: now,
      firstStartedAt: null,
      lastStartedAt: null,
      lastTickAt: null,
    }
    addOrReplaceTask(task)
    return id
  }

  const removeTask = (id) => {
    const idx = tasks.value.findIndex(t => t.id === id)
    if (idx !== -1) {
      tasks.value.splice(idx, 1)
      save()
    }
  }

  const clearTasks = () => {
    tasks.value = []
    save()
  }

  const replaceTasks = (nextTasks) => {
    tasks.value = Array.isArray(nextTasks) ? nextTasks : []
    save()
  }

  const startTask = (id) => {
    const task = tasks.value.find(t => t.id === id)
    if (!task) return
    if (task.status === 'done') return
    const now = Date.now()
    if (!task.firstStartedAt) task.firstStartedAt = now
    task.lastStartedAt = now
    task.lastTickAt = now
    task.status = 'running'
    save()
  }

  const pauseTask = (id) => {
    const task = tasks.value.find(t => t.id === id)
    if (!task) return
    if (task.status !== 'running') return
    const now = Date.now()
    if (task.lastTickAt) {
      const deltaSec = Math.floor((now - task.lastTickAt) / 1000)
      if (deltaSec > 0) task.processedSeconds += deltaSec
    }
    task.lastTickAt = null
    task.status = 'paused'
    save()
  }

  const toggleTask = (id) => {
    const task = tasks.value.find(t => t.id === id)
    if (!task) return
    if (task.status === 'running') pauseTask(id)
    else startTask(id)
  }

  const startAll = () => {
    for (const task of tasks.value) {
      if (task.status === 'done') continue
      if (task.status === 'running') continue
      startTask(task.id)
    }
  }

  const resetTask = (id) => {
    const task = tasks.value.find(t => t.id === id)
    if (!task) return
    task.processedSeconds = 0
    task.lastTickAt = null
    task.status = 'waiting'
    task.lastOutputPath = ''
    task.lastOutputName = ''
    task.lastOutputAt = null
    task.lastError = ''
    task.failedAt = null
    save()
  }

  const setTaskLastOutput = (id, output) => {
    const task = tasks.value.find(t => t.id === id)
    if (!task) return
    task.lastOutputPath = output?.path || ''
    task.lastOutputName = output?.name || ''
    task.lastOutputAt = Number.isFinite(output?.at) ? output.at : (Number.isFinite(output?.outputAt) ? output.outputAt : null)
    save()
  }

  const markTaskDone = (id) => {
    const task = tasks.value.find(t => t.id === id)
    if (!task) return
    task.status = 'done'
    task.lastTickAt = null
    task.lastError = ''
    task.failedAt = null
    save()
  }

  const markTaskFailed = (id, message) => {
    const task = tasks.value.find(t => t.id === id)
    if (!task) return
    task.status = 'failed'
    task.lastTickAt = null
    task.lastError = String(message || '处理失败')
    task.failedAt = Date.now()
    task.failCount = (Number.isFinite(task.failCount) ? task.failCount : 0) + 1
    save()
  }
  
  const markTaskTerminated = (id) => {
    const task = tasks.value.find(t => t.id === id)
    if (!task) return
    task.status = 'terminated'
    task.lastTickAt = null
    save()
  }

  const setTaskDuration = (id, totalSeconds) => {
    const task = tasks.value.find(t => t.id === id)
    if (!task) return
    const v = Math.max(0, Math.floor(Number(totalSeconds) || 0))
    if (v <= 0) return
    task.totalSeconds = v
    task.durationEstimated = false
    save()
  }

  load()
  normalizeAfterLoad()

  return {
    tasks,
    addVideoTask,
    addUpTaskFromUpVideos,
    removeTask,
    clearTasks,
    replaceTasks,
    startTask,
    pauseTask,
    toggleTask,
    startAll,
    resetTask,
    setTaskLastOutput,
    markTaskDone,
    markTaskFailed,
    markTaskTerminated,
    setTaskDuration,
  }
})
