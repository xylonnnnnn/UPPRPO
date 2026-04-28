<template>
  <div class="auth-container">
    <form class="card" @submit.prevent="submit">
      <h2>Подтверждение email</h2>
      
      <div v-if="error" class="alert error">{{ error }}</div>
      <div v-if="success" class="alert success">✅ Email подтверждён! Перенаправляем...</div>
      
      <p class="hint">
        Введите 6-значный код из письма на <b>{{ email }}</b>
      </p>
      
      <div class="form-control">
        <input 
          v-model="code" 
          type="text" 
          placeholder="000000" 
          maxlength="6"
          pattern="\d{6}"
          :disabled="isLoading || success"
          required
          class="code-input"
        >
      </div>
      
      <button class="btn primary" type="submit" :disabled="!isValid || isLoading || success">
        {{ isLoading ? 'Проверка...' : 'Подтвердить' }}
      </button>
      
      <div class="bottom-actions">
        <button type="button" class="btn link" @click="resendCode" :disabled="isLoading">
          Отправить код ещё раз
        </button>
        <button type="button" class="btn link" @click="goToLogin">
          Назад ко входу
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const code = ref('')
const isLoading = ref(false)
const error = ref('')
const success = ref(false)

const isValid = computed(() => /^\d{6}$/.test(code.value))

onMounted(() => {
  // Получаем email из sessionStorage (установлен при регистрации)
  const pending = sessionStorage.getItem('pending_email')
  if (!pending) {
    // Если email нет — редирект на регистрацию
    router.push('/register')
  } else {
    email.value = pending
  }
})

const submit = async () => {
  if (!isValid.value) return
  
  error.value = ''
  isLoading.value = true
  
  const result = await authStore.verifyEmail(email.value, code.value)
  
  if (result.success) {
    success.value = true
    sessionStorage.removeItem('pending_email')
    // Через 1.5 сек редирект на логин
    setTimeout(() => {
      router.push('/login')
    }, 1500)
  } else {
    error.value = result.error
  }
  
  isLoading.value = false
}

const resendCode = async () => {
  // Бэкенд не имеет эндпоинта для повторной отправки,
  // поэтому просто делаем вид, что отправили (для демо)
  // В продакшене: добавить POST /resend-verification
  error.value = ''
  isLoading.value = true
  
  // Имитация запроса
  await new Promise(r => setTimeout(r, 1000))
  
  error.value = 'Код отправлен повторно (демо-режим)'
  isLoading.value = false
}

const goToLogin = () => {
  sessionStorage.removeItem('pending_email')
  router.push('/login')
}
</script>

<style scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #f0f0f0;
  padding: 1rem;
}

.card {
  background: white;
  padding: 2rem;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  width: 100%;
  max-width: 400px;
  text-align: center;
}

.hint {
  color: #666;
  margin: 1rem 0 1.5rem;
  font-size: 0.95rem;
  line-height: 1.5;
}

.form-control {
  margin: 1rem 0;
}

.code-input {
  width: 100%;
  padding: 1rem;
  border: 2px solid #ddd;
  border-radius: 8px;
  font-size: 1.5rem;
  font-weight: 600;
  text-align: center;
  letter-spacing: 0.5rem;
  box-sizing: border-box;
}

.code-input:focus {
  outline: none;
  border-color: #e60023;
}

.btn {
  width: 100%;
  padding: 0.75rem;
  border: none;
  border-radius: 24px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
  margin-top: 0.5rem;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn.primary {
  background: #e60023;
  color: white;
}

.btn.link {
  background: none;
  color: #555;
  text-decoration: underline;
  padding: 0.5rem;
  width: auto;
}

.bottom-actions {
  margin-top: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  align-items: center;
}

.alert {
  padding: 0.75rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

.alert.error {
  background: #ffebee;
  color: #c62828;
}

.alert.success {
  background: #e8f5e9;
  color: #2e7d32;
}
</style>