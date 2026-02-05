<template>
  <div class="h-full flex flex-col">
    <!-- 头部栏 -->
    <t-card :bordered="false" class="mb-6 rounded-lg">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-xl font-bold text-gray-900">文件管理</h2>
          <p class="text-sm text-gray-500 mt-1">查看和管理已生成的知识库文件</p>
        </div>
        <div class="ml-auto flex items-center text-sm text-gray-500">
          <t-button variant="outline" @click="fetchFiles">
            <template #icon><t-icon name="refresh" /></template>
            刷新
          </t-button>
        </div>
      </div>
    </t-card>

    <!-- 文件列表 -->
    <t-card :bordered="false" class="flex-1 overflow-hidden flex flex-col relative">
      <div class="mb-4 flex gap-3 items-center">
        <div class="flex items-center gap-3">
          <t-input v-model="searchQuery" placeholder="搜索文件..." class="w-64" clearable>
            <template #prefix-icon><t-icon name="search" /></template>
          </t-input>
          <!-- 新增：支持实时搜索的输入型筛选组件（与搜索框高度一致） -->
          <SearchSelect
            :model-value="filterValue.up || []"
            :options="upOptions"
            placeholder="筛选 UP 主"
            width="160px"
            @update:modelValue="(vals) => filterValue.up = vals"
            @change="(vals) => onFilterChange({ ...filterValue, up: vals })"
          />
        </div>
        <t-select v-model="sortBy" :options="sortOptions" placeholder="排序方式" class="w-36" />
        <div class="ml-auto flex items-center text-sm text-gray-500">
          共 <span class="font-bold text-gray-900 mx-1">{{ filteredFiles.length }}</span> 个文件
        </div>
      </div>

      <div class="flex-1 overflow-auto pb-16 task-list-container">
        <t-table
          :data="filteredFiles"
          :columns="columns"
          row-key="path"
          hover
          :pagination="pagination"
          :selected-row-keys="selectedRowKeys"
          @select-change="onSelectChange"
          :filter-value="filterValue"
          @filter-change="onFilterChange"
        >
          <template #name="{ row }">
            <div class="flex items-center">
              <div class="w-8 h-8 rounded bg-blue-50 text-blue-600 flex items-center justify-center mr-3 flex-shrink-0">
                <t-icon name="file" />
              </div>
              <span 
                class="font-medium text-gray-900 hover:text-blue-600 cursor-pointer transition-colors truncate" 
                :title="row.name" 
                @click="previewFile(row)"
                v-html="highlight(row.name)"
              ></span>
            </div>
          </template>
          
          <template #bv="{ row }">
            <span v-if="row.bv" class="font-mono text-xs bg-gray-100 px-1 py-0.5 rounded" v-html="highlight(row.bv)"></span>
            <span v-else class="text-gray-300">-</span>
          </template>
          
          <template #date="{ row }">
             <span v-if="row.date && row.date !== '未知'">{{ row.date }}</span>
             <span v-else class="text-gray-300">未知</span>
          </template>

          <template #up="{ row }">
            <t-tag variant="light" theme="default" class="truncate max-w-full" :title="row.up" v-html="highlight(row.up)"></t-tag>
          </template>
          
          <template #op="{ row }">
            <div class="flex justify-end gap-2">
              <t-button variant="text" shape="square" theme="primary" title="预览" @click="previewFile(row)">
                <t-icon name="browse" />
              </t-button>
              <t-button variant="text" shape="square" theme="default" title="下载" @click="downloadFile(row)">
                <t-icon name="download" />
              </t-button>
              <t-button variant="text" shape="square" theme="danger" title="删除" @click="deleteFile(row)">
                <t-icon name="delete" />
              </t-button>
            </div>
          </template>
        </t-table>
      </div>

      <!-- 悬浮操作栏 -->
      <transition
        enter-active-class="transition ease-out duration-200"
        enter-from-class="opacity-0 translate-y-10"
        enter-to-class="opacity-100 translate-y-0"
        leave-active-class="transition ease-in duration-150"
        leave-from-class="opacity-100 translate-y-0"
        leave-to-class="opacity-0 translate-y-10"
      >
        <div v-if="selectedRowKeys.length > 0" class="fixed bottom-12 left-1/2 transform -translate-x-1/2 z-50">
          <div class="bg-gray-900 text-white px-6 py-3 rounded-full shadow-lg flex items-center gap-6">
            <div class="text-sm">
              已选择 <span class="font-bold text-blue-400 text-lg mx-1">{{ selectedRowKeys.length }}</span> 项
            </div>
            <div class="h-4 w-px bg-gray-700"></div>
            <div class="flex items-center gap-2">
              <t-button theme="primary" size="small" :loading="batchDownloading" @click="batchDownload">
                <template #icon><t-icon name="download" /></template>
                下载
              </t-button>
              <t-button theme="default" size="small" :loading="batchMerging" @click="batchMerge">
                <template #icon><t-icon name="file-add" /></template>
                合并下载
              </t-button>
              <t-button theme="danger" size="small" @click="batchDelete">
                <template #icon><t-icon name="delete" /></template>
                删除
              </t-button>
              <t-button theme="danger" variant="text" size="small" @click="clearSelection">
                取消
              </t-button>
            </div>
          </div>
        </div>
      </transition>
    </t-card>

    <t-dialog v-model:visible="previewVisible" :header="previewTitle" width="960px" :confirm-btn="null" cancel-btn="关闭">
      <div class="space-y-3">
        <div class="flex items-center justify-between gap-3">
          <div class="text-xs text-gray-500 truncate" :title="previewPath">路径：{{ previewPath }}</div>
          <div class="flex items-center gap-2">
            <t-button size="small" variant="outline" :loading="previewLoading" @click="reloadPreview">刷新</t-button>
            <t-button size="small" theme="primary" variant="outline" :disabled="!previewContent" @click="copyPreview">复制</t-button>
          </div>
        </div>
        <div class="border border-gray-100 rounded bg-gray-900 text-gray-100 p-4 font-mono text-xs overflow-auto custom-scrollbar" style="max-height: 60vh;">
          <div v-if="previewLoading" class="text-gray-400">加载中...</div>
          <pre v-else class="whitespace-pre-wrap break-words">{{ previewContent }}</pre>
        </div>
      </div>
    </t-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, onUnmounted } from 'vue'
