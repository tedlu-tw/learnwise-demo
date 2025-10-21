import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'
import './index.css'

async function initApp() {
  const app = createApp(App)
  app.use(createPinia())
  
  // Initialize auth state from stored token before mounting
  const auth = useAuthStore()
  await auth.initializeAuth()
  
  app.use(router)
  app.mount('#app')
}

initApp().catch(console.error)
