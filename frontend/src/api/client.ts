import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api

// Auth API
export const authApi = {
  login: async (email: string, password: string) => {
    const formData = new URLSearchParams()
    formData.append('username', email)
    formData.append('password', password)
    
    const response = await api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
    return response.data
  },
  
  register: async (email: string, password: string) => {
    const response = await api.post('/auth/register', { email, password })
    return response.data
  },
  
  getMe: async () => {
    const response = await api.get('/auth/me')
    return response.data
  },
}

// Videos API
export const videosApi = {
  list: async () => {
    const response = await api.get('/videos/')
    return response.data
  },
  
  get: async (id: number) => {
    const response = await api.get(`/videos/${id}`)
    return response.data
  },
  
  upload: async (file: File, onProgress?: (progress: number) => void) => {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await api.post('/videos/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (e.total && onProgress) {
          onProgress(Math.round((e.loaded * 100) / e.total))
        }
      }
    })
    return response.data
  },
  
  process: async (id: number, options: {
    min_clip_duration?: number
    max_clip_duration?: number
    max_clips?: number
    title?: string
    description?: string
    tags?: string[]
  }) => {
    const response = await api.post(`/videos/${id}/process`, options)
    return response.data
  },
  
  getClips: async (id: number) => {
    const response = await api.get(`/videos/${id}/clips`)
    return response.data
  },
  
  delete: async (id: number) => {
    const response = await api.delete(`/videos/${id}`)
    return response.data
  },
}

// Clips API
export const clipsApi = {
  list: async () => {
    const response = await api.get('/clips/')
    return response.data
  },
  
  get: async (id: number) => {
    const response = await api.get(`/clips/${id}`)
    return response.data
  },
  
  update: async (id: number, data: {
    caption?: string
    hashtags?: string[]
    status?: string
  }) => {
    const response = await api.patch(`/clips/${id}`, data)
    return response.data
  },
  
  regenerateContent: async (id: number, options: {
    title?: string
    description?: string
    tags?: string[]
    platform?: string
  }) => {
    const response = await api.post(`/clips/${id}/regenerate-content`, options)
    return response.data
  },
  
  delete: async (id: number) => {
    const response = await api.delete(`/clips/${id}`)
    return response.data
  },
  
  preview: async (id: number) => {
    const response = await api.get(`/clips/${id}/preview`)
    return response.data
  },
}

// Social API
export const socialApi = {
  getAccounts: async () => {
    const response = await api.get('/social/accounts')
    return response.data
  },
  
  connectTwitter: async () => {
    const response = await api.get('/social/connect/twitter')
    return response.data
  },
  
  connectYouTube: async () => {
    const response = await api.get('/social/connect/youtube')
    return response.data
  },
  
  connectTikTok: async () => {
    const response = await api.get('/social/connect/tiktok')
    return response.data
  },
  
  disconnect: async (accountId: number) => {
    const response = await api.delete(`/social/accounts/${accountId}`)
    return response.data
  },
  
  post: async (data: {
    clip_id: number
    platforms: string[]
    caption?: string
    hashtags?: string[]
    scheduled_at?: string
  }) => {
    const response = await api.post('/social/post', data)
    return response.data
  },
  
  getPosts: async () => {
    const response = await api.get('/social/posts')
    return response.data
  },
}
