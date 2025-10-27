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
      // First register the user
      const registerRes = await axios.post('/auth/register', { username, email, password })
      console.log('Registration response:', registerRes.data)
      
      if (!registerRes.data.message?.includes('successfully')) {
        throw new Error('Registration failed: Invalid response')
      }
      
      // If registration successful, automatically log in
      const loginRes = await axios.post('/auth/login', { email, password })
      console.log('Auto-login response:', loginRes.data)
      
      if (!loginRes.data || !loginRes.data.access_token || !loginRes.data.user) {
        throw new Error('Auto-login failed after registration')
      }
      
      return loginRes.data
    } catch (error) {
      console.error('Registration/Login error:', error.response?.data || error)
      // Include more detail in the error message
      const errorMessage = error.response?.data?.error || error.response?.data?.message || error.message
      throw new Error(errorMessage || 'Registration failed')
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
