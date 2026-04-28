const API_URL = (process.env.VUE_APP_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')

export const resolveImageUrl = (url) => {
  if (!url || typeof url !== 'string') return ''
  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:')) {
    return url
  }
  if (url.startsWith('/')) {
    return `${API_URL}${url}`
  }
  return `${API_URL}/${url}`
}

export const isRenderableImageUrl = (url) => {
  return resolveImageUrl(url) !== ''
}