import { MessagePlugin, DialogPlugin, Checkbox } from 'tdesign-vue-next'
import { http } from '../api/http'
import { useRoute } from 'vue-router'

const files = ref([])
const upList = ref([])
// const selectedUp = ref(null) // Removed
const searchQuery = ref('')
const debouncedSearchQuery = ref('')
const sortBy = ref('date')
const route = useRoute()
const containerRef = ref(null) // 滚动容器引用

const selectedRowKeys = ref([])
const batchDownloading = ref(false)
const batchMerging = ref(false)
const selectionMode = ref('multiple')
const filterValue = ref({}) // Column filter state

const previewVisible = ref(false)
const previewLoading = ref(false)
const previewTitle = ref('预览')
const previewPath = ref('')
const previewContent = ref('')

const sortOptions = [
  { value: 'date', label: '最新日期' },
  { value: 'name', label: '文件名称' },
  { value: 'up', label: 'UP 主' }
]

const debounce = (fn, delay) => {
  let timer = null
  return function (...args) {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      fn.apply(this, args)
    }, delay)
  }
}

watch(searchQuery, debounce((val) => {
  debouncedSearchQuery.value = val
}, 300))

const highlight = (text) => {
  if (!text) return ''
  if (!debouncedSearchQuery.value) return String(text)
  const query = debouncedSearchQuery.value.trim()
  if (!query) return String(text)
  // Escape regex special characters
  const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const regex = new RegExp(`(${escaped})`, 'gi')
  return String(text).replace(regex, '<span class="text-blue-600 font-bold bg-yellow-100">$1</span>')
}

const setSelectionMode = (mode) => {
  const next = mode === 'single' ? 'single' : 'multiple'
  selectionMode.value = next
  if (next === 'single' && selectedRowKeys.value.length > 1) {
    selectedRowKeys.value = [selectedRowKeys.value[selectedRowKeys.value.length - 1]]
  }
}

const columns = computed(() => [
  {
    colKey: 'row-select',
    type: 'multiple',
    width: 60,
    fixed: 'left',
    title: (h) => {
      return h(
        'div',
        { title: selectionMode.value === 'multiple' ? '多选模式（关闭为单选）' : '单选模式（开启为多选）', style: { display: 'flex', justifyContent: 'center', cursor: 'pointer' } },
        [
          h(Checkbox, {
            checked: selectionMode.value === 'multiple',
            onChange: (checked) => setSelectionMode(checked ? 'multiple' : 'single'),
          }),
        ],
      )
    },
  },
  { colKey: 'name', title: '文件名', width: '30%', ellipsis: true },
  { colKey: 'bv', title: 'BV号', width: '120', ellipsis: true },
  { colKey: 'date', title: '上传日期', width: '120', sorter: true },
  { colKey: 'up', title: 'UP 主', width: '20%' },
  { colKey: 'op', title: '操作', width: '140', align: 'right', fixed: 'right' },
])

