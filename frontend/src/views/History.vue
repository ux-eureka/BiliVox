<template>
  <div class="flex flex-col gap-6">
    <!-- 顶部统计卡片 -->
    <t-row :gutter="24">
      <t-col :span="3" :xs="6" :sm="6" :md="3">
        <t-card :bordered="false" hover-shadow class="cursor-pointer">
          <div class="flex items-center">
            <div class="w-12 h-12 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center mr-4">
              <t-icon name="history" size="24px" />
            </div>
            <div>
              <div class="text-gray-500 text-xs font-bold uppercase mb-1">总处理次数</div>
              <div class="text-2xl font-bold text-gray-900">{{ history.length }}</div>
            </div>
          </div>
        </t-card>
      </t-col>
      <t-col :span="3" :xs="6" :sm="6" :md="3">
        <t-card :bordered="false" hover-shadow class="cursor-pointer">
          <div class="flex items-center">
            <div class="w-12 h-12 rounded-lg bg-green-50 text-green-600 flex items-center justify-center mr-4">
              <t-icon name="check-circle" size="24px" />
            </div>
            <div>
              <div class="text-gray-500 text-xs font-bold uppercase mb-1">成功率</div>
              <div class="text-2xl font-bold text-gray-900">{{ successRate }}%</div>
            </div>
          </div>
        </t-card>
      </t-col>
      <t-col :span="3" :xs="6" :sm="6" :md="3">
        <t-card :bordered="false" hover-shadow class="cursor-pointer">
          <div class="flex items-center">
            <div class="w-12 h-12 rounded-lg bg-orange-50 text-orange-600 flex items-center justify-center mr-4">
              <t-icon name="time" size="24px" />
            </div>
            <div>
              <div class="text-gray-500 text-xs font-bold uppercase mb-1">平均耗时</div>
              <div class="text-2xl font-bold text-gray-900">{{ averageTimeLabel }}</div>
            </div>
          </div>
        </t-card>
      </t-col>
      <t-col :span="3" :xs="6" :sm="6" :md="3">
        <t-card :bordered="false" hover-shadow class="cursor-pointer">
          <div class="flex items-center">
            <div class="w-12 h-12 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center mr-4">
              <t-icon name="calendar" size="24px" />
            </div>
            <div>
              <div class="text-gray-500 text-xs font-bold uppercase mb-1">今日处理</div>
              <div class="text-2xl font-bold text-gray-900">{{ todayCount }}</div>
            </div>
          </div>
        </t-card>
      </t-col>
    </t-row>

    <!-- 图表区域 -->
    <t-row :gutter="24">
      <t-col :span="8" :xs="12">
        <t-card title="处理趋势 (近7天)" :bordered="false" class="h-80">
          <v-chart class="h-full w-full" :option="trendOption" autoresize />
        </t-card>
      </t-col>
      <t-col :span="4" :xs="12">
        <t-card title="状态分布" :bordered="false" class="h-80">
          <v-chart class="h-full w-full" :option="pieOption" autoresize />
        </t-card>
      </t-col>
    </t-row>

    <!-- 列表操作栏 -->
    <t-card :bordered="false">
      <div class="flex flex-wrap gap-4 justify-between items-center mb-4">
        <div class="flex gap-4 items-center flex-1">
          <t-input v-model="searchQuery" placeholder="搜索 UP主 或 视频标题" class="w-64">
            <template #prefix-icon><t-icon name="search" /></template>
          </t-input>
          <t-select v-model="statusFilter" :options="statusOptions" placeholder="状态过滤" clearable class="w-40" />
          <t-date-range-picker v-model="dateRange" placeholder="选择时间范围" class="w-64" />
        </div>
        <div class="flex gap-2">
          <t-button variant="outline" @click="fetchHistory">
            <template #icon><t-icon name="refresh" /></template>
            刷新
          </t-button>
          <t-button variant="outline" @click="exportHistory" :disabled="filteredHistory.length === 0">
            <template #icon><t-icon name="download" /></template>
            导出
          </t-button>
        </div>
      </div>

      <!-- 数据表格 -->
      <t-table
        :data="filteredHistory"
        :columns="columns"
        row-key="taskId"
        hover
        :pagination="pagination"
        :loading="loading"
        stripe
      >
        <template #status="{ row }">
          <t-tag :theme="row.status === '成功' ? 'success' : 'danger'" variant="light">
            <template #icon>
              <t-icon :name="row.status === '成功' ? 'check-circle' : 'close-circle'" />
            </template>
            {{ row.status }}
          </t-tag>
        </template>
        
        <template #op="{ row }">
          <t-button variant="text" theme="primary" size="small" @click="showDetail(row)">详情</t-button>
        </template>
      </t-table>
    </t-card>

    <!-- 详情弹窗 -->
    <t-dialog v-model:visible="detailVisible" header="记录详情" :footer="false">
      <div v-if="currentRecord" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <div class="text-gray-500 text-sm mb-1">UP 主</div>
            <div class="font-bold">{{ currentRecord.upName }}</div>
          </div>
          <div>
            <div class="text-gray-500 text-sm mb-1">处理时间</div>
            <div class="font-bold">{{ currentRecord.timestamp }}</div>
          </div>
          <div class="col-span-2">
            <div class="text-gray-500 text-sm mb-1">视频标题</div>
            <div class="font-bold">{{ currentRecord.title }}</div>
          </div>
          <div>
            <div class="text-gray-500 text-sm mb-1">状态</div>
            <t-tag :theme="currentRecord.status === '成功' ? 'success' : 'danger'" variant="light">
              {{ currentRecord.status }}
            </t-tag>
          </div>
          <div>
             <div class="text-gray-500 text-sm mb-1">耗时</div>
             <div class="font-bold">{{ durationLabel(currentRecord) }}</div>
          </div>
        </div>
        <div class="bg-gray-50 p-4 rounded text-sm text-gray-700 font-mono mt-4 border border-gray-100">
          {{ recordDetail(currentRecord) }}
        </div>
      </div>
    </t-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { MessagePlugin } from 'tdesign-vue-next'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, TitleComponent } from 'echarts/components'
