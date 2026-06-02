<template>
  <div class="pin-detail-page">
    <!-- Хедер с навигацией -->
    <header class="detail-header">
      <button class="btn-back" @click="$router.back()">← Назад</button>
      <h1>Пин</h1>
      <div class="header-actions">
        <button 
          v-if="isOwner" 
          class="btn danger" 
          @click="deletePin"
          :disabled="isLoading"
        >
          🗑️ Удалить
        </button>
      </div>
    </header>

    <!-- Лоадер -->
    <div v-if="loading" class="loader">Загрузка...</div>

    <!-- Ошибка -->
    <div v-else-if="error" class="error-box">
      <p>❌ {{ error }}</p>
      <button class="btn primary" @click="loadPin">Попробовать ещё раз</button>
    </div>

    <!-- Контент пина -->
    <div v-else-if="pin" class="pin-content">
      
      <!-- Изображение -->
      <div class="pin-image-wrapper">
        <img 
          v-if="resolvedImageUrl" 
          :src="resolvedImageUrl" 
          :alt="pin.title"
          @error="onImageError"
        >
        <div v-else class="image-placeholder">
          <span>📷</span>
          <p>Нет изображения</p>
        </div>
      </div>

      <!-- Информация -->
      <div class="pin-info">
        <h2>{{ pin.title }}</h2>
        
        <p v-if="pin.description" class="description">{{ pin.description }}</p>
        
        <!-- Ссылка -->
        <a 
          v-if="pin.link_url" 
          :href="pin.link_url" 
          target="_blank" 
          rel="noopener noreferrer"
          class="link-url"
        >
          🔗 {{ truncateUrl(pin.link_url) }}
        </a>

        <!-- Автор и дата -->
        <div class="meta">
          <div class="author">
            <img v-if="authorAvatar" class="avatar-img" :src="authorAvatar" :alt="pin.author.username">
            <span v-else class="avatar">{{ pin.author.username[0].toUpperCase() }}</span>
            <span>{{ pin.author.username }}</span>
          </div>
          <span class="date">{{ formatDate(pin.created_at) }}</span>
        </div>

        <!-- Лайки -->
        <div class="actions">
          <button class="btn like-btn" @click="toggleLike" :disabled="liking">
            {{ pin.is_liked ? '❤️' : '🤍' }} {{ pin.likes_count }}
          </button>
        </div>
      </div>

      <!-- Комментарии -->
      <section class="comments-section">
        <h3>Комментарии ({{ comments.length }})</h3>
        
        <!-- Форма добавления -->
        <form @submit.prevent="addComment" class="comment-form">
          <textarea
            v-model="newComment"
            placeholder="Напишите комментарий..."
            :disabled="commentLoading"
            rows="3"
            maxlength="500"
            required
          ></textarea>
          <div class="comment-form-actions">
            <small>{{ newComment.length }}/500</small>
            <button 
              type="submit" 
              class="btn primary" 
              :disabled="!newComment.trim() || commentLoading"
            >
              {{ commentLoading ? 'Отправка...' : 'Отправить' }}
            </button>
          </div>
        </form>

        <!-- Список комментариев -->
        <div class="comments-list">
          <div 
            v-for="comment in comments" 
            :key="comment.id" 
            class="comment-item"
          >
            <div class="comment-header">
              <img v-if="commentAvatar(comment)" class="avatar-img small" :src="commentAvatar(comment)" :alt="comment.user.username">
              <span v-else class="avatar small">{{ comment.user.username[0].toUpperCase() }}</span>
              <span class="username">{{ comment.user.username }}</span>
              <span class="date">{{ formatDate(comment.created_at) }}</span>
              
              <!-- Кнопка удаления (если комментарий мой) -->
              <button 
                v-if="comment.user.id === currentUserId" 
                class="btn-delete-comment"
                @click="deleteComment(comment.id)"
                title="Удалить комментарий"
              >
                ✕
              </button>
            </div>
            <p class="comment-text">{{ comment.comment }}</p>
          </div>
          
          <p v-if="comments.length === 0" class="no-comments">
            Пока нет комментариев. Будьте первым! 💬
          </p>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
// 🔥 Импорты для ESLint
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { pinsApi, profileApi } from '@/api/endpoints'
import { resolveImageUrl } from '@/utils/image'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const pin = ref(null)
const comments = ref([])
const loading = ref(true)
const error = ref('')
const isLoading = ref(false)

// Комментарии
const newComment = ref('')
const commentLoading = ref(false)

// Лайки
const liking = ref(false)

// ID текущего пользователя (для проверки прав)
const currentUserId = computed(() => {
  return authStore.user?.id || null
})

// Проверка: принадлежит ли пин текущему пользователю
const isOwner = computed(() => {
  return pin.value?.author?.id === currentUserId.value
})

