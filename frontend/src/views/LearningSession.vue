<template>
    <Nav :showLogin="false" activeItem="session" />
    <div class="w-full h-screen flex justify-center items-center">
        <div class="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg">
            <div v-if="error" class="text-red-600 mb-4">
                {{ error }}
                <button @click="retrySession" class="ml-2 text-blue-600 underline">Retry</button>
            </div>
            
            <div v-if="loading" class="flex justify-center">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span class="ml-2">Loading...</span>
            </div>
            
            <div v-else-if="question">
                <div class="mb-6">
                    <h2 class="text-2xl font-bold text-gray-800">
                        <MathText :text="question.text" />
                    </h2>
                    <div class="flex flex-col gap-2 mt-2">
                        <div class="flex items-center gap-2">
                            <span v-if="question.is_review"
                                class="px-2 py-1 text-xs rounded bg-yellow-100 text-yellow-800">Review</span>
                            <span v-else class="px-2 py-1 text-xs rounded bg-blue-100 text-blue-800">New</span>
                        </div>
                        <div class="flex items-center">
                            <span v-if="question.type === 'multiple'"
                                class="px-3 py-2 text-sm font-medium rounded bg-purple-100 text-purple-800 flex items-center gap-2">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                選擇所有正確答案 (可複選)
                            </span>
                            <span v-else
                                class="px-3 py-2 text-sm font-medium rounded bg-blue-100 text-blue-800 flex items-center gap-2">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                        d="M5 13l4 4L19 7" />
                                </svg>
                                選擇一個答案
                            </span>
                        </div>
                    </div>
                </div>
                
                <div class="space-y-3">
                    <div v-for="(option, index) in question.options" :key="question.id + '-' + index"
                        class="flex items-center p-3 rounded-lg border transition-colors duration-200"
                        :class="[
                            question.type === 'multiple' ? 
                                (selectedAnswers.includes(index) ? 'border-blue-500 bg-blue-50' : 'border-gray-200') :
                                (selectedAnswer === index ? 'border-blue-500 bg-blue-50' : 'border-gray-200'),
                            answerSubmitted && feedback?.correct_indices.includes(index) ? 'border-green-500 bg-green-50' : '',
                            answerSubmitted && !feedback?.correct_indices.includes(index) && 
                                (question.type === 'multiple' ? selectedAnswers.includes(index) : selectedAnswer === index)
                                ? 'border-red-500 bg-red-50' : ''
                        ]">
                        <div class="mr-3">
                            <template v-if="question.type === 'multiple'">
                                <input type="checkbox" 
                                    :checked="selectedAnswers.includes(index)"
                                    @change="toggleAnswer(index)"
                                    :disabled="answerSubmitted"
                                    class="form-checkbox h-5 w-5 text-blue-600"/>
                            </template>
                            <template v-else>
                                <input type="radio" 
                                    :value="index" 
                                    v-model="selectedAnswer"
                                    name="answer"
                                    :disabled="answerSubmitted"
                                    class="form-radio h-5 w-5 text-blue-600"/>
                            </template>
                        </div>
                        <MathText :text="option" />
                    </div>
                </div>
                
                <div v-if="answerSubmitted && feedback" class="mt-4">
                    <div :class="[
                        'p-4 rounded-lg border-l-4',
                        feedback.correct ? 'bg-green-50 border-green-500' : 'bg-red-50 border-red-500'
                    ]">
                        <div class="flex items-center">
                            <svg v-if="feedback.correct" class="w-6 h-6 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                            </svg>
                            <svg v-else class="w-6 h-6 text-red-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                            </svg>
                            <span class="font-bold" :class="feedback.correct ? 'text-green-700' : 'text-red-700'">
                                {{ feedback.correct ? '答對了！' : '答錯了' }}
                            </span>
                        </div>

                        <div v-if="!feedback.correct && feedback.correct_indices" class="mt-3">
                            <div class="font-medium text-gray-700 mb-2">正確答案:</div>
                            <div class="space-y-2">
                                <div v-for="idx in feedback.correct_indices" :key="idx" 
                                     class="p-2 bg-white rounded border border-gray-200">
                                    <MathText :text="question.options[idx]" />
                                </div>
                            </div>
                        </div>

                        <div v-if="feedback.explanation" class="mt-3 text-gray-600">
                            <div class="font-medium text-gray-700 mb-1">說明:</div>
                            <MathText :text="feedback.explanation" />
                        </div>
                    </div>
                    
                    <div class="mt-4 flex justify-end">
                        <button class="btn" @click="nextQuestion">下一題</button>
                    </div>
                </div>
                <div v-else>
                    <div class="mt-6 flex justify-between items-center">
                        <span class="text-sm text-gray-500">
                            Progress: {{ currentQuestion }}/{{ totalQuestions }}
                        </span>
                        <button @click="submitAnswer"
                            :disabled="(question.type === 'multiple' ? selectedAnswers.length === 0 : selectedAnswer === null) || answerSubmitted"
                            class="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50">
                            Submit Answer
                        </button>
                    </div>
                </div>
            </div>
            <div v-else-if="!error">
                <p class="text-gray-500">Loading question...</p>
            </div>
        </div>
    </div>
