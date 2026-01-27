<template>
  <t-layout class="h-screen w-full overflow-hidden bg-canvas">
    <!-- 桌面端侧边栏 -->
    <t-aside v-if="!isMobile" :width="collapsed ? '64px' : '240px'" class="border-r border-border transition-all duration-300 relative flex flex-col bg-surface shadow-ui h-full">
      <AppMenu v-model="activeValue" :collapsed="collapsed" />
      
      <!-- 侧边栏切换按钮 -->
      <div class="absolute bottom-20 -right-3 z-10">
        <t-button shape="circle" size="small" theme="default" class="shadow-ui-lg border border-border" @click="collapsed = !collapsed">
          <template #icon>
            <t-icon :name="collapsed ? 'chevron-right' : 'chevron-left'" />
          </template>
        </t-button>
      </div>
    </t-aside>

    <!-- 移动端抽屉菜单 -->
    <t-drawer v-else v-model:visible="mobileMenuVisible" placement="left" :footer="false" :header="false" size="240px" class="mobile-menu-drawer">
      <div class="h-full flex flex-col">
        <AppMenu v-model="activeValue" :collapsed="false" @click="mobileMenuVisible = false" />
      </div>
    </t-drawer>

    <t-layout class="flex flex-col h-full overflow-hidden">
      <t-header class="bg-surface px-6 h-16 border-b border-border flex items-center justify-between shrink-0 shadow-ui z-10">
        <div class="flex items-center gap-3">
          <!-- 移动端菜单触发按钮 -->
          <t-button v-if="isMobile" variant="text" shape="square" @click="mobileMenuVisible = true">
            <template #icon><t-icon name="view-list" /></template>
          </t-button>
          <div class="text-lg font-bold text-gray-800">{{ currentRouteTitle }}</div>
        </div>
        
        <div class="flex items-center gap-4">
          <t-button shape="circle" variant="text" class="hidden sm:block" aria-label="通知">
            <t-icon name="notification" />
          </t-button>
          <t-button shape="circle" variant="text" aria-label="帮助" @click="showHelp = true">
            <t-icon name="help-circle" />
          </t-button>
        </div>
      </t-header>

      <t-content class="flex-1 overflow-auto bg-canvas relative">
        <div class="w-full px-6 py-6">
          <router-view v-slot="{ Component }">
            <transition name="fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </div>
      </t-content>
    </t-layout>

    <t-dialog v-model:visible="showHelp" header="关于 BiliVox" :footer="false" centered>
      <div class="text-center py-6">
        <t-icon name="logo-youtube" size="64px" class="text-blue-600 mb-4" />
        <h3 class="text-xl font-bold mb-2">BiliVox</h3>
        <p class="text-gray-500">v1.0.0</p>
        <p class="mt-4 text-gray-600">视频资料库构建工具，基于 TDesign 重构。</p>
      </div>
    </t-dialog>
  </t-layout>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { MessagePlugin } from 'tdesign-vue-next'
import { useRoute } from 'vue-router'
import AppMenu from './components/AppMenu.vue'
import { http } from './api/http'
import { useTaskStore } from './store/task'

const route = useRoute()
const showHelp = ref(false)
const activeValue = ref('/')
const collapsed = ref(false)
const taskStore = useTaskStore()
let monitorTimer = null

// 移动端适配
const isMobile = ref(false)
const mobileMenuVisible = ref(false)

const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
  if (isMobile.value) {
    collapsed.value = false // 移动端不需要折叠状态
  }
}

const pollMonitor = async (notify) => {
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
    if (notify && count > 0) {
      MessagePlugin.success(`监控发现 ${count} 个新投稿，已加入待处理任务`)
    }
  } catch (e) {
    return
  }
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  pollMonitor(false)
  monitorTimer = setInterval(() => pollMonitor(true), 10 * 60 * 1000)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
  if (monitorTimer) {
    clearInterval(monitorTimer)
    monitorTimer = null
  }
})

const navigationItems = [
  { title: '控制面板', path: '/' },
  { title: '文件管理', path: '/files' },
  { title: '配置中心', path: '/config' },
  { title: '历史记录', path: '/history' },
]

const currentRouteTitle = computed(() => {
  const item = navigationItems.find(i => i.path === route.path)
  return item ? item.title : 'BiliVox'
})

watch(() => route.path, (newPath) => {
  activeValue.value = newPath
  if (isMobile.value) {
    mobileMenuVisible.value = false // 移动端路由跳转后自动关闭抽屉
  }
}, { immediate: true })
</script>

<style>
/* 页面切换动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 640px) {
  .t-drawer__body {
    padding: 0 !important;
  }
}

/* 自定义滚动条 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