const resolvedImageUrl = computed(() => resolveImageUrl(pin.value?.image_url))
const authorAvatar = computed(() => resolveImageUrl(pin.value?.author?.img_url || pin.value?.author?.image_url))
const commentAvatar = (comment) => resolveImageUrl(comment?.user?.img_url || comment?.user?.image_url)

// Загрузка пина
const loadPin = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const pinId = route.params.id
    const response = await pinsApi.getById(pinId)
    
    pin.value = response.data
    comments.value = response.data.comments || []
    
  } catch (err) {
    console.error('Failed to load pin:', err)
    error.value = err.response?.data?.detail || 'Не удалось загрузить пин'
    
    // Если 404 — редирект на главную через 2 сек
    if (err.response?.status === 404) {
      setTimeout(() => router.push('/'), 2000)
    }
  } finally {
    loading.value = false
  }
}

const loadCurrentUser = async () => {
  if (authStore.user?.id) return

  const response = await profileApi.getMe()
  authStore.user = response.data
  localStorage.setItem('user_info', JSON.stringify(response.data))
}

// 🔥 Обработчики
const onImageError = (e) => {
  e.target.style.display = 'none'
  e.target.parentElement.classList.add('no-image')
}

const truncateUrl = (url, max = 40) => {
  if (url.length <= max) return url
  return url.slice(0, max) + '...'
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  })
}

// 🔥 Лайк/дизлайк
const toggleLike = async () => {
  if (!pin.value || liking.value) return
  
  liking.value = true
  try {
    const response = await pinsApi.like(pin.value.id)
    // Обновляем локальное состояние
    pin.value.is_liked = response.data.is_liked
    pin.value.likes_count = response.data.likes_count
  } catch (err) {
    console.error('Like error:', err)
    error.value = 'Не удалось изменить лайк'
  } finally {
    liking.value = false
  }
}

// 🔥 Добавление комментария
const addComment = async () => {
  if (!newComment.value.trim() || !pin.value) return
  
  commentLoading.value = true
  try {
    const response = await pinsApi.addComment(pin.value.id, newComment.value.trim())
    
    // Добавляем новый комментарий в начало списка
    comments.value.unshift({
      id: response.data.id || Date.now(), // временный ID если бэкенд не вернул
      comment: newComment.value.trim(),
      created_at: new Date().toISOString(),
      user: {
        id: currentUserId.value,
        username: authStore.user?.username || 'Вы'
      }
    })
    
    // Сброс формы
    newComment.value = ''
    
    // Обновляем данные пина (если бэкенд вернул обновлённый объект)
    if (response.data.comments) {
      comments.value = response.data.comments
    }
    
  } catch (err) {
    console.error('Add comment error:', err)
    error.value = err.response?.data?.detail || 'Не удалось добавить комментарий'
  } finally {
    commentLoading.value = false
  }
}

// 🔥 Удаление комментария
const deleteComment = async (commentId) => {
  if (!confirm('Удалить этот комментарий?')) return
  
  try {
    await pinsApi.deleteComment(commentId)
    // Удаляем из локального списка
    comments.value = comments.value.filter(c => c.id !== commentId)
  } catch (err) {
    console.error('Delete comment error:', err)
    error.value = 'Не удалось удалить комментарий'
  }
}

// 🔥 Удаление пина
const deletePin = async () => {
  if (!confirm('Удалить этот пин? Это действие нельзя отменить.')) return
  
  isLoading.value = true
  try {
    await pinsApi.delete(pin.value.id)
    // Редирект на главную после успешного удаления
    router.push('/')
  } catch (err) {
    console.error('Delete pin error:', err)
    error.value = err.response?.data?.detail || 'Не удалось удалить пин'
  } finally {
    isLoading.value = false
  }
}

// Загружаем при монтировании
onMounted(() => {
  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }
  loadCurrentUser()
    .then(loadPin)
    .catch((err) => {
      console.error('Failed to load current user:', err)
      error.value = err.response?.data?.detail || 'Не удалось загрузить текущего пользователя'
      loading.value = false
    })
})
</script>

<style scoped>
.pin-detail-page {
  min-height: 100vh;
  background: var(--bg);
  color: var(--text);
}

/* 🔹 Хедер */
.detail-header {
  position: sticky;
  top: 0;
  background: color-mix(in srgb, var(--surface) 88%, transparent);
  backdrop-filter: blur(18px);
  padding: 1rem 2rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  border-bottom: 1px solid var(--border);
  z-index: 100;
}

.detail-header h1 {
  margin: 0;
  font-size: 1.25rem;
  flex: 1;
}

.btn-back {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  padding: 0.5rem;
  color: var(--text);
}

