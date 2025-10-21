<template>
    <Nav />
    <div class="max-w-lg mx-auto mt-10 p-6 bg-white rounded shadow">
        <h2 class="text-2xl font-bold mb-4">Select Skills</h2>
        <div class="mb-4">
            <label v-for="skill in skills" :key="skill" class="block mb-2">
                <input type="checkbox" :value="skill" v-model="selectedSkills" class="mr-2" />
                {{ skill }}
            </label>
        </div>
        <button class="btn w-full" @click="saveSkills">Save & Continue</button>
    </div>
</template>
<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { userService } from '@/services/user.service'
import { useLessonStore } from '@/stores/lesson'
import Nav from '@/components/common/Nav.vue'
const skills = ref(['Algebra', 'Geometry', 'Calculus', 'Statistics'])
const selectedSkills = ref([])
const router = useRouter()
const auth = useAuthStore()
const lesson = useLessonStore()
async function saveSkills() {
    if (!selectedSkills.value.length) return
    // Normalize to lowercase before sending to backend
    const normalizedSkills = selectedSkills.value.map(s => s.toLowerCase())
    await userService.updateSkills(normalizedSkills)
    auth.user.selected_skills = normalizedSkills
    // Start the first lesson session for the selected skills
    await lesson.startLesson('initial', normalizedSkills)
    router.push('/session')
}
</script>
<style scoped>
.btn {
    @apply bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600;
}
</style>
