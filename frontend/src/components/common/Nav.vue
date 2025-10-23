<template>
  <nav class="relative w-full bg-white border-gray-200 shadow-md">
    <div class="max-w-screen-xl flex flex-wrap items-center justify-between mx-auto p-4 px-10 ">
      <span class="self-center text-2xl font-semibold whitespace-nowrap">LearnWise</span>
      <ul class="flex space-x-10">
        <li :class="navClass('dashboard')">
          <a href="/dashboard" class="block py-2 px-2 text-gray-900 font-medium text-lg">儀表板</a>
        </li>
        <li :class="navClass('session')">
          <a href="/session" class="block py-2 px-2 text-gray-900 font-medium text-lg">課程</a>
        </li>
        <!-- Show 登入 or 登出 depending on prop or auth state -->
        <li :class="navClass('auth')">
          <div v-if="shouldShowLogin">
            <a href="/login" class="block py-2 px-2 text-gray-900 font-medium text-lg">登入</a>
          </div>
          <div v-else>
            <button @click="handleLogout" class="block py-2 px-3 text-gray-900 font-medium text-lg">登出</button>
          </div>
        </li>
      </ul>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  // When provided, this boolean decides whether to show the login button (true)
  // or the logout button (false). When omitted, Nav will use the auth store
  // to show Login if the user is not logged in, Logout otherwise.
  showLogin: { type: Boolean, required: false },
  // Optional active item: 'dashboard' | 'session' | 'auth'
  activeItem: { type: String, required: false }
})

const auth = useAuthStore()
const router = useRouter()

const shouldShowLogin = computed(() => {
  if (typeof props.showLogin === 'boolean') return props.showLogin
  return !auth.isLoggedIn
})

// Determine current active item: prop overrides route detection
const currentActive = computed(() => {
  if (props.activeItem) return props.activeItem
})

function navClass(name) {
  if (currentActive.value === name) return `border-b-4 border-[#FFCC00]`
  return ''
}

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>