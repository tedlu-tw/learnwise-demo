import { defineStore } from 'pinia'
import { authService } from '@/services/auth.service'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: null,
    error: null
  }),
  getters: {
    currentUser: (state) => state.user,
    isLoggedIn: (state) => {
      // Check both state and localStorage
      return (!!state.token && !!state.user) || !!localStorage.getItem('token')
    }
  },
  actions: {
    async login(credentials) {
      try {
        const data = await authService.login(credentials)
        this.token = data.access_token
        this.user = {
          ...data.user,
          selected_skills: data.user.selected_skills || []
        }
        this.error = null
        // Store both token and user data in localStorage
        localStorage.setItem('token', data.access_token)
        localStorage.setItem('user', JSON.stringify(this.user))
      } catch (e) {
        this.error = e.response?.data?.error || 'Login failed'
        this.user = null
        this.token = null
        localStorage.removeItem('token')
        localStorage.removeItem('user')
      }
    },
    async register(credentials) {
      try {
        console.log('Starting registration process for:', credentials.email)
        const data = await authService.register(credentials)
        
        // Registration and auto-login successful
        this.token = data.access_token
        this.user = {
          ...data.user,
          selected_skills: data.user.selected_skills || []
        }
        this.error = null
        
        // Store both token and user data in localStorage
        localStorage.setItem('token', data.access_token)
        localStorage.setItem('user', JSON.stringify(this.user))
        
        console.log('Registration and auto-login successful for:', credentials.email)
      } catch (e) {
        console.error('Registration error:', e)
        
        // Clear any partial state
        this.user = null
        this.token = null
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        
        // Set a user-friendly error message
        if (e.message.includes('already registered')) {
          this.error = '此電子郵件已經註冊過了'
        } else if (e.message.includes('validation')) {
          this.error = '請檢查輸入的資料是否正確'
        } else {
          this.error = '註冊失敗：' + (e.message || '請稍後再試')
        }
        
        throw new Error(this.error)
      }
    },
    async initializeAuth() {
      const token = localStorage.getItem('token')
      const userData = localStorage.getItem('user')
      
      if (token && userData) {
        try {
          this.token = token
          this.user = JSON.parse(userData)
          console.log('Auth initialized from localStorage:', this.user)
          
          // Optionally verify token is still valid with backend
          // If this fails, it will be handled by axios interceptor
          await authService.getCurrentUser()
        } catch (e) {
          console.error('Token verification failed:', e)
          // Token is invalid, clear everything
          this.logout()
        }
      }
    },
    logout() {
      this.user = null
      this.token = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  }
})
