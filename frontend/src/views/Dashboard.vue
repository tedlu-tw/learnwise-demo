<template>
    <div class="w-full min-h-screen bg-gray-50">
        <Nav :showLogin="false" activeItem="dashboard" />
        <div class="w-full p-6">
            <div class="max-w-7xl mx-auto">
                <!-- Welcome Message -->
                <div class="mb-8">
                    <h1 class="text-2xl font-bold text-gray-800">
                        歡迎回來，{{ user?.username || '同學' }}！
                    </h1>
                    <p class="text-gray-600 mt-2">
                        {{ getGreetingMessage() }}
                    </p>
                </div>

                <div v-if="loading" class="flex justify-center items-center min-h-[200px]">
                    <div class="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                </div>
                <div v-else>
                    <!-- Stats Grid -->
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                        <!-- Total Questions Answered -->
                        <div class="bg-white rounded-lg shadow-md p-6 border border-gray-200">
                            <div class="text-sm text-gray-500 mb-2">已作答題數</div>
                            <div class="text-3xl font-bold text-gray-900 mb-2">{{ stats.total_questions }} 題</div>
                            <div class="text-sm" :class="stats.accuracy_rate >= 70 ? 'text-green-600' : 'text-orange-500'">
                                正確率 {{ stats.accuracy_rate }}%
                            </div>
                        </div>

                        <!-- Review Questions -->
                        <div class="bg-white rounded-lg shadow-md p-6 border border-gray-200">
                            <div class="text-sm text-gray-500 mb-2">待複習題數</div>
                            <div class="text-3xl font-bold text-gray-900 mb-2">{{ stats.due_count }} 題</div>
                            <div class="text-sm text-blue-600">
                                {{ stats.due_count > 0 ? '建議現在進行複習！' : '目前沒有需要複習的題目' }}
                            </div>
                        </div>

                        <!-- Learning Status -->
                        <div class="bg-white rounded-lg shadow-md p-6 border border-gray-200">
                            <div class="text-sm text-gray-500 mb-2">學習狀態</div>
                            <div class="text-3xl font-bold text-gray-900 mb-2">
                                {{ getStatusEmoji(stats.mastery_rate) }}
                            </div>
                            <div class="text-sm text-gray-600">
                                掌握度 {{ stats.mastery_rate }}%
                            </div>
                        </div>
                    </div>

                    <!-- Skills Progress Section -->
                    <div class="bg-white rounded-lg shadow-md p-6 border border-gray-200">
                        <div class="flex justify-between items-center mb-6">
                            <h3 class="text-lg font-semibold text-gray-900">技能進度</h3>
                            <button @click="refreshProgress" class="text-blue-500 hover:text-blue-700">
                                <i class="fas fa-sync-alt" :class="{ 'animate-spin': refreshing }"></i>
                            </button>
                        </div>
                        <div class="overflow-x-auto">
                            <table class="w-full">
                                <thead>
                                    <tr class="border-b border-gray-200">
                                        <th class="text-left py-3 text-sm font-medium text-gray-500">主題</th>
                                        <th class="text-right py-3 text-sm font-medium text-gray-500">已完成</th>
                                        <th class="text-right py-3 text-sm font-medium text-gray-500">總題數</th>
                                        <th class="text-right py-3 text-sm font-medium text-gray-500">進度</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr v-for="(progress, skill) in stats.skills_progress" :key="skill"
                                        class="border-b border-gray-100 hover:bg-gray-50">
                                        <td class="py-3 text-sm text-gray-900">{{ getSkillName(skill) }}</td>
                                        <td class="py-3 text-sm text-gray-600 text-right">
                                            {{ progress.answered }}
                                        </td>
                                        <td class="py-3 text-sm text-gray-600 text-right">
                                            {{ progress.total }}
                                        </td>
                                        <td class="py-3 text-sm text-right">
                                            <div class="inline-flex items-center">
                                                <div class="w-24 bg-gray-200 rounded-full h-2 mr-2">
                                                    <div class="h-2 rounded-full" 
                                                         :style="{width: `${getProgressPercentage(progress)}%`,
                                                                 backgroundColor: getProgressColor(progress)}"
                                                    ></div>
                                                </div>
                                                <span class="text-gray-600">{{ getProgressPercentage(progress) }}%</span>
                                            </div>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useLessonStore } from '@/stores/lesson'
import { useAuthStore } from '@/stores/auth'
import { lessonService } from '@/services/lesson.service'
import Nav from '@/components/common/Nav.vue'

const lesson = useLessonStore()
const auth = useAuthStore()
const user = auth.currentUser
const loading = ref(true)
const refreshing = ref(false)
const stats = ref({
    total_questions: 0,
    accuracy_rate: 0,
    due_count: 0,
    mastery_rate: 0,
    skills_progress: {}
})

const skillNames = {
    'algebra': '代數',
    'geometry': '幾何',
    'trigonometry': '三角函數',
    'calculus': '微積分',
    'statistics': '統計與機率',
    'sequence': '數列級數',
    'inequality': '不等式',
    'function': '函數',
    'polynomial': '多項式',
    'analytic_geometry': '解析幾何'
}

const getSkillName = (skill) => {
    return skillNames[skill] || skill
}

const getStatusEmoji = (masteryRate) => {
    if (masteryRate >= 80) return '🌟'
    if (masteryRate >= 60) return '😊'
    if (masteryRate >= 40) return '🤔'
    return '💪'
}

const getProgressPercentage = (progress) => {
    if (!progress.total) return 0
    return Math.round((progress.answered / progress.total) * 100)
}

const getProgressColor = (progress) => {
    const percentage = getProgressPercentage(progress)
    if (percentage >= 80) return '#10B981' // Green
    if (percentage >= 60) return '#3B82F6' // Blue
    if (percentage >= 40) return '#F59E0B' // Yellow
    return '#6B7280' // Gray
}

const refreshProgress = async () => {
    try {
        refreshing.value = true
        await loadDashboardData()
    } finally {
        refreshing.value = false
    }
}

const loadDashboardData = async () => {
    try {
        const [progressData, dueData] = await Promise.all([
            lesson.getProgressSummary(),
            lessonService.getDueCount()
        ])

        stats.value = {
            total_questions: progressData.total_questions || 0,
            accuracy_rate: progressData.accuracy_rate || 0,
            due_count: dueData.due_count || 0,
            mastery_rate: progressData.mastery_rate || 0,
            skills_progress: progressData.skills_progress || {}
        }
    } catch (error) {
        console.error('Error loading dashboard data:', error)
    } finally {
        loading.value = false
    }
}

const getGreetingMessage = () => {
    const hour = new Date().getHours()
    if (hour >= 5 && hour < 12) {
        return '早安！新的一天開始了，讓我們一起學習吧。'
    } else if (hour >= 12 && hour < 18) {
        return '午安！保持專注，繼續努力！'
    } else if (hour >= 18 && hour < 22) {
        return '晚安！複習一下今天學到的知識吧。'
    } else {
        return '夜深了，注意休息，明天繼續加油！'
    }
}

onMounted(loadDashboardData)
</script>
