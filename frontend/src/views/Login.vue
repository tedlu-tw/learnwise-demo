<template>
    <Nav />
    <div class="w-full h-screen flex flex-col justify-center items-center">
        <div class="w-full flex flex-col justify-center items-center">
            <!-- title & description -->
            <span class="text-2xl font-bold">登入你的帳號</span>
            <span class="text-lg font-normal mt-2">輸入你的電子郵件和密碼</span>
            <!-- input form-->
            <input v-model="email" type="text"
                class="w-96 bg-white border border-[#E0E0E0] rounded-lg px-4 py-2 text-left mt-5" placeholder="Email" />
            <input v-model="password" type="password" autocomplete="current-password"
                class="w-96 bg-white border border-[#E0E0E0] rounded-lg px-4 py-2 text-left mt-4"
                placeholder="Password" />
            <button class="w-96 bg-black text-white rounded-lg px-4 py-2 mt-4" v-on:click="login">登入</button>
            <!-- register notice -->
            <span class="text-sm text-[#828282] mt-5">還沒有帳號嗎？<a href="#" class="text-black">註冊</a></span>
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
    @apply border rounded px-3 py-2;
}

.btn {
    @apply bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600;
}
</style>