</template>
<script setup>
import { ref, onMounted, watch } from 'vue'
import { useLessonStore } from '@/stores/lesson'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import { lessonService } from '@/services/lesson.service'
import MathText from '@/components/common/MathText.vue'
import Nav from '@/components/common/Nav.vue'

const lesson = useLessonStore()
const auth = useAuthStore()
const router = useRouter()

const selectedAnswer = ref(null)
const selectedAnswers = ref([])
const currentQuestion = ref(1)
const totalQuestions = ref(10)
const feedback = ref(null)
const answerSubmitted = ref(false)
const question = ref(null)
const loading = ref(false)
const error = ref(null)

onMounted(async () => {
    console.log('LearningSession mounted')
    console.log('Auth state before initialization:', { user: auth.user, token: auth.token })

    try {
        loading.value = true

        // Initialize auth if not already initialized
        if (!auth.user && localStorage.getItem('token')) {
            await auth.initializeAuth()
            console.log('Auth state after initialization:', { user: auth.user, token: auth.token })
        }

        // Only start lesson if not already started
        if (!lesson.currentSession || !lesson.currentSession.question) {
            if (!auth.user?.selected_skills?.length) {
                console.log('No skills found, redirecting to skills page')
                router.push('/skills')
                return
            }
            
            await lesson.startLesson('initial', auth.user.selected_skills)
            const nextQuestion = await lesson.fetchNextQuestion()
            question.value = nextQuestion
            console.log('Initial question loaded:', question.value)
        } else {
            question.value = lesson.currentSession.question
        }
    } catch (e) {
        console.error('Error starting session:', e)
        error.value = 'Failed to start learning session. Please try again.'
    } finally {
        loading.value = false
    }
})

watch(question, () => {
    selectedAnswer.value = null
    selectedAnswers.value = []
    answerSubmitted.value = false
    feedback.value = null
})

function toggleAnswer(idx) {
    if (answerSubmitted.value) return
    const index = selectedAnswers.value.indexOf(idx)
    if (index === -1) {
        selectedAnswers.value.push(idx)
    } else {
        selectedAnswers.value.splice(index, 1)
    }
}

async function submitAnswer() {
    if (answerSubmitted.value) return
    if ((question.value.type === 'multiple' && selectedAnswers.value.length === 0) ||
        (question.value.type !== 'multiple' && selectedAnswer.value === null)) return
        
    const sessionId = lesson.currentSession?.session_id
    const questionId = question.value?.id
    
    // Send answers as array for both single and multiple choice
    const answerArray = question.value.type === 'multiple' 
        ? selectedAnswers.value
        : [selectedAnswer.value]
        
    feedback.value = null
    
    if (sessionId && questionId) {
        try {
            const res = await lessonService.submitAnswer(sessionId, questionId, answerArray)
            feedback.value = res
            answerSubmitted.value = true
        } catch (err) {
            error.value = err.message || 'Failed to submit answer'
        }
    }
}

async function nextQuestion() {
    answerSubmitted.value = false
    feedback.value = null
    selectedAnswer.value = null
    selectedAnswers.value = []
    
    const sessionId = lesson.currentSession?.session_id
    if (!sessionId) {
        router.push('/dashboard')
        return
    }
    
    try {
        const nextRes = await lessonService.getNextQuestion(sessionId)
        if (nextRes.completed) {
            // Session is complete, redirect to dashboard or summary
            router.push('/dashboard')
            return
        }
        
        if (nextRes.question) {
            question.value = nextRes.question
            currentQuestion.value++
        }
    } catch (err) {
        error.value = err.message || 'Failed to load next question'
    }
}

function retrySession() {
    error.value = null
    location.reload()
}
</script>
<style scoped>
.btn {
    padding: 0.75rem 1.5rem;
    background-color: #2563eb;
    color: white;
    border-radius: 0.375rem;
    cursor: pointer;
    transition: background-color 0.2s;
}

.btn:hover {
    background-color: #1d4ed8;
}

.btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}
</style>
