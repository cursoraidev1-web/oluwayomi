import { create } from 'zustand'
import { authApi } from '../api/client'

interface User {
  id: number
  email: string
  is_active: boolean
  created_at: string
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  logout: () => void
  checkAuth: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('token'),
  isAuthenticated: false,
  isLoading: true,
  
  login: async (email: string, password: string) => {
    const data = await authApi.login(email, password)
    localStorage.setItem('token', data.access_token)
    
    const user = await authApi.getMe()
    set({ 
      token: data.access_token, 
      user, 
      isAuthenticated: true,
      isLoading: false 
    })
  },
  
  register: async (email: string, password: string) => {
    await authApi.register(email, password)
    // Auto login after register
    const data = await authApi.login(email, password)
    localStorage.setItem('token', data.access_token)
    
    const user = await authApi.getMe()
    set({ 
      token: data.access_token, 
      user, 
      isAuthenticated: true,
      isLoading: false 
    })
  },
  
  logout: () => {
    localStorage.removeItem('token')
    set({ user: null, token: null, isAuthenticated: false })
  },
  
  checkAuth: async () => {
    const token = localStorage.getItem('token')
    if (!token) {
      set({ isLoading: false, isAuthenticated: false })
      return
    }
    
    try {
      const user = await authApi.getMe()
      set({ user, isAuthenticated: true, isLoading: false })
    } catch {
      localStorage.removeItem('token')
      set({ user: null, token: null, isAuthenticated: false, isLoading: false })
    }
  },
}))

// Check auth on app load
useAuthStore.getState().checkAuth()
