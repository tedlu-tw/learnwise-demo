<template>
    <Nav :showLogin="false" activeItem="auth" />
    <div class="w-full h-screen flex flex-col justify-center items-center">
        <div class="w-full flex flex-col justify-center items-center">
            <!-- title & description -->
            <span class="text-2xl font-bold">建立新帳號</span>
            <span class="text-lg font-normal mt-2">輸入以下資料以註冊帳號</span>
            
            <!-- registration form -->
            <form @submit.prevent="register" class="w-full flex flex-col items-center">
                <div class="w-96 space-y-4 mt-5">
                    <div>
                        <label for="username" class="block text-sm font-medium text-gray-700 mb-1">使用者名稱</label>
                        <input v-model="username" type="text" id="username" name="username"
                            class="w-full bg-white border border-[#E0E0E0] rounded-lg px-4 py-2 text-left"
                            placeholder="請輸入使用者名稱" required 
                            :class="{'border-red-500': validationErrors.username}"
                        />
                        <p v-if="validationErrors.username" class="mt-1 text-sm text-red-600">
                            {{ validationErrors.username }}
                        </p>
                    </div>

                    <div>
                        <label for="email" class="block text-sm font-medium text-gray-700 mb-1">電子郵件</label>
                        <input v-model="email" type="email" id="email" name="email"
                            class="w-full bg-white border border-[#E0E0E0] rounded-lg px-4 py-2 text-left"
                            placeholder="請輸入電子郵件" required
                            :class="{'border-red-500': validationErrors.email}"
                        />
                        <p v-if="validationErrors.email" class="mt-1 text-sm text-red-600">
                            {{ validationErrors.email }}
                        </p>
                    </div>

                    <div>
                        <label for="password" class="block text-sm font-medium text-gray-700 mb-1">密碼</label>
                        <input v-model="password" type="password" id="password" name="password"
                            class="w-full bg-white border border-[#E0E0E0] rounded-lg px-4 py-2 text-left"
                            placeholder="請輸入密碼" required
                            :class="{'border-red-500': validationErrors.password}"
                            autocomplete="new-password"
                        />
                        <p v-if="validationErrors.password" class="mt-1 text-sm text-red-600">
                            {{ validationErrors.password }}
                        </p>
                    </div>

                    <div>
                        <label for="confirmPassword" class="block text-sm font-medium text-gray-700 mb-1">確認密碼</label>
                        <input v-model="confirmPassword" type="password" id="confirmPassword" name="confirmPassword"
                            class="w-full bg-white border border-[#E0E0E0] rounded-lg px-4 py-2 text-left"
                            placeholder="請再次輸入密碼" required
                            :class="{'border-red-500': validationErrors.confirmPassword}"
                            autocomplete="new-password"
                        />
                        <p v-if="validationErrors.confirmPassword" class="mt-1 text-sm text-red-600">
                            {{ validationErrors.confirmPassword }}
                        </p>
                    </div>
                </div>

                <!-- Error message -->
                <p v-if="error" class="text-red-600 mt-4">{{ error }}</p>

                <!-- Submit button -->
                <button type="submit" 
                    class="w-96 bg-black text-white rounded-lg px-4 py-2 mt-6 disabled:opacity-50 disabled:cursor-not-allowed"
                    :disabled="isSubmitting">
                    <span v-if="isSubmitting" class="flex items-center justify-center">
                        <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        註冊中...
                    </span>
                    <span v-else>建立帳號</span>
                </button>
            </form>

            <!-- Login link -->
            <span class="text-sm text-[#828282] mt-5">
                已經有帳號了？
                <router-link to="/login" class="text-black hover:underline">登入</router-link>
            </span>
        </div>
    </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Nav from '@/components/common/Nav.vue'

const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const error = ref(null)
const isSubmitting = ref(false)
const validationErrors = ref({})

const validateForm = () => {
    const errors = {}
    
    // Username validation
    if (username.value.length < 3) {
        errors.username = '使用者名稱至少需要 3 個字元'
    }
    
    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(email.value)) {
        errors.email = '請輸入有效的電子郵件地址'
    }
    
    // Password validation
    if (password.value.length < 6) {
        errors.password = '密碼至少需要 6 個字元'
    }
    
    // Confirm password validation
    if (password.value !== confirmPassword.value) {
        errors.confirmPassword = '確認密碼與密碼不符'
    }
    
    validationErrors.value = errors
    return Object.keys(errors).length === 0
}

const register = async () => {
    error.value = null
    
    if (!validateForm()) {
        return
    }
    
    isSubmitting.value = true
    
    try {
        await auth.register({
            username: username.value,
            email: email.value,
            password: password.value
        })
        
        // Registration successful, redirect to skill selection
        router.push('/skill-selection')
    } catch (e) {
        // Display the error from the auth store if available
        error.value = e.message || auth.error || '註冊失敗，請稍後再試'
        
        // Clear the password fields on error
        password.value = ''
        confirmPassword.value = ''
    } finally {
        isSubmitting.value = false
    }
}
</script>
