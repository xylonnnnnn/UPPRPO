<template>
  <div class="profile-page">
    <div class="profile-card" v-if="!loading">
      <!-- 🔹 Аватар (заглушка) -->
      <div class="avatar-section">
        <div class="avatar-placeholder">
          <span>{{ username.charAt(0).toUpperCase() }}</span>
        </div>
        <p class="avatar-hint">📷 Аватар (скоро)</p>
      </div>

      <!-- 🔹 Имя пользователя -->
      <div class="form-section">
        <label>Имя пользователя</label>
        <div v-if="!isEditingName" class="display-row">
          <span class="value">{{ username }}</span>
          <button @click="startEditName" class="btn-edit">Изменить</button>
        </div>
        <div v-else class="edit-row">
          <input 
            v-model.trim="editUsername" 
            type="text" 
            maxlength="50"
            :disabled="savingName"
            placeholder="Введите новое имя"
          >
          <div class="edit-actions">
            <button @click="cancelEditName" :disabled="savingName">Отмена</button>
            <button 
              @click="saveName" 
              :disabled="!isValidUsername || savingName"
              class="btn-save"
            >
              {{ savingName ? 'Сохраняем...' : 'Сохранить' }}
            </button>
          </div>
          <p v-if="nameError" class="error-msg">{{ nameError }}</p>
        </div>
      </div>

      <!-- 🔹 Описание -->
      <div class="form-section">
        <label>О себе</label>
        <div v-if="!isEditingDesc" class="display-row">
          <span class="value desc-text">{{ description || 'Добавьте описание...' }}</span>
          <button @click="startEditDesc" class="btn-edit">Изменить</button>
        </div>
        <div v-else class="edit-row">
          <textarea 
            v-model="editDescription" 
            rows="3" 
            maxlength="300"
            :disabled="savingDesc"
            placeholder="Расскажите о себе..."
          ></textarea>
          <div class="edit-actions">
            <small>{{ editDescription.length }}/300</small>
            <button @click="cancelEditDesc" :disabled="savingDesc">Отмена</button>
            <button @click="saveDescription" :disabled="savingDesc" class="btn-save">
              {{ savingDesc ? 'Сохраняем...' : 'Сохранить' }}
            </button>
          </div>
        </div>
      </div>

      <!-- 🔹 Уведомление об успехе -->
      <div v-if="successMsg" class="success-banner">{{ successMsg }}</div>

      <!-- 🔹 Навигация -->
      <button @click="$router.push('/')" class="btn-back">← На главную</button>
    </div>

    <div v-else class="loader">Загрузка профиля...</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { profileApi } from '@/api/endpoints'

const authStore = useAuthStore()

// Состояние
const username = ref('')
const description = ref('')
const editUsername = ref('')
const editDescription = ref('')

const isEditingName = ref(false)
const isEditingDesc = ref(false)
const savingName = ref(false)
const savingDesc = ref(false)
const nameError = ref('')
const successMsg = ref('')
const loading = ref(true)

const isValidUsername = computed(() => editUsername.value.length >= 3)

// Инициализация
onMounted(async () => {
  try {
    const res = await profileApi.getMe()
    username.value = res.data.username
    description.value = res.data.description || ''
    editUsername.value = username.value
    editDescription.value = description.value
    authStore.user = res.data
    localStorage.setItem('user_info', JSON.stringify(res.data))
  } catch (err) {
    console.warn('Failed to load profile, using defaults')
  } finally {
    loading.value = false
  }
})

// 🔹 Логика имени
const startEditName = () => {
  editUsername.value = username.value
  isEditingName.value = true
  nameError.value = ''
  successMsg.value = ''
}

const cancelEditName = () => {
  editUsername.value = username.value
  isEditingName.value = false
  nameError.value = ''
}

const saveName = async () => {
  savingName.value = true
  nameError.value = ''
  
  try {
    const response = await profileApi.rename(editUsername.value)
    username.value = response.data.username
    editUsername.value = response.data.username
    
    // Обновляем глобальный стейт (если используется в хедере)
    authStore.user = response.data
    localStorage.setItem('user_info', JSON.stringify(response.data))
    
    isEditingName.value = false
    showSuccess('Имя успешно изменено!')
  } catch (err) {
    nameError.value = err.response?.data?.detail || 'Ошибка при смене имени'
  } finally {
    savingName.value = false
  }
}

