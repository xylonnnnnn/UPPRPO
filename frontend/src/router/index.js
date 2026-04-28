// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginPage.vue'),
    meta: { guestOnly: true }
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/RegisterPage.vue'),
    meta: { guestOnly: true }
  },
  {
    path: '/verify',
    name: 'verify',
    component: () => import('@/views/VerifyPage.vue'),
    meta: { guestOnly: true }
  },
  {
    path: '/auth/google/callback',
    name: 'google-callback',
    component: () => import('@/views/GoogleCallback.vue')
  },
  {
    path: '/',
    name: 'feed',
    component: () => import('@/views/FeedPage.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/pin/:id',
    name: 'pin-detail',
    component: () => import('@/views/PinDetailPage.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('@/views/ProfilePage.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

// 🔥 Глобальный гард с отладкой
router.beforeEach((to) => {
  const auth = useAuthStore()
  
  console.log('🔍 Router guard:', {
    path: to.path,
    requiresAuth: to.meta.requiresAuth,
    guestOnly: to.meta.guestOnly,
    isAuthenticated: auth.isAuthenticated
  })
  
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    console.log('🔒 Redirecting to /login')
    return '/login'
  }
  
  if (to.meta.guestOnly && auth.isAuthenticated) {
    console.log('🔓 Redirecting to /')
    return '/'
  }
  
  console.log('✅ Navigation allowed')
})

export default router