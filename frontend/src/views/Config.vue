<template>
  <div class="h-full flex flex-col">
    <!-- 顶部操作栏 -->
    <t-card :bordered="false" class="mb-6 rounded-lg">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-xl font-bold text-gray-900">系统配置</h2>
          <p class="text-sm text-gray-500 mt-1">管理监控目标与系统运行参数</p>
        </div>
        <t-button theme="primary" :loading="saving" @click="saveConfig">
          <template #icon><t-icon name="save" /></template>
          保存变更
        </t-button>
      </div>
    </t-card>

    <!-- 主要内容区域 -->
    <t-card :bordered="false" class="flex-1 overflow-hidden">
      <t-tabs v-model="activeTab" class="flex-1 flex flex-col min-h-0 custom-tabs">
        <t-tab-panel value="monitor" label="监控配置" :destroy-on-hide="false" class="flex-1 overflow-auto">
          <div class="p-6">
            <div class="flex items-center justify-end mb-4">
              <t-button theme="primary" variant="outline" :loading="pollingMonitor" @click="pollMonitorAndQueue">
                <template #icon><t-icon name="refresh" /></template>
                检查更新并加入待处理
              </t-button>
            </div>
            <t-row :gutter="[24, 24]">
              <!-- 添加卡片 -->
              <t-col :span="3" :xs="12" :sm="6" :md="4" :lg="3">
                <div 
                  class="h-48 border-2 border-dashed border-gray-300 rounded-lg flex flex-col items-center justify-center cursor-pointer hover:border-blue-500 hover:bg-blue-50 transition-all group"
                  @click="showAddDialog = true"
                >
                  <t-icon name="add-circle" size="48px" class="text-gray-400 group-hover:text-blue-500 mb-2 transition-colors" />
                  <span class="text-gray-500 group-hover:text-blue-500 font-medium transition-colors">添加 UP 主</span>
                </div>
              </t-col>

              <!-- UP主列表 -->
              <t-col 
                v-for="(up, index) in config.upList" 
                :key="index"
                :span="3" :xs="12" :sm="6" :md="4" :lg="3"
              >
                <div class="h-48 border border-gray-200 rounded-lg p-6 flex flex-col justify-between hover:shadow-lg transition-shadow relative group bg-white">
                  <div class="flex justify-between items-start">
                    <t-avatar size="56px" class="bg-blue-600 text-white font-bold text-xl">
                      {{ up.name.charAt(0) }}
                    </t-avatar>
                    <t-button shape="circle" variant="text" theme="danger" class="opacity-0 group-hover:opacity-100 transition-opacity" @click="removeUp(index)">
                      <template #icon><t-icon name="close" /></template>
                    </t-button>
                  </div>
                  <div>
                    <h3 class="text-lg font-bold text-gray-900 truncate" :title="up.name">{{ up.name }}</h3>
                    <div class="flex items-center mt-2 text-gray-500 text-sm bg-gray-50 px-2 py-1 rounded w-fit">
                      <t-icon name="user" size="14px" class="mr-1" />
                      <span class="font-mono">{{ up.uid }}</span>
                    </div>
                  </div>
                </div>
              </t-col>
            </t-row>
          </div>
        </t-tab-panel>

        <t-tab-panel value="pipeline" label="处理模式" :destroy-on-hide="false" class="flex-1 overflow-auto">
          <div class="p-6 max-w-5xl">
            <t-form :data="config" label-align="top">
              <div class="bg-blue-50/50 rounded-xl p-5 border border-blue-100 mb-6">
                <h3 class="text-lg font-bold mb-4 flex items-center gap-2 text-blue-900">
                  <t-icon name="control-platform" />
                  模式选择
                </h3>
                <t-form-item label="Pipeline 模式" name="pipeline.mode">
                  <t-radio-group v-model="config.pipeline.mode" variant="default-filled">
                    <t-radio-button value="local">本地处理 (Local)</t-radio-button>
                    <t-radio-button value="bibigpt">BibiGPT API</t-radio-button>
                  </t-radio-group>
                  <div class="text-xs text-gray-500 mt-2">
                    <template v-if="config.pipeline.mode === 'local'">
                      使用本地显卡/CPU 进行转录与 LLM 整理，无需额外付费，但需消耗本地算力。
                    </template>
                    <template v-else>
                      直接调用 BibiGPT 云端 API，速度极快且不占用本地资源，需配置 API Token。
                    </template>
                  </div>
                </t-form-item>
              </div>

              <div v-if="config.pipeline.mode === 'local'" class="mt-6 space-y-6">
                <!-- 转录配置 -->
                <div class="bg-purple-50 rounded-xl p-5 border border-purple-100">
                  <h3 class="text-lg font-bold mb-4 flex items-center gap-2 text-purple-900">
                    <t-icon name="sound" />
                    本地转录配置 (Whisper)
                  </h3>
                  <t-row :gutter="24">
                    <t-col :span="6">
                      <t-form-item label="模型大小" name="transcribe.model_name" help="模型越大精度越高，但速度越慢">
                        <t-select v-model="config.transcribe.model_name" :options="['tiny', 'base', 'small', 'medium', 'large-v3']" />
                      </t-form-item>
                    </t-col>
                    <t-col :span="6">
                      <t-form-item label="计算设备" name="transcribe.device">
                        <t-select v-model="config.transcribe.device" :options="['cuda', 'cpu']" />
                      </t-form-item>
                    </t-col>
                    <t-col :span="6">
                      <t-form-item label="计算精度" name="transcribe.compute_type">
                        <t-select v-model="config.transcribe.compute_type" :options="['float16', 'int8_float16', 'int8']" />
                      </t-form-item>
                    </t-col>
                    <t-col :span="6">
                      <t-form-item 
                        label="批处理大小 (Batch Size)" 
                        name="transcribe.batch_size" 
                        :help="config.transcribe.device === 'cuda' ? '建议：8G显存设24-32，16G设48-64，24G+设64-128' : 'CPU 模式下建议保持较小值 (1-16)'"
                      >
                        <div class="w-full px-2">
                          <t-slider 
                            v-model="config.transcribe.batch_size" 
                            :min="1" 
                            :max="128" 
                            :label="true" 
                          />
                        </div>
                      </t-form-item>
                    </t-col>
                    <t-col :span="6" v-if="config.transcribe.device === 'cuda'">
                      <t-form-item label="Beam Size" name="transcribe.beam_size" help="搜索束宽（建议 1~5，越小越快但精度稍降）">
                        <div class="w-full px-2">
                          <t-slider v-model="config.transcribe.beam_size" :min="1" :max="10" :label="true" />
                        </div>
                      </t-form-item>
                    </t-col>
                  </t-row>
                </div>

                <!-- LLM 配置 -->
                <div class="bg-gray-50 rounded-xl p-5 border border-gray-200">
                  <h3 class="text-lg font-bold mb-4 flex items-center gap-2">
                    <t-icon name="chat" />
                    本地 LLM 配置
                  </h3>
                  <t-row :gutter="24">
                    <t-col :span="12">
                      <t-form-item label="系统提示词 (System Prompt)" name="llm.system_prompt">
                        <t-textarea v-model="config.llm.system_prompt" :autosize="{ minRows: 3, maxRows: 6 }" />
                      </t-form-item>
                    </t-col>
                    <t-col :span="6">
                      <t-form-item label="温度 (Temperature)" name="llm.temperature" help="值越高，回答越随机">
                        <div class="w-full px-2">
                          <t-slider v-model="config.llm.temperature" :min="0" :max="2" :step="0.1" :label="true" />
                        </div>
                      </t-form-item>
                    </t-col>
                    <t-col :span="6">
                      <t-form-item label="最大生成长度" name="llm.max_tokens">
                        <t-input-number v-model="config.llm.max_tokens" theme="column" />
                      </t-form-item>
                    </t-col>
                  </t-row>
                </div>
              </div>

              <div v-if="config.pipeline.mode === 'bibigpt'" class="bg-gray-50 rounded-xl p-5 border border-gray-200">
                <h3 class="text-lg font-bold mb-4 flex items-center gap-2">
                  <t-icon name="cloud" />
                  BibiGPT 配置
                </h3>
                <t-row :gutter="[24, 24]">
                  <t-col :span="12">
                    <t-form-item label="API 地址" name="bibigpt.api_url">
                      <t-input v-model="config.bibigpt.api_url" placeholder="默认：https://api.bibigpt.co/api" />
                    </t-form-item>
                  </t-col>
                  <t-col :span="12">
                    <t-form-item label="API Token" name="bibigpt.token">
                      <t-input v-model="config.bibigpt.token" type="password" placeholder="请输入您的 BibiGPT Token" />
                      <div class="text-xs text-gray-500 mt-1">
                        请前往 <a href="https://bibigpt.co" target="_blank" class="text-blue-600 hover:underline">bibigpt.co</a> 获取
                      </div>
                    </t-form-item>
                  </t-col>
                </t-row>
              </div>
            </t-form>
          </div>
        </t-tab-panel>
        
        <t-tab-panel value="download" label="下载设置" :destroy-on-hide="false" class="flex-1 overflow-auto">
          <div class="p-6 max-w-5xl">
            <t-form :data="config" label-align="top">

              <div class="mb-8">
                <h3 class="text-lg font-bold mb-4 flex items-center">
                  <span class="w-1 h-6 bg-slate-600 rounded mr-3"></span>
                  本地服务访问控制
                  <t-tag class="ml-3" size="small" variant="light" :theme="apiKeyEnabled ? 'warning' : 'success'">
                    {{ apiKeyEnabled ? '已启用 API Key' : '未启用 API Key' }}
                  </t-tag>
                </h3>
                <t-row :gutter="24">
                  <t-col :span="12">
                    <t-form-item
                      label="后端 API Key（可选）"
                      help="用于保护本机 BiliVox 后端接口（会作为 X-API-Key 请求头发送）。不是 DeepSeek/OpenAI 的 Key。"
                    >
                      <div class="flex items-center gap-2">
                        <t-input v-model="apiKeyInput" type="password" placeholder="留空表示不配置（未启用时可不填）" class="flex-1" />
                        <t-button theme="primary" variant="outline" @click="saveApiKey">保存</t-button>
                      </div>
                    </t-form-item>
                  </t-col>
                </t-row>
              </div>
              
              <!-- 下载配置 -->
              <div class="mb-8">
                <h3 class="text-lg font-bold mb-4 flex items-center">
                  <span class="w-1 h-6 bg-blue-600 rounded mr-3"></span>
                  下载配置
                </h3>
                <t-row :gutter="24">
                  <t-col :span="6">
                    <t-form-item label="临时目录" name="download.temp_dir">
                      <div class="flex items-center gap-2">
                        <t-input
                          v-model="config.download.temp_dir"
                          class="flex-1 path-input"
                          :status="tempDirStatus"
                          :tips="tempDirTips"
                          :title="config.download.temp_dir"
                        />
                        <t-button
                          theme="default"
                          variant="outline"
                          :loading="tempDirPicking"
                          @click="pickFolder('temp_dir')"
                        >
                          <template #icon><t-icon name="folder" /></template>
                          选择文件夹
                        </t-button>
                      </div>
                    </t-form-item>
                  </t-col>
                  <t-col :span="6">
                    <t-form-item label="输出目录" name="download.output_dir">
                      <div class="flex items-center gap-2">
                        <t-input
                          v-model="config.download.output_dir"
                          class="flex-1 path-input"
                          :status="outputDirStatus"
                          :tips="outputDirTips"
                          :title="config.download.output_dir"
                        />
                        <t-button
                          theme="default"
                          variant="outline"
                          :loading="outputDirPicking"
                          @click="pickFolder('output_dir')"
                        >
                          <template #icon><t-icon name="folder" /></template>
                          选择文件夹
                        </t-button>
                      </div>
                    </t-form-item>
                  </t-col>
                  <t-col :span="6">
                    <t-form-item label="音频格式" name="download.audio_format">
                      <t-select v-model="config.download.audio_format" :options="['m4a', 'mp3', 'wav']" />
                    </t-form-item>
                  </t-col>
                  <t-col :span="6">
                    <t-form-item
                      label="FFmpeg 路径（可选）"
                      name="download.ffmpeg_location"
                      help="修复下载时报 ffmpeg/ffprobe not found。填写 ffmpeg.exe 路径或其所在目录。"
                    >
                      <div class="flex items-center gap-2">
                        <t-input v-model="config.download.ffmpeg_location" class="flex-1" :title="config.download.ffmpeg_location" placeholder="例如：D:\\ffmpeg\\bin\\ffmpeg.exe" />
                        <t-button theme="default" variant="outline" :loading="ffmpegPicking" @click="pickFfmpeg">
                          <template #icon><t-icon name="folder-open" /></template>
                          选择文件
                        </t-button>
                      </div>
                    </t-form-item>
                  </t-col>
                  <t-col :span="6">
                    <t-form-item
                      label="浏览器 Cookie 来源（可选）"
                      name="download.cookies_from_browser"
                      help="用于解决 B 站风控导致的 UP 投稿列表拉取失败（352/-799）。建议选 chrome 或 edge。"
                    >
                      <t-select
                        v-model="config.download.cookies_from_browser"
                        :options="[
                          { label: '不使用', value: '' },
                          { label: 'Chrome', value: 'chrome' },
                          { label: 'Edge', value: 'edge' },
                        ]"
                      />
                    </t-form-item>
                  </t-col>
                  <t-col :span="6">
                    <t-form-item
                      label="Cookie 文件（可选）"
                      name="download.cookiefile"
                      help="优先级高于浏览器来源。填写 cookies.txt 文件路径（yt-dlp 兼容格式）。"
                    >
                      <div class="flex items-center gap-2">
                        <t-input v-model="config.download.cookiefile" class="flex-1" :title="config.download.cookiefile" placeholder="例如：D:\\cookies.txt" />
                        <t-button theme="default" variant="outline" :loading="cookieFilePicking" @click="pickCookieFile">
                          <template #icon><t-icon name="folder-open" /></template>
                          选择文件
                        </t-button>
                      </div>
                    </t-form-item>
                  </t-col>
                </t-row>
              </div>

              <t-divider />

            </t-form>
          </div>
        </t-tab-panel>
      </t-tabs>
    </t-card>

    <!-- 添加 UP 主对话框 -->
    <t-dialog
      v-model:visible="showAddDialog"
      header="添加监控目标"
      :confirm-btn="{ content: '确认', loading: addingUp, disabled: !canAddUp }"
      @confirm="addUp"
    >
      <div class="space-y-4">
        <t-input
          v-model="newUpUrl"
          label="UP 主主页链接或 UID"
          placeholder="例如：https://space.bilibili.com/1505790047"
          :status="addUpStatus"
          :tips="addUpTips"
          @enter="addUp"
        >
          <template #prefix-icon><t-icon name="link" /></template>
        </t-input>
      </div>
    </t-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { MessagePlugin } from 'tdesign-vue-next'
