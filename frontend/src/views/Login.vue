<template>
  <div class="max-w-md mx-auto mt-20 p-6 bg-white rounded shadow">
    <h2 class="text-2xl font-bold mb-4">Login</h2>
    <form @submit.prevent="login">
      <input v-model="email" type="email" placeholder="Email" class="input mb-2 w-full" required />
      <input v-model="password" type="password" placeholder="Password" class="input mb-2 w-full" required />
      <button class="btn w-full" type="submit">Login</button>
      <div v-if="error" class="text-red-500 mt-2">{{ error }}</div>
    </form>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
const email = ref('')
const password = ref('')
const auth = useAuthStore()
const error = ref(null)
const router = useRouter()
async function login() {
  await auth.login({ email: email.value, password: password.value })
  error.value = auth.error
  console.log('auth.user:', auth.user)
  console.log('auth.isLoggedIn:', auth.isLoggedIn)
  if (auth.isLoggedIn) {
    // If user has selected skills, go to session, else go to skills selection
    if (auth.user?.selected_skills?.length) {
      console.log('Redirecting to /session')
      router.push('/session')
    } else {
      console.log('Redirecting to /skills')
      router.push('/skills')
    }
  } else if (auth.user) {
    // Fallback: user is set but isLoggedIn is false, try to redirect anyway
    console.warn('auth.user is set but isLoggedIn is false, forcing redirect')
    if (auth.user.selected_skills && auth.user.selected_skills.length) {
      console.log('Fallback: Redirecting to /session')
      router.push('/session')
    } else {
      console.log('Fallback: Redirecting to /skills')
      router.push('/skills')
    }
  }
}
</script>
<style scoped>
.input { @apply border rounded px-3 py-2; }
.btn { @apply bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600; }
</style>
