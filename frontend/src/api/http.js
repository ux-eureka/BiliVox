import axios from 'axios'

export const API_KEY_STORAGE_KEY = 'bilivox.apiKey'

export const http = axios.create({
  baseURL: '',
  timeout: 30000,
})

http.interceptors.request.use((config) => {
  const apiKey = localStorage.getItem(API_KEY_STORAGE_KEY)
  if (apiKey) {
    config.headers = config.headers || {}
    config.headers['X-API-Key'] = apiKey
  }
  return config
})

http.interceptors.response.use(
  (res) => res,
  (error) => {
    const status = error?.response?.status
    const detail = error?.response?.data?.detail
    if (status === 401) {
      error.userMessage = '未授权：服务端启用了 API Key，请先配置 API Key'
    } else if (typeof detail === 'string' && detail) {
      error.userMessage = detail
    } else if (error?.code === 'ECONNABORTED') {
      error.userMessage = '请求超时'
    } else {
      error.userMessage = '请求失败'
    }
    return Promise.reject(error)
  }
)
