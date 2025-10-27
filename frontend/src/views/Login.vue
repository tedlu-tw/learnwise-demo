<template>
    <Nav :showLogin="true" activeItem="auth" />
    <div class="w-full h-screen flex flex-col justify-center items-center">
        <div class="w-full flex flex-col justify-center items-center">
            <!-- title & description -->
            <span class="text-2xl font-bold">登入你的帳號</span>
            <span class="text-lg font-normal mt-2">輸入你的電子郵件和密碼</span>
            <!-- input form -->
            <form @submit.prevent="login" class="w-full flex flex-col items-center">
                <input v-model="email" type="text"
                    class="w-96 bg-white border border-[#E0E0E0] rounded-lg px-4 py-2 text-left mt-5" placeholder="Email" required/>
                <input v-model="password" type="password" autocomplete="current-password"
                    class="w-96 bg-white border border-[#E0E0E0] rounded-lg px-4 py-2 text-left mt-4"
                    placeholder="Password" required/>
                <!-- error message shown when login fails -->
                <p v-if="error" class="text-red-600 mt-2">{{ error || '帳號或密碼錯誤' }}</p>
                <button type="submit" class="w-96 bg-black text-white rounded-lg px-4 py-2 mt-4">登入</button>
            </form>
            <!-- register notice -->
            <span class="text-sm text-[#828282] mt-5">
                還沒有帳號嗎？
                <router-link to="/register" class="text-black hover:underline">註冊</router-link>
            </span>
        </div>
    </div>
</template>
<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Nav from '@/components/common/Nav.vue'
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
    if (auth.user) {
        // Fallback: user is set but isLoggedIn is false, try to redirect anyway
        console.warn('auth.user is set but isLoggedIn is false, forcing redirect')
        if (auth.user.selected_skills && auth.user.selected_skills.length) {
            console.log('Fallback: Redirecting to /dashboard')
            router.push('/dashboard')
        } else {
            console.log('Fallback: Redirecting to /skills')
            router.push('/skills')
        }
    }
}
</script>
<style scoped>
.input {
    border: 1px solid #e5e7eb;
    border-radius: 0.375rem;
    padding: 0.75rem 1rem;
}

.btn {
    background-color: #3b82f6;
    color: white;
    padding: 0.75rem 1rem;
    border-radius: 0.375rem;
}

.btn:hover {
    background-color: #2563eb;
}
</style>