.btn-back:hover {
  color: var(--primary);
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

/* 🔹 Контент */
.pin-content {
  display: grid;
  grid-template-columns: 1fr;
  gap: 2rem;
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

@media (min-width: 900px) {
  .pin-content {
    grid-template-columns: 1fr 400px;
    align-items: start;
  }
}

/* 🔹 Изображение */
.pin-image-wrapper {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: var(--shadow-soft);
}

.pin-image-wrapper img {
  width: 100%;
  height: auto;
  display: block;
}

.image-placeholder,
.pin-image-wrapper.no-image {
  min-height: 400px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--surface-soft);
  color: var(--text-muted);
}

.image-placeholder span {
  font-size: 4rem;
  margin-bottom: 1rem;
}

/* 🔹 Информация */
.pin-info {
  background: var(--surface);
  border: 1px solid var(--border);
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: var(--shadow-soft);
}

.pin-info h2 {
  margin: 0 0 1rem 0;
  font-size: 1.5rem;
  color: var(--text);
}

.description {
  color: var(--text-muted);
  line-height: 1.6;
  margin: 0 0 1rem 0;
  
  /* 🔥 Перенос длинных строк */
  white-space: pre-wrap;      /* Сохраняет переносы строк + переносит длинные слова */
  word-wrap: break-word;      /* Устаревшее, но для совместимости */
  overflow-wrap: break-word;  /* Современный стандарт: разбивает длинные слова */
  hyphens: auto;              /* Авто-перенос по слогам (опционально, красиво) */
  
  /* 🔥 Защита от "вылезания" за пределы контейнера */
  max-width: 100%;
  display: block;
}

.link-url {
  display: inline-block;
  color: var(--primary);
  text-decoration: none;
  margin: 0 0 1rem 0;
  font-size: 0.95rem;
}

.link-url:hover {
  text-decoration: underline;
}

.meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 0;
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  margin: 1rem 0;
  font-size: 0.9rem;
  color: var(--text-muted);
}

.author {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
  color: var(--text);
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.9rem;
}

.avatar.small {
  width: 24px;
  height: 24px;
  font-size: 0.75rem;
}

.avatar-img {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid var(--border);
}

.avatar-img.small {
  width: 24px;
  height: 24px;
}

.actions {
  display: flex;
  gap: 0.5rem;
}

.like-btn {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  background: var(--surface-soft);
  color: var(--text);
}

.like-btn:hover:not(:disabled) {
  background: var(--primary-soft);
}

/* 🔹 Комментарии */
.comments-section {
  background: var(--surface);
  border: 1px solid var(--border);
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: var(--shadow-soft);
  align-self: start;
  position: sticky;
  top: 100px;
}

.comments-section h3 {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
  color: var(--text);
}

.comment-form {
  margin-bottom: 1.5rem;
}

.comment-form textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  font-size: 1rem;
  font-family: inherit;
  resize: vertical;
  min-height: 80px;
  box-sizing: border-box;
  color: var(--text);
  background: var(--surface-raised);
}

.comment-form textarea:focus {
  outline: none;
  border-color: var(--primary);
}

.comment-form-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 0.5rem;
}

.comment-form-actions small {
  color: var(--text-muted);
  font-size: 0.8rem;
}

.comments-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-height: 400px;
  overflow-y: auto;
  padding-right: 0.5rem;
}

.comment-item {
  padding: 0.75rem;
  background: var(--surface-soft);
  border-radius: var(--radius);
}

.comment-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.username {
  font-weight: 600;
  color: var(--text);
}

.date {
  color: var(--text-muted);
  font-size: 0.85rem;
}

.btn-delete-comment {
  margin-left: auto;
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 1rem;
  padding: 0.25rem;
}

.btn-delete-comment:hover {
  color: var(--primary);
}

.comment-text {
  margin: 0;
  color: var(--text);
  line-height: 1.5;
  white-space: pre-wrap;
}

.no-comments {
  text-align: center;
  color: var(--text-muted);
  padding: 1rem;
  font-style: italic;
}

/* 🔹 Общие стили */
.loader,
.error-box {
  text-align: center;
  padding: 3rem;
  color: var(--text-muted);
}

.error-box {
  color: var(--danger);
  background: color-mix(in srgb, var(--danger) 14%, var(--surface));
  border-radius: var(--radius);
  margin: 2rem;
}

.btn {
  padding: 0.5rem 1rem;
  border: 1px solid var(--border);
  border-radius: 20px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s, background 0.2s;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn.primary {
  background: var(--primary);
  border-color: var(--primary);
  color: white;
}

.btn.danger {
  background: var(--danger);
  border-color: var(--danger);
  color: white;
}

/* 🔹 Скроллбар для комментариев */
.comments-list::-webkit-scrollbar {
  width: 6px;
}
.comments-list::-webkit-scrollbar-track {
  background: var(--surface-soft);
  border-radius: 3px;
}
.comments-list::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 3px;
}
.comments-list::-webkit-scrollbar-thumb:hover {
  background: var(--text-muted);
}
</style>
  color: var(--text);
  background: var(--surface-raised);
