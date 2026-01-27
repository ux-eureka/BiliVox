import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'ControlPanel',
    component: () => import('../views/ControlPanel.vue')
  },
  {
    path: '/config',
    name: 'Config',
    component: () => import('../views/Config.vue')
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('../views/History.vue')
  },
  {
    path: '/files',
    name: 'Files',
    component: () => import('../views/Files.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
