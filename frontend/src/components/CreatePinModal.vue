<template>
  <Teleport to="body">
    <div v-if="modelValue" class="modal-overlay" @click.self="closeModal">
      <div class="modal-card">
        <!-- Хедер -->
        <div class="modal-header">
          <h3>Создать новый пин</h3>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>

        <form @submit.prevent="submit" class="modal-form">
          
          <!-- 🔥 Загрузка изображения (Drag & Drop) -->
          <div class="form-group">
            <label>Изображение *</label>
            
            <!-- Превью или зона загрузки -->
            <div 
              v-if="imagePreview" 
              class="image-preview"
              @click="triggerFileInput"
            >
              <img :src="imagePreview" alt="Preview">
              <button type="button" class="remove-btn" @click.stop="removeImage">
                ✕
              </button>
              <div class="preview-overlay">Нажмите, чтобы заменить</div>
            </div>
            
            <div 
              v-else 
              class="drop-zone" 
              @dragover.prevent="isDragging = true"
              @dragleave.prevent="isDragging = false"
              @drop.prevent="handleDrop"
              @click="triggerFileInput"
              :class="{ 'drag-over': isDragging }"
            >
              <div class="drop-icon">📷</div>
              <p>Перетащите изображение сюда</p>
              <p class="drop-hint">или нажмите для выбора файла</p>
              <p class="drop-limit">PNG, JPG до 10 МБ • или оставьте пустым</p>
            </div>
            
            <input 
              type="file" 
              ref="fileInput" 
              accept="image/*" 
              @change="handleFileSelect"
              class="hidden-input"
            >
            
            <!-- Прогресс загрузки -->
            <div v-if="uploading" class="upload-progress">
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
              </div>
              <span>Загрузка: {{ uploadProgress }}%</span>
            </div>
          </div>

          <!-- Заголовок -->
          <div class="form-group">
            <label for="pin-title">Заголовок *</label>
            <input
              id="pin-title"
              v-model="form.title"
              type="text"
              placeholder="О чём этот пин?"
              :disabled="isLoading"
              maxlength="200"
              required
            >
            <small>{{ form.title.length }}/200</small>
          </div>

          <!-- Описание -->
          <div class="form-group">
            <label for="pin-desc">Описание</label>
            <textarea
              id="pin-desc"
              v-model="form.description"
              placeholder="Добавьте описание..."
              :disabled="isLoading"
              rows="3"
              maxlength="500"
            ></textarea>
            <small>{{ form.description?.length || 0 }}/500</small>
          </div>

          <!-- Ссылка -->
          <div class="form-group">
            <label for="pin-link">Ссылка (необязательно)</label>
            <input
              id="pin-link"
              v-model="form.link_url"
              type="url"
              placeholder="https://example.com"
              :disabled="isLoading"
            >
          </div>

          <!-- Выбор доски -->
          <div class="form-group">
            <label for="pin-board">Сохранить в доску *</label>
            <select
              id="pin-board"
              v-model="form.board_id"
              :disabled="isLoading || boardsLoading"
              required
            >
              <option value="" disabled>
                {{ boardsLoading ? 'Загрузка досок...' : 'Выберите доску' }}
              </option>
              <option v-for="board in boards" :key="board.id" :value="board.id">
                {{ board.name }} {{ board.is_private ? '🔒' : '' }}
              </option>
            </select>
            <button 
              type="button" 
              class="btn-link" 
              @click="emit('create-board')"
              :disabled="isLoading"
            >
              + Создать новую доску
            </button>
          </div>

          <!-- Ошибки -->
          <div v-if="error" class="alert error">{{ error }}</div>

          <!-- Кнопки -->
          <div class="modal-actions">
            <button 
              type="button" 
              class="btn secondary" 
              @click="closeModal"
              :disabled="isLoading || uploading"
            >
              Отмена
            </button>
            <button 
              type="submit" 
              class="btn primary" 
              :disabled="!isValid || isLoading || uploading"
            >
              {{ isLoading ? 'Создаём...' : 'Сохранить пин' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
// 🔥 Импорты для ESLint + Vue
import { ref, computed, onMounted, defineProps, defineEmits } from 'vue'
import { boardsApi, pinsApi, uploadApi } from '@/api/endpoints'

// 🔥 НЕ присваиваем в переменную, если не используем в скрипте
defineProps({
  modelValue: Boolean
})

const emit = defineEmits(['update:modelValue', 'pin-created', 'create-board'])

// Состояние формы
const form = ref({
  title: '',
  description: '',
  link_url: '',
  board_id: null
})

const imageFile = ref(null)
const imagePreview = ref(null)
const isDragging = ref(false)
const fileInput = ref(null)

// Загрузка досок
const boards = ref([])
const boardsLoading = ref(false)

// Загрузка изображения
const uploading = ref(false)
const uploadProgress = ref(0)

// Общее состояние
const isLoading = ref(false)
const error = ref('')

// Валидация
const isValid = computed(() => 
  form.value.title.trim().length >= 1 && 
  form.value.board_id !== null
)

// Загрузка списка досок при открытии
onMounted(async () => {
  await loadBoards()
})

const loadBoards = async () => {
  boardsLoading.value = true
  try {
    const response = await boardsApi.getAll()
    boards.value = response.data
    if (boards.value.length > 0 && !form.value.board_id) {
      form.value.board_id = boards.value[0].id
    }
  } catch (err) {
    console.error('Failed to load boards:', err)
    error.value = 'Не удалось загрузить список досок'
  } finally {
    boardsLoading.value = false
  }
}

// 🔥 Обработчики для Drag & Drop
const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleFileSelect = (event) => {
  const file = event.target.files?.[0]
  if (file) validateAndSetFile(file)
}

const handleDrop = (event) => {
  isDragging.value = false
  const file = event.dataTransfer?.files?.[0]
  if (file) validateAndSetFile(file)
}

const validateAndSetFile = (file) => {
  if (!file.type.startsWith('image/')) {
    error.value = 'Пожалуйста, выберите изображение'
    return
  }
  
  if (file.size > 10 * 1024 * 1024) {
    error.value = 'Файл слишком большой (макс. 10 МБ)'
    return
  }
  
  error.value = ''
  imageFile.value = file
  
  const reader = new FileReader()
  reader.onload = (e) => {
    imagePreview.value = e.target?.result
  }
  reader.readAsDataURL(file)
}

const removeImage = () => {
  imageFile.value = null
  imagePreview.value = null
  if (fileInput.value) fileInput.value.value = ''
}

// Загрузка изображения на сервер
const uploadImage = async (file) => {
  uploading.value = true
  uploadProgress.value = 0
  
  try {
    const progressInterval = setInterval(() => {
      uploadProgress.value = Math.min(90, uploadProgress.value + 10)
    }, 200)
    
    const response = await uploadApi.image(file)
    
    clearInterval(progressInterval)
    uploadProgress.value = 100
    
    return response.data.image_url
    
  } catch (err) {
    console.error('Upload error:', err)
    throw new Error(err.response?.data?.detail || 'Ошибка загрузки изображения')
  } finally {
    await new Promise(resolve => setTimeout(resolve, 300))
    uploading.value = false
    uploadProgress.value = 0
  }
}

// 🔥 Основная функция создания пина
const submit = async () => {
  if (!isValid.value) return
  
  error.value = ''
  isLoading.value = true
  
  try {
    let image_url = null
    
    // 🔥 Загружаем изображение ТОЛЬКО если пользователь его выбрал
    if (imageFile.value) {
      image_url = await uploadImage(imageFile.value)
    } else {
      // 🔥 Placeholder для пинов без изображения
      // Можно отправить null, или ссылку на заглушку
    //   image_url = 'https://via.placeholder.com/400x600?text=No+Image'
      // Или: image_url = null (если бэкенд принимает)
      image_url = null
    }
    console.log(form.value.board_id)
    const pinData = {
      title: form.value.title.trim(),
      description: form.value.description?.trim() || null,
      link_url: form.value.link_url?.trim() || null,
      image_url: image_url,  // может быть null или заглушка
      board_id: Number(form.value.board_id)
    }
    
    const response = await pinsApi.create(pinData)
    
    emit('pin-created', response.data)
    closeModal()
    
  } catch (err) {
    console.error('Create pin error:', err)
    error.value = err.message || 'Ошибка создания пина'
  } finally {
    isLoading.value = false
  }
}

const closeModal = () => {
  form.value = { title: '', description: '', link_url: '', board_id: null }
  imageFile.value = null
  imagePreview.value = null
  error.value = ''
  if (fileInput.value) fileInput.value.value = ''
  
  emit('update:modelValue', false)
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
  overflow-y: auto;
}

.modal-card {
  background: white;
  border-radius: 16px;
  width: 100%;
  max-width: 520px;
  max-height: 95vh;
  overflow-y: auto;
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.25);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #eee;
  position: sticky;
  top: 0;
  background: white;
  z-index: 1;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.75rem;
  color: #999;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  line-height: 1;
  transition: color 0.2s;
}

.close-btn:hover {
  color: #333;
}

.modal-form {
  padding: 1.5rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  font-weight: 600;
  color: #333;
  margin-bottom: 0.5rem;
  font-size: 0.95rem;
}

.form-group input[type="text"],
.form-group input[type="url"],
.form-group textarea,
.form-group select {
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
.form-group textarea:focus,
.form-group select:focus {
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

.btn-link {
  background: none;
  border: none;
  color: #e60023;
  font-size: 0.9rem;
  cursor: pointer;
  padding: 0;
  margin-top: 0.5rem;
  text-decoration: none;
}

.btn-link:hover {
  text-decoration: underline;
}

.btn-link:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 🔥 Drop Zone */
.drop-zone {
  border: 3px dashed #ddd;
  border-radius: 12px;
  padding: 2rem 1rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  background: #fafafa;
}

.drop-zone:hover,
.drop-zone.drag-over {
  border-color: #e60023;
  background: #fff5f5;
}

.drop-icon {
  font-size: 3rem;
  margin-bottom: 0.5rem;
}

.drop-zone p {
  margin: 0.25rem 0;
  color: #666;
}

.drop-hint {
  font-size: 0.9rem;
  color: #999;
}

.drop-limit {
  font-size: 0.8rem;
  color: #bbb;
  margin-top: 0.75rem;
}

.hidden-input {
  display: none;
}

/* 🔥 Image Preview */
.image-preview {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  max-height: 300px;
}

.image-preview img {
  width: 100%;
  height: auto;
  display: block;
  object-fit: contain;
  background: #f5f5f5;
}

.image-preview .remove-btn {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  background: rgba(230, 0, 35, 0.9);
  color: white;
  border: none;
  border-radius: 50%;
  width: 28px;
  height: 28px;
  font-size: 1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.image-preview .remove-btn:hover {
  background: #c4001d;
}

.preview-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 0.5rem;
  font-size: 0.85rem;
  text-align: center;
  opacity: 0;
  transition: opacity 0.2s;
}

.image-preview:hover .preview-overlay {
  opacity: 1;
}

/* 🔥 Progress Bar */
.upload-progress {
  margin-top: 0.75rem;
}

.progress-bar {
  height: 6px;
  background: #eee;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 0.25rem;
}

.progress-fill {
  height: 100%;
  background: #e60023;
  transition: width 0.2s;
  border-radius: 3px;
}

.upload-progress span {
  font-size: 0.85rem;
  color: #666;
}

/* 🔥 Alerts */
.alert {
  padding: 0.75rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

.alert.error {
  background: #ffebee;
  color: #c62828;
  border-left: 4px solid #c62828;
}

/* 🔥 Actions */
.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid #eee;
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

/* 🔥 Responsive */
@media (max-width: 600px) {
  .modal-card {
    max-height: 100vh;
    border-radius: 16px 16px 0 0;
  }
  
  .modal-actions {
    flex-direction: column-reverse;
  }
  
  .btn {
    width: 100%;
  }
}
</style>