import { http } from '../api/http'
import { API_KEY_STORAGE_KEY } from '../api/http'
import { useTaskStore } from '../store/task'
import { useRouter } from 'vue-router'

// 状态
const activeTab = ref('monitor')
const saving = ref(false)
const showAddDialog = ref(false)
const addingUp = ref(false)
const addUpStatus = ref('default')
const addUpTips = ref('')

const tempDirPicking = ref(false)
const outputDirPicking = ref(false)
const cookieFilePicking = ref(false)
const ffmpegPicking = ref(false)
const tempDirStatus = ref('default')
const outputDirStatus = ref('default')
const tempDirTips = ref('')
const outputDirTips = ref('')

const apiKeyEnabled = ref(false)
const apiKeyInput = ref(localStorage.getItem(API_KEY_STORAGE_KEY) || '')
const taskStore = useTaskStore()
const router = useRouter()

// 完整配置结构
const config = ref({
  upList: [],
  download: {
    temp_dir: 'temp',
    output_dir: 'output',
    audio_format: 'm4a',
    ffmpeg_location: '',
    cookiefile: '',
    cookies_from_browser: '',
    headers: {}
  },
  transcribe: {
    model_name: 'large-v3',
    compute_type: 'float16',
    device: 'cuda',
    batch_size: 24,
    beam_size: 5
  },
  llm: {
    enabled: true,
    system_prompt: '',
    temperature: 0.3,
    max_tokens: 4096
  },
  pipeline: {
    mode: 'local'
  },
  bibigpt: {
    api_url: 'https://api.bibigpt.co/api',
    token: ''
  }
})

