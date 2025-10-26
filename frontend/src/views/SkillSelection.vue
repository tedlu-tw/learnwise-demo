<template>
    <Nav :showLogin="false" activeItem="session" />
    <div class="max-w-4xl mx-auto mt-10 p-6 bg-white rounded shadow">
        <h2 class="text-2xl font-bold mb-4">選擇學習領域</h2>
        <div class="mb-6">
            <p class="text-gray-600 mb-4">請選擇您想要學習的數學領域（可複選）：</p>
            <div class="mb-4">
                <input type="text" 
                       v-model="searchQuery"
                       placeholder="搜尋領域..."
                       class="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-500"
                />
            </div>
            <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                <button v-for="skill in filteredSkills" 
                        :key="skill"
                        @click="toggleSkill(skill)"
                        class="p-3 text-left rounded-lg border transition-all duration-200 flex items-center gap-2"
                        :class="[
                            selectedSkills.includes(skill) 
                                ? 'bg-blue-50 border-blue-500 text-blue-700' 
                                : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50'
                        ]">
                    <span class="flex-shrink-0">
                        <svg v-if="selectedSkills.includes(skill)" 
                             xmlns="http://www.w3.org/2000/svg" 
                             class="h-5 w-5 text-blue-500" 
                             viewBox="0 0 20 20" 
                             fill="currentColor">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                        </svg>
                        <svg v-else 
                             xmlns="http://www.w3.org/2000/svg" 
                             class="h-5 w-5 text-gray-400" 
                             viewBox="0 0 20 20" 
                             fill="currentColor">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm0-2a6 6 0 100-12 6 6 0 000 12z" clip-rule="evenodd" />
                        </svg>
                    </span>
                    <span class="text-sm">{{ skill }}</span>
                </button>
            </div>
        </div>
        <div class="flex flex-col gap-4">
            <p v-if="saveError" class="text-red-500 text-sm">{{ saveError }}</p>
            <div class="flex items-center gap-4">
                <span class="text-sm text-gray-500">已選擇 {{ selectedSkills.length }} 個領域</span>
                <button class="btn flex-grow" 
                        :disabled="!selectedSkills.length"
                        @click="saveSkills">
                    開始學習
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { userService } from '@/services/user.service'
import { useLessonStore } from '@/stores/lesson'
import Nav from '@/components/common/Nav.vue'

const loading = ref(true)
const saveError = ref('')
const skills = ref([])
const selectedSkills = ref([])
const searchQuery = ref('')
const router = useRouter()
const auth = useAuthStore()
const lesson = useLessonStore()

// Fetch categories from backend
onMounted(async () => {
    try {
        skills.value = await userService.getCategories()
        // If user has previously selected skills, load them
        if (auth.user?.selected_skills?.length) {
            selectedSkills.value = auth.user.selected_skills
        }
    } catch (error) {
        console.error('Failed to fetch categories:', error)
    } finally {
        loading.value = false
    }
})

// Filter skills based on search query
const filteredSkills = computed(() => {
    if (!searchQuery.value) return skills.value
    const query = searchQuery.value.toLowerCase()
    return skills.value.filter(skill => 
        skill.toLowerCase().includes(query)
    )
})

// Handle skill selection
function toggleSkill(skill) {
    const index = selectedSkills.value.indexOf(skill)
    if (index === -1) {
        selectedSkills.value.push(skill)
    } else {
        selectedSkills.value.splice(index, 1)
    }
}

async function saveSkills() {
    if (!selectedSkills.value.length) return
    try {
        saveError.value = ''
        // First update user skills
        const updatedUser = await userService.updateSkills(selectedSkills.value)
        
        // Update both auth store and localStorage
        auth.user = {
            ...auth.user,
            selected_skills: selectedSkills.value
        }
        localStorage.setItem('user', JSON.stringify(auth.user))
        console.log('Updated user skills:', auth.user.selected_skills)
        
        try {
            // Then try to start the lesson
            await lesson.startLesson('initial', selectedSkills.value)
            router.push('/session')
        } catch (error) {
            console.error('Failed to start lesson:', error)
            // Even if starting lesson fails, skills were saved
            router.push('/dashboard')
        }
    } catch (error) {
        console.error('Failed to save skills:', error)
        saveError.value = '保存失敗，請稍後再試'
    }
}
</script>
<style scoped>
.btn {
    background-color: #3b82f6;
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 0.375rem;
    transition: background-color 0.2s;
}

.btn:hover:not(:disabled) {
    background-color: #2563eb;
}

.btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}
</style>
