import axios from 'axios'

const baseURL = import.meta.env.VITE_API_URL ? `${import.meta.env.VITE_API_URL.replace(/\/$/, '')}/api` : '/api'
console.log('API baseURL:', baseURL)

const api = axios.create({
  baseURL,
})

// Add a request interceptor to include JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Add a response interceptor to handle token expiration
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Only auto-redirect on 401 for non-auth initialization calls
    if (error.response?.status === 401 && 
        !error.config?.url?.includes('/auth/me') && 
        window.location.pathname !== '/login') {
      // Token expired during normal API calls, redirect to login
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
