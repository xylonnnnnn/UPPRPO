// src/api/endpoints.js
import api from './axios'

export const boardsApi = {
  getAll: () => api.get('/boards'),
  create: (boardData) => api.post('/create/board', boardData),
  delete: (boardId) => api.delete(`/delete/board/${boardId}`)  // ✅ Только для досок
}

// 🔹 Пины
export const pinsApi = {
  getAll: (page = 1, size = 20) => 
    api.get('/pins', { params: { page, size } }),
  
  getById: (pinId) => api.get(`/pins/${pinId}`),  // ✅ Перенесли сюда
  
  create: (pinData) => api.post('/create/pins/', pinData),
  
  like: (pinId) => api.post(`/pins/${pinId}/like`),
  
  addComment: (pinId, comment) => 
    api.post(`/pins/${pinId}/add_comment`, comment, {
      headers: { 'Content-Type': 'application/json' }
    }),
  
  delete: (pinId) => api.delete(`/delete/pin/${pinId}`),  // ✅ Только для пинов
  
  deleteComment: (commentId) => api.delete(`/delete/comment/${commentId}`)
}

export const profileApi = {
  getMe: () => api.get('/user/me'),
  // 🔥 FastAPI Body(str) ожидает JSON-строку, поэтому используем JSON.stringify
  rename: (newName) => api.patch('/user/rename', JSON.stringify(newName), {
    headers: { 'Content-Type': 'application/json' }
  }),
  updateDescription: (newDesc) => api.patch('/user/change_description', JSON.stringify(newDesc), {
    headers: { 'Content-Type': 'application/json' }
  })
  // GET /user/me добавим позже, пока используем данные из authStore
}

export const uploadApi = {
  image: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/upload/image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }
}

export const authApi = {
  login: (username, password) => {
    const params = new URLSearchParams()
    params.append('username', username)
    params.append('password', password)
    return api.post('/token', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
  },
  register: (userData) => api.post('/register', userData),
  verifyEmail: (email, code) => api.post('/verify-email', { email, code })
}