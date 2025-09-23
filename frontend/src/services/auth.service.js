import axios from 'axios'
export const authService = {
  async login({ email, password }) {
    const res = await axios.post('/api/auth/login', { email, password })
    return res.data
  },
  async register({ username, email, password }) {
    const res = await axios.post('/api/auth/register', { username, email, password })
    return res.data
  }
}