import { http } from '../api/http'

use([CanvasRenderer, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent])

const history = ref([])
const loading = ref(false)
const searchQuery = ref('')
const statusFilter = ref('')
const dateRange = ref([])
const detailVisible = ref(false)
const currentRecord = ref(null)

const statusOptions = [
  { label: '成功', value: '成功' },
  { label: '失败', value: '失败' }
]

const columns = [
  { colKey: 'upName', title: 'UP 主', width: '20%' },
  { colKey: 'title', title: '视频标题', width: '35%', ellipsis: true },
  { colKey: 'timestamp', title: '处理时间', width: '20%', sorter: true },
  { colKey: 'status', title: '状态', width: '15%' },
  { colKey: 'op', title: '操作', width: '10%', align: 'center', fixed: 'right' }
]

const pagination = {
  defaultPageSize: 10,
  totalContent: false,
  showJumper: true
}

const parseTimestampMs = (ts) => {
  const s = String(ts || '').trim()
  if (!s) return null
  const m = s.match(/^(\d{4})-(\d{2})-(\d{2})(?:\s+(\d{2}):(\d{2})(?::(\d{2}))?)?$/)
  if (!m) return null
  const year = Number(m[1])
  const month = Number(m[2]) - 1
  const day = Number(m[3])
  const hh = Number(m[4] || 0)
  const mm = Number(m[5] || 0)
  const ss = Number(m[6] || 0)
  const d = new Date(year, month, day, hh, mm, ss)
  const ms = d.getTime()
  return Number.isFinite(ms) ? ms : null
}

// 图表配置
const trendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { top: 30, right: 20, bottom: 20, left: 40, containLabel: true },
  xAxis: { type: 'category', data: trendData.value.labels },
  yAxis: { type: 'value' },
  series: [
    {
      data: trendData.value.counts,
      type: 'line',
      smooth: true,
      color: '#0052D9',
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [{ offset: 0, color: 'rgba(0, 82, 217, 0.3)' }, { offset: 1, color: 'rgba(0, 82, 217, 0)' }]
        }
      }
    }
  ]
}))

const pieOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: '0%', left: 'center' },
  series: [
    {
      name: '状态分布',
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
      label: { show: false, position: 'center' },
      emphasis: { label: { show: true, fontSize: 20, fontWeight: 'bold' } },
      data: [
        { value: history.value.filter(h => h.status === '成功').length, name: '成功', itemStyle: { color: '#00A870' } },
        { value: history.value.filter(h => h.status === '失败').length, name: '失败', itemStyle: { color: '#E34D59' } }
      ]
    }
  ]
}))

