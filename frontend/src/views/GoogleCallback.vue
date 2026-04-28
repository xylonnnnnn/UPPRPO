<template>
  <div class="callback-container">
    <div class="spinner"></div>
    <p>{{ message }}</p>
    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'  // 🔥 useRoute убрали — не нужен
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const message = ref('Обработка авторизации Google...')
const error = ref('')

onMounted(async () => {
  try {
    // 🎯 Способ 1: Токен в хеше URL (#access_token=...)
    const hash = window.location.hash
    if (hash && hash.includes('access_token')) {
      const params = new URLSearchParams(hash.substring(1))
      const token = params.get('access_token')
      if (token) {
        authStore.finishGoogleAuth(token)
        message.value = '✅ Успешно! Перенаправляем...'
        setTimeout(() => router.push('/'), 1000)
        return
      }
    }
    
    // 🎯 Способ 2: Парсим ответ, если он в тексте страницы (для разработки)
    const bodyText = document.body.innerText?.trim()
    if (bodyText && bodyText.startsWith('{')) {
      try {
        const data = JSON.parse(bodyText)
        if (data.access_token) {
          authStore.finishGoogleAuth(data.access_token)
          message.value = '✅ Успешно! Перенаправляем...'
          document.body.innerHTML = ''
          setTimeout(() => router.push('/'), 1000)
          return
        }
      } catch (parseErr) {
        // 🔥 Пустой catch заменили на комментарий для ESLint
        // Игнорируем ошибки парсинга, пробуем следующий способ
        console.debug('JSON parse failed, trying next method')
      }
    }
    
    // 🎯 Способ 3: Fetch к тому же URL (если CORS разрешает)
    const response = await fetch(window.location.href, {
      method: 'GET',
      credentials: 'include'
    })
    
    if (response.ok) {
      const data = await response.json()
      if (data.access_token) {
        authStore.finishGoogleAuth(data.access_token)
        message.value = '✅ Успешно! Перенаправляем...'
        setTimeout(() => router.push('/'), 1000)
        return
      }
    }
    
    // Если ничего не сработало
    error.value = 'Не удалось получить токен. Попробуйте войти ещё раз.'
    setTimeout(() => router.push('/login'), 3000)
    
  } catch (e) {
    console.error('Google callback error:', e)
    error.value = 'Ошибка обработки авторизации'
    setTimeout(() => router.push('/login'), 3000)
  }
})
</script>

<style scoped>
.callback-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: #f0f0f0;
  text-align: center;
  padding: 2rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #e60023;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error {
  color: #c62828;
  margin-top: 1rem;
}
</style>