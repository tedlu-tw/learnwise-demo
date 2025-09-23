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
    isLoggedIn: (state) => !!state.token
  },
  actions: {
    async login(credentials) {
      try {
        const data = await authService.login(credentials)
        this.token = data.access_token
        this.user = data.user
        this.error = null
        // Store token in localStorage for router guard
        localStorage.setItem('token', data.access_token)
      } catch (e) {
        this.error = e.response?.data?.error || 'Login failed'
        this.user = null
        this.token = null
        localStorage.removeItem('token')
      }
    },
    logout() {
      this.user = null
      this.token = null
      localStorage.removeItem('token')
    }
  }
})