const newUpUrl = ref('')
const pollingMonitor = ref(false)

const normalizeSpaceUrlOrUid = (raw) => {
  const v = String(raw || '').trim()
  if (!v) return null
  if (/^\d+$/.test(v)) return `https://space.bilibili.com/${v}`
  if (/^https?:\/\//i.test(v)) return v
  return null
}

const canAddUp = computed(() => {
  if (addingUp.value) return false
  return !!normalizeSpaceUrlOrUid(newUpUrl.value)
})

// 获取配置
const fetchConfig = async () => {
  try {
    const response = await http.get('/api/config')
    // 合并默认值以防后端返回空对象
    config.value = {
      upList: response.data.upList || [],
      download: { ...config.value.download, ...response.data.download },
      transcribe: { ...config.value.transcribe, ...response.data.transcribe },
      llm: { ...config.value.llm, ...response.data.llm },
      pipeline: { ...config.value.pipeline, ...response.data.pipeline },
      bibigpt: { ...config.value.bibigpt, ...response.data.bibigpt }
    }
  } catch (error) {
    MessagePlugin.error('获取配置失败: ' + (error?.userMessage || error.message))
  }
}

// 保存配置
const saveConfig = async () => {
  saving.value = true
  try {
    await http.post('/api/config', config.value)
    MessagePlugin.success('配置保存成功')
  } catch (error) {
    MessagePlugin.error('保存失败: ' + (error?.userMessage || error.message))
  } finally {
    saving.value = false
  }
}

const addUp = async () => {
  const url = normalizeSpaceUrlOrUid(newUpUrl.value)
  if (!url || addingUp.value) return

  addUpStatus.value = 'default'
  addUpTips.value = ''
  addingUp.value = true
  try {
    const resp = await http.post('/api/monitor/targets', { input: url })
    const upList = Array.isArray(resp.data?.upList) ? resp.data.upList : null
    if (upList) config.value.upList = upList
    newUpUrl.value = ''
    showAddDialog.value = false
    MessagePlugin.success('已添加到监控列表')
  } catch (error) {
    addUpStatus.value = 'error'
    addUpTips.value = error?.userMessage || '解析失败'
    MessagePlugin.error(addUpTips.value)
  } finally {
    addingUp.value = false
  }
}

// 删除 UP 主
const removeUp = async (index) => {
  const uid = String(config.value.upList?.[index]?.uid ?? '').trim()
  if (!uid) return
  try {
    const resp = await http.delete(`/api/monitor/targets/${encodeURIComponent(uid)}`)
    const upList = Array.isArray(resp.data?.upList) ? resp.data.upList : null
    if (upList) config.value.upList = upList
    else config.value.upList.splice(index, 1)
    MessagePlugin.success('已移除')
  } catch (error) {
    MessagePlugin.error(error?.userMessage || '移除失败')
  }
}

const pollMonitorAndQueue = async () => {
  if (pollingMonitor.value) return
  pollingMonitor.value = true
  try {
    const resp = await http.post('/api/monitor/poll', { maxPerUp: 1 })
    const events = Array.isArray(resp.data?.events) ? resp.data.events : []
    let count = 0
    for (const e of events) {
      const uid = String(e?.uid ?? '').trim()
      const name = String(e?.name ?? '').trim()
      const videos = Array.isArray(e?.videos) ? e.videos : []
      if (!uid || videos.length === 0) continue
      taskStore.addTasksFromUpVideos({ uid, name }, `https://space.bilibili.com/${uid}`, videos)
      count += videos.length
    }
    if (count <= 0) {
      MessagePlugin.info('未发现新投稿')
      return
    }
    MessagePlugin.success(`发现 ${count} 个新投稿，已加入待处理任务`)
    router.push('/')
  } catch (error) {
    MessagePlugin.error(error?.userMessage || '检查失败')
  } finally {
    pollingMonitor.value = false
  }
}

onMounted(() => {
  fetchConfig()
  fetchAuthStatus()
})

const fetchAuthStatus = async () => {
  try {
    const response = await http.get('/api/auth_status')
    apiKeyEnabled.value = !!response.data?.enabled
  } catch (e) {
    apiKeyEnabled.value = false
  }
}

const saveApiKey = () => {
  const v = String(apiKeyInput.value || '').trim()
  if (v) localStorage.setItem(API_KEY_STORAGE_KEY, v)
  else localStorage.removeItem(API_KEY_STORAGE_KEY)
  MessagePlugin.success('API Key 已保存')
}

const pickFolder = async (target) => {
  const pickingRef = target === 'temp_dir' ? tempDirPicking : outputDirPicking
  const statusRef = target === 'temp_dir' ? tempDirStatus : outputDirStatus
  const tipsRef = target === 'temp_dir' ? tempDirTips : outputDirTips

  pickingRef.value = true
  statusRef.value = 'default'
  tipsRef.value = ''

  try {
    const initial = target === 'temp_dir' ? config.value.download.temp_dir : config.value.download.output_dir
    const response = await http.get('/api/select_folder', {
      params: {
        title: '选择文件夹',
        initial,
      },
    })

    const selectedPath = response.data?.path
    if (!selectedPath) {
      return
    }

    if (target === 'temp_dir') {
      config.value.download.temp_dir = selectedPath
    } else {
      config.value.download.output_dir = selectedPath
    }

    statusRef.value = 'success'
    MessagePlugin.success('选择成功')
    setTimeout(() => {
      statusRef.value = 'default'
    }, 1500)
  } catch (error) {
    statusRef.value = 'error'
    tipsRef.value = error?.response?.data?.detail || '选择失败'
    MessagePlugin.error(tipsRef.value)
  } finally {
    pickingRef.value = false
  }
}

const pickCookieFile = async () => {
  if (cookieFilePicking.value) return
  cookieFilePicking.value = true
  try {
    const initial = config.value.download.cookiefile || ''
    const response = await http.get('/api/select_file', {
      params: {
        title: '选择 cookies.txt',
        initial,
        filetypes: 'cookies.txt|cookies.txt;Text|*.txt;All|*',
      },
    })
    const selectedPath = response.data?.path
    if (!selectedPath) return
    config.value.download.cookiefile = selectedPath
    MessagePlugin.success('已选择 cookies.txt')
  } catch (error) {
    MessagePlugin.error(error?.userMessage || error?.response?.data?.detail || '选择失败')
  } finally {
    cookieFilePicking.value = false
  }
}

const pickFfmpeg = async () => {
  if (ffmpegPicking.value) return
  ffmpegPicking.value = true
  try {
    const initial = config.value.download.ffmpeg_location || ''
    const response = await http.get('/api/select_file', {
      params: {
        title: '选择 ffmpeg.exe',
        initial,
        filetypes: 'ffmpeg.exe|ffmpeg.exe;All|*',
      },
    })
    const selectedPath = response.data?.path
    if (!selectedPath) return
    config.value.download.ffmpeg_location = selectedPath
    MessagePlugin.success('已选择 ffmpeg.exe')
  } catch (error) {
    MessagePlugin.error(error?.userMessage || error?.response?.data?.detail || '选择失败')
  } finally {
    ffmpegPicking.value = false
  }
}
</script>

<style scoped>
.path-input :deep(.t-input__inner) {
  text-overflow: ellipsis;
}
</style>
