<template>
  <div class="auth-container">
    <form class="card" @submit.prevent="submit">
      <h2>Вход в Pinterest Clone</h2>
      
      <!-- Отображение ошибки -->
      <div v-if="error" class="alert error">{{ error }}</div>
      
      <!-- Поле логина (username, не email!) -->
      <div class="form-control">
        <input
          v-model="username"
          type="text"
          placeholder="Логин или email"
          :disabled="authStore.isLoading"
          required
          autocomplete="username"
        >
      </div>

      <!-- Поле пароля -->
      <div class="form-control">
        <input
          v-model="password"
          type="password"
          placeholder="Пароль"
          :disabled="authStore.isLoading"
          required
          autocomplete="current-password"
        >
      </div>

      <!-- Кнопка входа -->
      <button 
        class="btn primary" 
        type="submit" 
        :disabled="!isValid || authStore.isLoading"
      >
        {{ authStore.isLoading ? 'Входим...' : 'Войти' }}
      </button>

      <!-- Дополнительные действия -->
      <div class="bottom-actions">
        <button 
          type="button" 
          class="btn link" 
          @click="goToRegister"
          :disabled="authStore.isLoading"
        >
          Зарегистрироваться
        </button>
        <!-- Google Auth можно добавить позже -->
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// Инициализация
const router = useRouter()
const authStore = useAuthStore()

// Реактивные данные (обязательно ref!)
const username = ref('')      // ← переименовали с email на username
const password = ref('')
const error = ref('')         // ← обязательно ref, иначе шаблон не обновится

// Вычисляемое свойство: валидация формы
const isValid = computed(() => 
  username.value.trim().length >= 1 && password.value.length >= 6
)

// Обработка отправки формы
const submit = async () => {
  error.value = ''  // очищаем предыдущую ошибку
  
  // Вызываем action из Pinia store
  const result = await authStore.login(username.value, password.value)
  
  if (result.success) {
    // Успех → редирект на главную
    router.push('/')
  } else {
    // Ошибка → показываем текст
    error.value = result.error
  }
}

// Переход на страницу регистрации
const goToRegister = () => {
  router.push('/register')
}
</script>

<style scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #f0f0f0;
}

.card {
  background: white;
  padding: 2rem;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  width: 100%;
  max-width: 400px;
}

.form-control {
  margin: 1rem 0;
}

.form-control input {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s;
  box-sizing: border-box; /* важно для padding */
}

.form-control input:focus {
  outline: none;
  border-color: #e60023; /* Pinterest red */
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

.btn.primary:hover:not(:disabled) {
  background: #c4001d;
}

.btn.link {
  background: none;
  color: #555;
  text-decoration: underline;
  padding: 0.5rem;
}

.btn.link:hover:not(:disabled) {
  color: #e60023;
}

.bottom-actions {
  margin-top: 1rem;
  text-align: center;
}

.alert.error {
  background: #ffebee;
  color: #c62828;
  padding: 0.75rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-size: 0.9rem;
  text-align: left;
}
</style>