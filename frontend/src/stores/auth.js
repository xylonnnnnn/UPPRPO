// src/stores/auth.js
import { defineStore } from 'pinia'
import api from '@/api/axios'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('auth_token') || null,
    isLoading: false,
    error: null
  }),

  getters: {
    isAuthenticated: (state) => !!state.token
  },

  actions: {
    async login(username, password) {
      this.isLoading = true
      this.error = null
      
      try {
        // 🔥 FastAPI OAuth2PasswordRequestForm ждёт именно 'username'
        const params = new URLSearchParams()
        params.append('username', username)
        params.append('password', password)

        console.log('📤 Login request:', { username, password: '***' })

        const response = await api.post('/token', params, {
          headers: { 
            'Content-Type': 'application/x-www-form-urlencoded' 
          }
        })

        console.log('📥 Login response:', response.data)
        console.log('🔍 Has access_token?', !!response.data?.access_token)

        // 🔥 Критически важно: проверяем структуру ответа
        if (response.data && typeof response.data.access_token === 'string') {
          this.token = response.data.access_token
          localStorage.setItem('auth_token', this.token)
          
          // Опционально: можно сразу запросить данные пользователя
          // const userResp = await api.get('/users/me')
          // this.user = userResp.data
          
          return { success: true }
        } else {
          // Сервер вернул 200, но не в ожидаемом формате
          console.warn('⚠️ Unexpected response format:', response.data)
          this.error = 'Неверный формат ответа от сервера'
          return { success: false, error: this.error }
        }
        
      } catch (err) {
        console.error('❌ Login error:', err)
        
        if (err.response) {
          // Сервер ответил, но с ошибкой (401, 400, 422...)
          console.error('📦 Error response:', err.response.status, err.response.data)
          this.error = err.response.data?.detail || 'Ошибка входа'
        } else if (err.request) {
          // Запрос ушёл, но ответа нет (CORS, сеть, сервер упал)
          console.error('📡 No response received:', err.request)
          this.error = 'Нет ответа от сервера. Проверь, что бэкенд запущен.'
        } else {
          // Ошибка до отправки (настройка axios, сеть)
          console.error('⚙️ Request setup error:', err.message)
          this.error = err.message || 'Ошибка при отправке запроса'
        }
        
        return { success: false, error: this.error }
        
      } finally {
        this.isLoading = false
        console.log('🔄 isLoading set to false')
      }
    },

    async register(userData) {
      this.isLoading = true
      this.error = null
      
      try {
        await api.post('/register', userData)
        return { success: true }
      } catch (err) {
        this.error = err.response?.data?.detail || 'Ошибка регистрации'
        return { success: false, error: this.error }
      } finally {
        this.isLoading = false
      }
    },

    async verifyEmail(email, code) {
      try {
        await api.post('/verify-email', { email, code })
        return { success: true }
      } catch (err) {
        return { 
          success: false, 
          error: err.response?.data?.detail || 'Ошибка верификации' 
        }
      }
    },

    startGoogleAuth() {
      // Открываем в том же окне — бэкенд вернёт токен, который обработает GoogleCallback
      window.location.href = `${api.defaults.baseURL}/login/google`
    },

    // 🔥 Метод для завершения авторизации (вызывается из GoogleCallback)
    finishGoogleAuth(token) {
      this.token = token
      localStorage.setItem('auth_token', token)
    },

    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('auth_token')
    }
  }
})