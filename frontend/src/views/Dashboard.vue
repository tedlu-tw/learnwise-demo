<template>
    <div class="w-full h-screen">
        <Nav :showLogin="false" activeItem="dashboard" />
        <div class="w-full bg-gray-50 p-6">
            <div class="max-w-7xl mx-auto">
                <!-- Top Row Stats -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                    <!-- Total Questions Card -->
                    <div class="bg-white rounded-lg shadow-md p-6 border border-gray-200">
                        <div class="text-sm text-gray-500 mb-2">總題數</div>
                        <div class="text-3xl font-bold text-gray-900 mb-2">{{ progress.total_questions }} 題</div>
                        <div class="text-sm text-green-600">比昨天還要多了 5 題！</div>
                    </div>

                    <!-- Study Streak Card -->
                    <div class="bg-white rounded-lg shadow-md p-6 border border-gray-200">
                        <div class="text-sm text-gray-500 mb-2">連續答題次數</div>
                        <div class="text-3xl font-bold text-gray-900 mb-2">{{ dueCount }} 題</div>
                        <div class="text-sm text-gray-600">最高次數為 10 題</div>
                    </div>
                </div>

                <!-- Skills Progress Section -->
                <div class="bg-white rounded-lg shadow-md p-6 border border-gray-200">
                    <h3 class="text-lg font-semibold text-gray-900 mb-6">技能樹</h3>
                    <div class="overflow-x-auto">
                        <table class="w-full">
                            <thead>
                                <tr class="border-b border-gray-200">
                                    <th class="text-left py-3 text-sm font-medium text-gray-500">主題</th>
                                    <th class="text-right py-3 text-sm font-medium text-gray-500">已完成題數</th>
                                    <th class="text-right py-3 text-sm font-medium text-gray-500">完成度</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr class="border-b border-gray-100">
                                    <td class="py-3 text-sm text-gray-900">一元二次方程式與判別式</td>
                                    <td class="py-3 text-sm text-gray-600 text-right">2</td>
                                    <td class="py-3 text-sm text-gray-600 text-right">5%</td>
                                </tr>
                                <tr class="border-b border-gray-100">
                                    <td class="py-3 text-sm text-gray-900">數列與等差、等比級數</td>
                                    <td class="py-3 text-sm text-gray-600 text-right">4</td>
                                    <td class="py-3 text-sm text-gray-600 text-right">3%</td>
                                </tr>
                                <tr class="border-b border-gray-100">
                                    <td class="py-3 text-sm text-gray-900">三角函數恆等式</td>
                                    <td class="py-3 text-sm text-gray-600 text-right">6</td>
                                    <td class="py-3 text-sm text-gray-600 text-right">10%</td>
                                </tr>
                                <tr class="border-b border-gray-100">
                                    <td class="py-3 text-sm text-gray-900">指數與對數函數</td>
                                    <td class="py-3 text-sm text-gray-600 text-right">8</td>
                                    <td class="py-3 text-sm text-gray-600 text-right">20%</td>
                                </tr>
                                <tr class="border-b border-gray-100">
                                    <td class="py-3 text-sm text-gray-900">直線與圓的方程式</td>
                                    <td class="py-3 text-sm text-gray-600 text-right">10</td>
                                    <td class="py-3 text-sm text-gray-600 text-right">2%</td>
                                </tr>
                                <tr class="border-b border-gray-100">
                                    <td class="py-3 text-sm text-gray-900">排列組合與二項式定理</td>
                                    <td class="py-3 text-sm text-gray-600 text-right">0</td>
                                    <td class="py-3 text-sm text-gray-600 text-right">0%</td>
                                </tr>
                                <tr>
                                    <td class="py-3 text-sm text-gray-900">機率與統計基礎</td>
                                    <td class="py-3 text-sm text-gray-600 text-right">0</td>
                                    <td class="py-3 text-sm text-gray-600 text-right">0%</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useLessonStore } from '@/stores/lesson'
import { lessonService } from '@/services/lesson.service'
import Nav from '@/components/common/Nav.vue'
const lesson = useLessonStore()
const progress = ref({
    total_questions: 0,
    accuracy_rate: 0,
    study_streak: 0,
    skills_progress: {}
})
const dueCount = ref(0)
onMounted(async () => {
    await lesson.getProgressSummary()
    progress.value = lesson.progress
    const due = await lessonService.getDueCount()
    dueCount.value = due.due_count
})
</script>
