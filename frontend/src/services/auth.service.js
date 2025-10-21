import axios from './axios'
export const authService = {
  async login({ email, password }) {
    const res = await axios.post('/auth/login', { email, password })
    return res.data
  },
  async register({ username, email, password }) {
    const res = await axios.post('/auth/register', { username, email, password })
    return res.data
  },
  async getCurrentUser() {
    const res = await axios.get('/auth/me')
    return res.data
  }
}