const pagination = computed(() => ({
  defaultPageSize: 10,
  totalContent: false,
  showJumper: true,
  total: filteredFiles.value.length
}))

const upOptions = computed(() => {
  // 从文件列表动态提取 UP 主列表，确保选项真实存在
  const ups = new Set(files.value.map(f => f.up).filter(Boolean))
  // 如果有后端返回的 upList，也合并进去
  upList.value.forEach(up => ups.add(up))
  return Array.from(ups).map(up => ({ label: up, value: up }))
})

// 计算属性：过滤后的文件
const filteredFiles = computed(() => {
  let result = [...files.value]
  
  // Filter by UP (Column Filter)
  if (filterValue.value.up && filterValue.value.up.length > 0) {
    result = result.filter(f => filterValue.value.up.includes(f.up))
  }
  
  // Fuzzy Search
  if (debouncedSearchQuery.value) {
    const query = debouncedSearchQuery.value.toLowerCase()
    result = result.filter(f => 
      f.name.toLowerCase().includes(query) ||
      f.up.toLowerCase().includes(query) ||
      (f.bv && f.bv.toLowerCase().includes(query)) ||
      (f.title && f.title.toLowerCase().includes(query))
    )
  }
  
  result.sort((a, b) => {
    switch (sortBy.value) {
      case 'date':
        return (Number(b.modifiedTs) || 0) - (Number(a.modifiedTs) || 0)
      case 'name':
        return a.name.localeCompare(b.name)
      case 'up':
        return a.up.localeCompare(b.up)
      default:
        return 0
    }
  })
  
  return result
})

const fetchFiles = async () => {
  try {
    const response = await http.get('/api/files')
    files.value = response.data.files
    upList.value = response.data.upList
    selectedRowKeys.value = []
  } catch (error) {
    MessagePlugin.error('获取文件列表失败: ' + (error?.userMessage || error.message))
    files.value = []
    upList.value = []
  }
}

const onFilterChange = (val) => {
  filterValue.value = val
}

const onSelectChange = (val, ctx) => {
  const next = Array.isArray(val) ? val : []
  if (selectionMode.value === 'single') {
    const currentKey = ctx?.currentRowKey ?? ctx?.currentKey ?? ctx?.rowKey
    const chosen = currentKey ?? next[next.length - 1]
    selectedRowKeys.value = chosen != null ? [chosen] : []
    return
  }
  selectedRowKeys.value = next
}

const clearSelection = () => {
  selectedRowKeys.value = []
}