// 计算属性
const filteredHistory = computed(() => {
  let result = [...history.value]
  
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(h => h.upName.toLowerCase().includes(query) || h.title.toLowerCase().includes(query))
  }
  
  if (statusFilter.value) {
    result = result.filter(h => h.status === statusFilter.value)
  }

  if (dateRange.value && dateRange.value.length === 2) {
    const startRaw = dateRange.value[0]
    const endRaw = dateRange.value[1]
    const startMs = parseTimestampMs(String(startRaw).slice(0, 10))
    const endMs = parseTimestampMs(String(endRaw).slice(0, 10))
    if (startMs != null && endMs != null) {
      const start = startMs
      const end = endMs + 24 * 3600 * 1000 - 1
      result = result.filter(h => {
        const ms = parseTimestampMs(h?.timestamp)
        return ms != null && ms >= start && ms <= end
      })
    }
  }
  
  return result
})

const successRate = computed(() => {
  if (history.value.length === 0) return 0
  const successCount = history.value.filter(h => h.status === '成功').length
  return Math.round((successCount / history.value.length) * 100)
})

const todayCount = computed(() => {
  const now = new Date()
  const y = now.getFullYear()
  const m = now.getMonth()
  const d = now.getDate()
  const start = new Date(y, m, d, 0, 0, 0).getTime()
  const end = new Date(y, m, d, 23, 59, 59, 999).getTime()
  return history.value.filter(h => {
    const ms = parseTimestampMs(h?.timestamp)
    return ms != null && ms >= start && ms <= end
  }).length
})

const averageTimeLabel = computed(() => {
  const durations = history.value
    .map(h => Number(h?.durationSec))
    .filter(v => Number.isFinite(v) && v > 0)
  if (durations.length === 0) return '—'
  const avg = Math.round(durations.reduce((a, b) => a + b, 0) / durations.length)
  return `${avg}s`
})

const trendData = computed(() => {
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const labels = []
  const counts = []
  for (let i = 6; i >= 0; i -= 1) {
    const d = new Date(today.getTime() - i * 24 * 3600 * 1000)
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    labels.push(key.slice(5))
    counts.push(
      history.value.filter(h => String(h?.timestamp || '').startsWith(key)).length
    )
  }
  return { labels, counts }
})

const durationLabel = (record) => {
  const v = Number(record?.durationSec)
  if (Number.isFinite(v) && v >= 0) return `${v}s`
  return '—'
}

const recordDetail = (record) => {
  const parts = []
  const detail = String(record?.detail || '').trim()
  if (detail) parts.push(detail)
  const d = Number(record?.downloadSec)
  const a = Number(record?.asrSec)
  const l = Number(record?.llmSec)
  const dur = Number(record?.durationSec)
  if (Number.isFinite(d) || Number.isFinite(a) || Number.isFinite(l) || Number.isFinite(dur)) {
    const seg = []
    if (Number.isFinite(d)) seg.push(`download=${d}s`)
    if (Number.isFinite(a)) seg.push(`asr=${a}s`)
    if (Number.isFinite(l)) seg.push(`llm=${l}s`)
    if (Number.isFinite(dur)) seg.push(`total=${dur}s`)
    if (seg.length) parts.push(seg.join(' | '))
  }
  const filePath = String(record?.filePath || '').trim()
  if (filePath) parts.push(`file=${filePath}`)
  return parts.length ? parts.join('\n') : '无详细信息'
}


// 方法
const fetchHistory = async () => {
  loading.value = true
  try {
    const response = await http.get('/api/history')
    history.value = response.data
  } catch (error) {
    MessagePlugin.error('获取历史记录失败: ' + (error?.userMessage || error.message))
    history.value = []
  } finally {
    loading.value = false
  }
}

const showDetail = (row) => {
  currentRecord.value = row
  detailVisible.value = true
}

const exportHistory = async () => {
  try {
    const data = filteredHistory.value.map(h => ({ ...h }))
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `history-${new Date().toISOString().slice(0, 10)}.json`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  } catch (e) {
    MessagePlugin.error('导出失败')
  }
}

onMounted(() => {
  fetchHistory()
})
</script>

<style scoped>
/* 确保图表容器有高度 */
.v-chart {
  height: 100%;
  width: 100%;
}
</style>
