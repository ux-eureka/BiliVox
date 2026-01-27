<template>
  <t-menu v-model="activeValue" theme="light" class="h-full flex flex-col" :collapsed="collapsed">
    <template #logo>
      <div class="flex items-center justify-center h-16 transition-all duration-300 overflow-hidden" :class="collapsed ? 'px-2' : 'px-6'">
        <t-icon name="logo-youtube" size="large" class="text-blue-600 flex-shrink-0" :class="collapsed ? '' : 'mr-2'" />
        <span v-show="!collapsed" class="text-xl font-bold text-gray-900 tracking-tight whitespace-nowrap transition-opacity duration-300">BiliVox</span>
      </div>
    </template>
    
    <t-menu-item value="/" to="/">
      <template #icon>
        <t-icon name="dashboard" />
      </template>
      控制面板
    </t-menu-item>
    <t-menu-item value="/files" to="/files">
      <template #icon>
        <t-icon name="folder" />
      </template>
      文件管理
    </t-menu-item>
    <t-menu-item value="/config" to="/config">
      <template #icon>
        <t-icon name="setting" />
      </template>
      配置中心
    </t-menu-item>
    <t-menu-item value="/history" to="/history">
      <template #icon>
        <t-icon name="history" />
      </template>
      历史记录
    </t-menu-item>

    <template #operations>
      <div class="p-4 border-t border-gray-100 mt-auto">
        <div class="flex items-center p-2 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors" :class="collapsed ? 'justify-center' : ''">
          <t-avatar class="bg-blue-600 text-white flex-shrink-0" :class="collapsed ? '' : 'mr-3'">U</t-avatar>
          <div v-show="!collapsed" class="overflow-hidden transition-all duration-300">
            <div class="text-sm font-bold text-gray-900 truncate">管理员</div>
            <div class="text-xs text-gray-500 truncate">admin@bilivox.com</div>
          </div>
        </div>
      </div>
    </template>
  </t-menu>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: String,
  collapsed: Boolean
})

const emit = defineEmits(['update:modelValue'])

const activeValue = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})
</script>