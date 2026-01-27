import { createApp } from 'vue'
import { createPinia } from 'pinia'
import TDesign from 'tdesign-vue-next'
import App from './App.vue'
import router from './router'

// 引入 TDesign 样式
import 'tdesign-vue-next/es/style/index.css'
import './style.css'

const app = createApp(App)

app.use(TDesign)
app.use(createPinia())
app.use(router)

app.mount('#app')
