<template>
  <div class="feed-page">
    <!-- Хедер -->
    <header class="feed-header">
      <h1 class="brand-title">OnlyFans Ruslana</h1>
      <div class="header-actions">
        <button class="btn outline" @click="showBoardModal = true">
          + Доска
        </button>
        <button class="btn primary" @click="showPinModal = true">
          + Пин
        </button>
        <button class="btn link" @click="logout">Выйти</button>
        <router-link to="/profile" class="btn outline">👤 Профиль</router-link>
      </div>
    </header>

     <!-- 🔥 Модалка создания доски -->
    <CreateBoardModal 
      v-model="showBoardModal"
      @board-created="handleBoardCreated"
    />

    <CreatePinModal 
      v-model="showPinModal"
      @pin-created="handlePinCreated"
      @create-board="showBoardModal = true"
    />

    <!-- Лента пинов (Masonry) -->
    <div class="pins-masonry">
      <PinCard 
        v-for="pin in pins" 
        :key="pin.id" 
        :pin="pin"
        @like="handleLike"
        @click="openPinDetail"
      />
    </div>

    <!-- Пагинация -->
    <div class="pagination" v-if="meta">
      <button 
        :disabled="!meta.has_prev" 
        @click="loadPage(meta.page - 1)"
      >← Назад</button>
      
      <span>Страница {{ meta.page }} из {{ meta.pages }}</span>
      
      <button 
        :disabled="!meta.has_next" 
        @click="loadPage(meta.page + 1)"
      >Вперёд →</button>
    </div>

    <!-- Лоадер -->
    <div v-if="loading" class="loader">Загрузка...</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/api/axios'
import PinCard from '@/components/PinCard.vue' // создадим ниже
import CreateBoardModal from '@/components/CreateBoardModal.vue'
import CreatePinModal from '@/components/CreatePinModal.vue'

const router = useRouter()
const authStore = useAuthStore()

const pins = ref([])
const meta = ref(null)
const loading = ref(false)
const currentPage = ref(1)

const showBoardModal = ref(false)
const showPinModal = ref(false)

// Загрузка пинов
const loadPins = async (page = 1, size = 20) => {
  loading.value = true
  pins.value = []
  try {
    const response = await api.get('/pins', {
      params: { page, size,  _t: Date.now() }
    })
    
    pins.value = response.data.items
    meta.value = response.data.meta
    currentPage.value = page
  } catch (err) {
    console.error('Ошибка загрузки пинов:', err)
  } finally {
    loading.value = false
  }
}

const loadPage = (page) => {
  if (page >= 1 && (!meta.value || page <= meta.value.pages)) {
    loadPins(page)
  }
}

const handleLike = async (pinId) => {
  try {
    const response = await api.post(`/pins/${pinId}/like`)
    // Обновляем пин в списке
    const index = pins.value.findIndex(p => p.id === pinId)
    if (index !== -1) {
      pins.value[index] = response.data
    }
  } catch (err) {
    console.error('Ошибка лайка:', err)
  }
}

const openPinDetail = (pinId) => {
  router.push(`/pin/${pinId}`)
}

const handleBoardCreated = (board) => {
  console.log('✅ Доска создана:', board)
  // Если модалка пина открыта — можно обновить список досок внутри неё
  // (реализуется через provide/inject или ref)
}

const handlePinCreated = (pin) => {
  console.log('✅ Пин создан:', pin)
  // 🔥 Автообновление ленты: перезагружаем первую страницу
  loadPins(1)
}

const logout = () => {
  authStore.logout()
  router.push('/login')
}

onMounted(() => {
  // Если не авторизован — редирект на логин
  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }
  loadPins()
})
</script>

<style scoped>
.feed-page {
  min-height: 100vh;
  background: #f0f0f0;
}

.feed-header {
  position: sticky;
  top: 0;
  background: white;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  z-index: 100;
}

.header-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 20px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn.primary {
  background: #e60023;
  color: white;
}

.btn.link {
  background: none;
  color: #555;
}

/* Masonry-сетка через CSS columns */
.pins-masonry {
  column-count: 2;
  column-gap: 1rem;
  padding: 1rem 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

@media (min-width: 768px) {
  .pins-masonry {
    column-count: 3;
  }
}

@media (min-width: 1200px) {
  .pins-masonry {
    column-count: 4;
  }
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  padding: 2rem;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loader {
  text-align: center;
  padding: 2rem;
  color: #666;
}

.brand-title {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  font-weight: 800;           /* Максимальная жирность как у логотипа */
  font-size: 1.55rem;         /* Чуть крупнее стандартного h1 */
  color: #00AFF0;             /* 🔥 Официальный цвет OnlyFans */
  letter-spacing: -0.6px;     /* Лёгкое сжатие как в оригинале */
  margin: 0;
  line-height: 1;
  user-select: none;
  padding: 0.2rem 0;
}
</style>