// 🔹 Логика описания
const startEditDesc = () => {
  editDescription.value = description.value
  isEditingDesc.value = true
  successMsg.value = ''
}

const cancelEditDesc = () => {
  editDescription.value = description.value
  isEditingDesc.value = false
}

const saveDescription = async () => {
  savingDesc.value = true
  
  try {
    const response = await profileApi.updateDescription(editDescription.value)
    description.value = response.data.description
    editDescription.value = response.data.description
    
    authStore.user = response.data
    localStorage.setItem('user_info', JSON.stringify(response.data))
    
    isEditingDesc.value = false
    showSuccess('Описание обновлено!')
  } catch (err) {
    nameError.value = err.response?.data?.detail || 'Ошибка при обновлении описания'
  } finally {
    savingDesc.value = false
  }
}

// 🔹 Утилиты
const showSuccess = (msg) => {
  successMsg.value = msg
  setTimeout(() => { successMsg.value = '' }, 3000)
}
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  background: #f0f0f0;
  display: flex;
  justify-content: center;
  padding: 2rem 1rem;
}

.profile-card {
  background: white;
  width: 100%;
  max-width: 600px;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
}

/* 🔹 Аватар */
.avatar-section {
  text-align: center;
  margin-bottom: 2rem;
}

.avatar-placeholder {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: #e60023;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.5rem;
  font-weight: 700;
  margin: 0 auto 0.5rem;
}

.avatar-hint {
  color: #999;
  font-size: 0.85rem;
  margin: 0;
}

/* 🔹 Секции формы */
.form-section {
  margin-bottom: 1.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #eee;
}

.form-section:last-of-type {
  border-bottom: none;
}

.form-section label {
  display: block;
  font-weight: 600;
  color: #333;
  margin-bottom: 0.5rem;
}

.display-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.value {
  font-size: 1.1rem;
  color: #222;
}

.desc-text {
  color: #666;
  white-space: pre-wrap;
  overflow-wrap: break-word;
  max-width: 80%;
}

.btn-edit {
  background: none;
  border: 1px solid #ddd;
  border-radius: 20px;
  padding: 0.4rem 1rem;
  color: #555;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-edit:hover {
  border-color: #e60023;
  color: #e60023;
}

/* 🔹 Режим редактирования */
.edit-row {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.edit-row input,
.edit-row textarea {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
  font-family: inherit;
  box-sizing: border-box;
}

.edit-row input:focus,
.edit-row textarea:focus {
  outline: none;
  border-color: #e60023;
}

.edit-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
}

.edit-actions button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 20px;
  font-weight: 600;
  cursor: pointer;
}

.edit-actions button:first-child {
  background: #f0f0f0;
  color: #333;
}

.btn-save {
  background: #e60023;
  color: white;
}

.btn-save:hover:not(:disabled) {
  background: #c4001d;
}

.btn-save:disabled,
.edit-actions button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.edit-actions small {
  color: #999;
  font-size: 0.8rem;
}

.error-msg {
  color: #c62828;
  background: #ffebee;
  padding: 0.5rem;
  border-radius: 6px;
  font-size: 0.9rem;
  margin: 0;
}

/* 🔹 Успех и навигация */
.success-banner {
  background: #e8f5e9;
  color: #2e7d32;
  padding: 0.75rem;
  border-radius: 8px;
  text-align: center;
  margin: 1rem 0;
  font-weight: 500;
}

.btn-back {
  display: block;
  width: 100%;
  padding: 0.75rem;
  margin-top: 1rem;
  background: white;
  border: 2px solid #ddd;
  border-radius: 20px;
  font-size: 1rem;
  font-weight: 600;
  color: #555;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-back:hover {
  border-color: #bbb;
  background: #f9f9f9;
}

.loader {
  text-align: center;
  padding: 3rem;
  color: #666;
  font-size: 1.1rem;
}
</style>