import axios from './axios'

export const authService = {
  async login({ email, password }) {
    try {
      const res = await axios.post('/auth/login', { email, password })
      if (!res.data || !res.data.access_token || !res.data.user) {
        console.error('Invalid login response structure:', res.data)
        throw new Error('Invalid server response')
      }
      return res.data
    } catch (error) {
      console.error('Login error:', error.response?.data || error)
      throw error
    }
  },

  async register({ username, email, password }) {
    try {
      const res = await axios.post('/auth/register', { username, email, password })
      return res.data
    } catch (error) {
      console.error('Registration error:', error.response?.data || error)
      throw error
    }
  },

  async getCurrentUser() {
    try {
      const res = await axios.get('/auth/me')
      return res.data
    } catch (error) {
      console.error('Get current user error:', error.response?.data || error)
      throw error
    }
  }
}
