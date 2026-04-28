<template>
  <Teleport to="body">
    <div v-if="modelValue" class="modal-overlay" @click.self="emit('update:modelValue', false)">
      <div class="modal-card">
        <!-- Хедер модалки -->
        <div class="modal-header">
          <h3>Создать новую доску</h3>
          <button class="close-btn" @click="emit('update:modelValue', false)">&times;</button>
        </div>

        <!-- Форма -->
        <form @submit.prevent="submit" class="modal-form">
          <div class="form-group">
            <label for="board-name">Название доски *</label>
            <input
              id="board-name"
              v-model="form.name"
              type="text"
              placeholder="Например: Вдохновение, Рецепты..."
              :disabled="isLoading"
              maxlength="100"
              required
            >
            <small>{{ form.name.length }}/100</small>
          </div>

          <div class="form-group">
            <label for="board-desc">Описание (необязательно)</label>
            <textarea
              id="board-desc"
              v-model="form.description"
              placeholder="О чём эта доска?"
              :disabled="isLoading"
              rows="3"
              maxlength="500"
            ></textarea>
            <small>{{ form.description?.length || 0 }}/500</small>
          </div>

          <div class="form-group checkbox">
            <label>
              <input
                type="checkbox"
                v-model="form.is_private"
                :disabled="isLoading"
              >
              <span>Скрытая доска (видна только вам)</span>
            </label>
          </div>

          <!-- Ошибки -->
          <div v-if="error" class="alert error">{{ error }}</div>

          <!-- Кнопки -->
          <div class="modal-actions">
            <button 
              type="button" 
              class="btn secondary" 
              @click="emit('update:modelValue', false)"
              :disabled="isLoading"
            >
              Отмена
            </button>
            <button 
              type="submit" 
              class="btn primary" 
              :disabled="!isValid || isLoading"
            >
              {{ isLoading ? 'Создаём...' : 'Создать доску' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
// 🔥 Импортируем для ESLint (игнорируй предупреждение Vue о "не нужно импортировать")
import { ref, computed } from 'vue'
import { defineProps, defineEmits } from 'vue'  // ← добавили импорт
import { boardsApi } from '@/api/endpoints'

// 🔥 Не присваиваем в переменную, если не используем в скрипте
defineProps({
  modelValue: Boolean  // v-model support
})

const emit = defineEmits(['update:modelValue', 'board-created'])

const form = ref({
  name: '',
  description: '',
  is_private: false
})

const isLoading = ref(false)
const error = ref('')

const isValid = computed(() => form.value.name.trim().length >= 1)

const submit = async () => {
  if (!isValid.value) return
  
  error.value = ''
  isLoading.value = true
  
  const payload = {
    name: form.value.name.trim(),
    description: form.value.description?.trim() || null,
    is_private: form.value.is_private
  }
  
  try {
    const response = await boardsApi.create(payload)
    
    emit('board-created', response.data)
    emit('update:modelValue', false)
    form.value = { name: '', description: '', is_private: false }
    
  } catch (err) {
    error.value = err.response?.data?.detail || 'Ошибка создания доски'
    console.error('Create board error:', err)
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-card {
  background: white;
  border-radius: 16px;
  width: 100%;
  max-width: 480px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #999;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  line-height: 1;
}

.close-btn:hover {
  color: #333;
}

.modal-form {
  padding: 1.5rem;
}

.form-group {
  margin-bottom: 1.25rem;
}

.form-group label {
  display: block;
  font-weight: 600;
  color: #333;
  margin-bottom: 0.5rem;
  font-size: 0.95rem;
}

.form-group input[type="text"],
.form-group textarea {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
  font-family: inherit;
  box-sizing: border-box;
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #e60023;
}

.form-group small {
  display: block;
  color: #999;
  font-size: 0.8rem;
  margin-top: 0.25rem;
  text-align: right;
}

.form-group.checkbox {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.form-group.checkbox label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0;
  font-weight: normal;
  cursor: pointer;
}

.form-group.checkbox input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
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

.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 1.5rem;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 24px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s, background 0.2s;
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

.btn.secondary {
  background: #f0f0f0;
  color: #333;
}

.btn.secondary:hover:not(:disabled) {
  background: #e0e0e0;
}
</style>