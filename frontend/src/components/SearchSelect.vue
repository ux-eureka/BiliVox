<template>
  <div class="relative" ref="rootRef" :style="containerStyle">
    <t-input
      v-model="keyword"
      :placeholder="placeholder"
      :disabled="disabled"
      @keydown="onKeydown"
      @focus="openPanel"
      @blur="onBlur"
      class="w-full"
    >
    </t-input>
    <t-popup v-model="visible" placement="bottom-left" :attach="rootRef" :overlay-style="{ width: popupWidth }">
      <template #content>
        <div class="bg-white border border-gray-200 rounded shadow-lg max-h-56 overflow-auto">
          <div v-if="loading" class="px-3 py-2 text-xs text-gray-500 flex items-center gap-2">
            <t-icon name="loading" class="animate-spin" /> 正在搜索…
          </div>
          <div v-else-if="results.length === 0" class="px-3 py-2 text-xs text-gray-500">无匹配数据</div>
          <ul v-else>
            <li
              v-for="(item, idx) in results"
              :key="item.value"
              @mousedown.prevent="selectItem(item)"
              :class="['px-3 py-2 cursor-pointer text-sm flex items-center justify-between', idx === activeIndex ? 'bg-blue-50' : '']"
            >
              <span v-html="highlight(item.label)"></span>
              <t-icon v-if="selectedSet.has(item.value)" name="check" class="text-blue-600" />
            </li>
          </ul>
        </div>
      </template>
    </t-popup>
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted, onBeforeUnmount } from 'vue'
import { http } from '../api/http'
import { MessagePlugin } from 'tdesign-vue-next'

const props = defineProps({
  modelValue: { type: Array, default: () => [] }, // 兼容原有多选
  options: { type: Array, default: () => [] },    // { label, value }
  placeholder: { type: String, default: '筛选 UP 主' },
  disabled: { type: Boolean, default: false },
  width: { type: [String, Number], default: '160px' }, // 保持与原下拉一致
})
const emit = defineEmits(['update:modelValue', 'change'])

const keyword = ref('')
const visible = ref(false)
const loading = ref(false)
const results = ref([])
const activeIndex = ref(0)
const selectedSet = ref(new Set(props.modelValue))
const rootRef = ref(null)

const containerStyle = computed(() => ({
  width: typeof props.width === 'number' ? `${props.width}px` : props.width,
}))
const popupWidth = computed(() => containerStyle.value.width)

const debounce = (fn, delay) => {
  let t = null
  return (...args) => {
    if (t) clearTimeout(t)
    t = setTimeout(() => fn(...args), delay)
  }
}

const doSearch = async (q) => {
  loading.value = true
  try {
    // 异步拉取最新文件与 UP 列表，再在前端过滤
    const resp = await http.get('/api/files')
    const ups = Array.from(new Set((resp.data?.upList || []).concat((resp.data?.files || []).map(f => f.up).filter(Boolean))))
    const items = ups.map(u => ({ label: u, value: u }))
    const s = String(q || '').trim().toLowerCase()
    results.value = s ? items.filter(i => i.label.toLowerCase().includes(s)) : items.slice(0, 50)
    activeIndex.value = 0
  } catch (e) {
    results.value = []
    MessagePlugin.error(e?.userMessage || '搜索失败')
  } finally {
    loading.value = false
  }
}
const debouncedSearch = debounce(doSearch, 300)

watch(keyword, (v) => {
  visible.value = true
  debouncedSearch(v)
})

watch(() => props.modelValue, (arr) => {
  selectedSet.value = new Set(arr || [])
})

const openPanel = () => {
  visible.value = true
  debouncedSearch(keyword.value)
}
const onBlur = () => {
  setTimeout(() => { visible.value = false }, 150)
}

const selectItem = (item) => {
  const set = new Set(selectedSet.value)
  if (set.has(item.value)) set.delete(item.value)
  else set.add(item.value)
  const arr = Array.from(set)
  selectedSet.value = new Set(arr)
  emit('update:modelValue', arr)
  emit('change', arr) // 兼容原 onChange
}

const onKeydown = (e) => {
  if (!visible.value || results.value.length === 0) return
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    activeIndex.value = Math.min(results.value.length - 1, activeIndex.value + 1)
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    activeIndex.value = Math.max(0, activeIndex.value - 1)
  } else if (e.key === 'Enter') {
    e.preventDefault()
    const item = results.value[activeIndex.value]
    if (item) selectItem(item)
  }
}

const highlight = (text) => {
  const q = String(keyword.value || '').trim()
  if (!q) return String(text || '')
  const escaped = q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const regex = new RegExp(`(${escaped})`, 'gi')
  return String(text || '').replace(regex, '<span class="text-blue-600 font-bold bg-yellow-100">$1</span>')
}

const handleClickOutside = (ev) => {
  if (!rootRef.value) return
  if (!rootRef.value.contains(ev.target)) visible.value = false
}
onMounted(() => document.addEventListener('mousedown', handleClickOutside))
onBeforeUnmount(() => document.removeEventListener('mousedown', handleClickOutside))
</script>

<style scoped>
.relative {
  position: relative;
}
:deep(.t-input) {
  height: 32px;
}
:deep(.t-input__inner) {
  height: 32px;
  line-height: 32px;
}
</style>