const batchDownload = async () => {
  if (selectedRowKeys.value.length === 0) return
  
  batchDownloading.value = true
  try {
    const response = await http.post(
      '/api/files/batch-download', 
      { files: selectedRowKeys.value },
      { responseType: 'blob' }
    )
    
    const blob = new Blob([response.data], { type: 'application/zip' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    // 从 header 获取文件名，或生成默认名
    let filename = 'bilivox_batch.zip'
    const disposition = response.headers['content-disposition']
    if (disposition && disposition.indexOf('attachment') !== -1) {
      const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/
      const matches = filenameRegex.exec(disposition)
      if (matches != null && matches[1]) { 
        filename = matches[1].replace(/['"]/g, '')
      }
    }
    
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    MessagePlugin.success('下载已开始')
    clearSelection()
  } catch (error) {
    MessagePlugin.error(error?.userMessage || '批量下载失败')
  } finally {
    batchDownloading.value = false
  }
}

const batchMerge = async () => {
  if (selectedRowKeys.value.length === 0) return
  
  batchMerging.value = true
  try {
    const response = await http.post(
      '/api/files/batch-merge', 
      { files: selectedRowKeys.value },
      { responseType: 'blob' }
    )
    
    const blob = new Blob([response.data], { type: 'text/markdown' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    let filename = 'bilivox_merged.md'
    const disposition = response.headers['content-disposition']
    if (disposition && disposition.indexOf('attachment') !== -1) {
      const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/
      const matches = filenameRegex.exec(disposition)
      if (matches != null && matches[1]) { 
        filename = matches[1].replace(/['"]/g, '')
      }
    }
    
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    MessagePlugin.success('合并下载已开始')
    clearSelection()
  } catch (error) {
    MessagePlugin.error(error?.userMessage || '合并下载失败')
  } finally {
    batchMerging.value = false
  }
}

const batchDelete = async () => {
  if (selectedRowKeys.value.length === 0) return
  
  const instance = DialogPlugin.confirm({
    header: '确认批量删除',
    body: `确定要删除选中的 ${selectedRowKeys.value.length} 个文件吗？\n此操作不可恢复。`,
    confirmBtn: { theme: 'danger', content: '确认删除' },
    cancelBtn: '取消',
    onConfirm: async () => {
      try {
        const response = await http.post('/api/files/batch-delete', { files: selectedRowKeys.value })
        MessagePlugin.success(response.data.message || '删除成功')
        clearSelection()
        await fetchFiles()
      } catch (error) {
        MessagePlugin.error(error?.userMessage || '批量删除失败')
      } finally {
        instance.destroy()
      }
    },
    onClose: () => instance.destroy(),
  })
}

const previewFile = async (row) => {
  previewTitle.value = row?.name || '预览'
  previewPath.value = row?.path || ''
  previewContent.value = ''
  previewVisible.value = true
  await reloadPreview()
}

const reloadPreview = async () => {
  if (!previewPath.value) return
  previewLoading.value = true
  try {
    const response = await http.get('/api/output', { params: { path: previewPath.value } })
    previewContent.value = response.data?.content || ''
  } catch (error) {
    MessagePlugin.error(error?.userMessage || '预览失败')
  } finally {
    previewLoading.value = false
  }
}

const copyPreview = async () => {
  try {
    await navigator.clipboard.writeText(previewContent.value || '')
    MessagePlugin.success('已复制')
  } catch (e) {
    MessagePlugin.error('复制失败')
  }
}

const downloadFile = async (row) => {
  const path = row?.path
  const name = row?.name || 'file.md'
  if (!path) return
  try {
    const response = await http.get('/api/download', { params: { path }, responseType: 'blob' })
    const blobUrl = URL.createObjectURL(response.data)
    const a = document.createElement('a')
    a.href = blobUrl
    a.download = name
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(blobUrl)
    MessagePlugin.success('开始下载')
  } catch (error) {
    MessagePlugin.error(error?.userMessage || '下载失败')
  }
}

const deleteFile = async (row) => {
  const path = row?.path
  if (!path) return
  const instance = DialogPlugin.confirm({
    header: '确认删除',
    body: `确定要删除该文件吗？\n${row?.name || path}`,
    confirmBtn: '删除',
    cancelBtn: '取消',
    onConfirm: async () => {
      try {
        await http.post('/api/file/delete', { path })
        MessagePlugin.success('已删除')
        await fetchFiles()
      } catch (e) {
        MessagePlugin.error(e?.userMessage || '删除失败')
      } finally {
        instance.destroy()
      }
    },
    onClose: () => instance.destroy(),
  })
}

// 滚动条高度监听
let resizeObserver = null

onMounted(() => {
  const keyword = String(route?.query?.keyword || '').trim()
  if (keyword) {
    try {
      searchQuery.value = decodeURIComponent(keyword)
    } catch (e) {
      searchQuery.value = keyword
    }
  }
  
  const presetUp = String(route?.query?.up || '').trim()
  if (presetUp) {
    try {
      const decodedUp = decodeURIComponent(presetUp)
      filterValue.value = { up: [decodedUp] }
    } catch (e) {
      filterValue.value = { up: [presetUp] }
    }
  }
  fetchFiles()

  // 初始化 ResizeObserver
  const container = document.querySelector('.task-list-container')
  if (container) {
    resizeObserver = new ResizeObserver(entries => {
      for (let entry of entries) {
        // 如果内容高度 <= 300，可以考虑隐藏滚动条（通过 CSS 或动态样式）
        // 这里主要通过 CSS max-height: 300px + overflow-y: auto 控制
        // 当内容不足时，浏览器会自动隐藏滚动条，无需额外 JS 干预
      }
    })
    resizeObserver.observe(container.firstElementChild || container)
  }
})

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
})
</script>

<style scoped>
.task-list-container {
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}
/* 隐藏 TDesign 表格自带的滚动条，使用外层容器滚动 */
:deep(.t-table__content) {
  overflow: visible !important;
}
:deep(.t-table--layout-fixed) {
  height: auto !important;
}

.up-column-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
</style>
