<template>
  <div ref="containerRef" class="system-logs-container">
    <div ref="scrollRef" class="scroll-content" @scroll="onScroll">
      <div class="logs-wrapper">
        <div v-if="!hasContent" class="empty-state">
          <p class="text-sm">{{ emptyText }}</p>
        </div>
        <div v-else class="logs-content">
          <div v-for="(line, index) in logLines" :key="index" class="log-line">{{ line }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'

const props = defineProps({
  logs: { type: String, default: '' },
  emptyText: { type: String, default: '等待系统输出...' },
  paddingSize: { type: Number, default: 16 },
  persistScrollKey: { type: String, default: '' },
  autoScroll: { type: Boolean, default: true }
})

const emit = defineEmits(['scroll', 'reach-bottom'])

const containerRef = ref(null)
const scrollRef = ref(null)
const scrollTop = ref(0)
const mounted = ref(false)

const hasContent = computed(() => props.logs && props.logs.trim().length > 0)

const logLines = computed(() => {
  if (!props.logs) return []
  return props.logs.split('\n').filter(line => line.length > 0)
})

const onScroll = (e) => {
  scrollTop.value = e.target.scrollTop
  const { scrollHeight, clientHeight } = e.target
  const distanceToBottom = scrollHeight - scrollTop.value - clientHeight
  if (distanceToBottom <= 5) {
    emit('reach-bottom')
  }
  emit('scroll', { scrollTop: scrollTop.value, scrollHeight, clientHeight })
}

const scrollToBottom = () => {
  if (scrollRef.value) {
    scrollRef.value.scrollTop = scrollRef.value.scrollHeight
  }
}

const saveScroll = () => {
  if (props.persistScrollKey && mounted.value) {
    localStorage.setItem(`scroll_${props.persistScrollKey}`, String(Math.round(scrollTop.value)))
  }
}

const restoreScroll = () => {
  if (props.persistScrollKey && scrollRef.value) {
    const saved = localStorage.getItem(`scroll_${props.persistScrollKey}`)
    if (saved !== null) {
      scrollRef.value.scrollTop = parseInt(saved, 10)
      scrollTop.value = parseInt(saved, 10)
    }
  }
}

watch(() => props.logs, () => {
  nextTick(() => {
    saveScroll()
    if (props.autoScroll) {
      scrollToBottom()
    }
  })
})

onMounted(() => {
  mounted.value = true
  nextTick(() => {
    restoreScroll()
    scrollToBottom()
  })
})

defineExpose({ scrollToBottom })
</script>

<style scoped>
.system-logs-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.scroll-content {
  flex: 1;
  min-height: 0;
  max-height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  background-color: #fafafa;
}

.logs-wrapper {
  padding: 16px;
  box-sizing: border-box;
  min-height: 100%;
}

.logs-content {
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.6;
}

.log-line {
  white-space: pre-wrap;
  word-break: break-word;
  overflow-wrap: break-word;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #6b7280;
}

/* 滚动条样式 */
.scroll-content::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.scroll-content::-webkit-scrollbar-track {
  background: transparent;
}

.scroll-content::-webkit-scrollbar-thumb {
  background-color: rgba(148, 163, 184, 0.4);
  border-radius: 3px;
}

.scroll-content::-webkit-scrollbar-thumb:hover {
  background-color: rgba(148, 163, 184, 0.6);
}
</style>
