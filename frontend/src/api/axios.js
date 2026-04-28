// src/api/axios.js
import axios from 'axios'

// Для Vue CLI: process.env.VUE_APP_*
const API_URL = process.env.VUE_APP_API_URL || 'http://127.0.0.1:8000'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 15000,
  // 🔥 Важно для CORS: отправлять куки/авторизацию
  withCredentials: false
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  // Логи для отладки
  console.log(`[axios] → ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`)
  return config
}, error => {
  console.error('[axios] Request error:', error)
  return Promise.reject(error)
})

api.interceptors.response.use(response => {
  console.log(`[axios] ← ${response.status} ${response.config.url}`)
  return response
}, error => {
  if (error.response) {
    console.error(`[axios] ← ${error.response.status} ${error.config.url}`, error.response.data)
    
    // 🔥 401 = токен истёк → выходим
    if (error.response.status === 401) {
      localStorage.removeItem('auth_token')
      // Не делаем редирект здесь, чтобы не зациклить
    }
  } else if (error.request) {
    console.error('[axios] ← No response received', error.request)
  } else {
    console.error('[axios] ← Setup error', error.message)
  }
  return Promise.reject(error)
})

export default api