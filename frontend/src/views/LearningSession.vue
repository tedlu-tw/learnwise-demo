<template>
    <Nav :showLogin="false" activeItem="session" />
    <div class="w-full min-h-screen py-8">
        <div class="max-w-4xl mx-auto px-4">
            <div v-if="error" class="text-red-600 mb-4 p-4 bg-red-50 rounded-lg">
                {{ error }}
                <button @click="retrySession" class="ml-2 text-blue-600 underline">重試</button>
            </div>
            
            <div v-if="loading" class="flex justify-center items-center min-h-[400px]">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span class="ml-2">載入中...</span>
            </div>
            
            <div v-else-if="question" class="bg-white rounded-xl shadow-lg">
                <QuestionCard
                    :question="question"
                    :current="currentQuestion"
                    :total="totalQuestions"
                    @answer-submitted="handleAnswerSubmitted"
                    @next-question="nextQuestion"
                />
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
import Nav from '@/components/common/Nav.vue'
import QuestionCard from '@/components/lesson/QuestionCard.vue'
import MathDisplay from '@/components/common/MathDisplay.vue'

const lesson = useLessonStore()
const auth = useAuthStore()
const router = useRouter()

const currentQuestion = ref(1)
const totalQuestions = ref(10)
const question = ref(null)
const loading = ref(false)
const error = ref(null)

// Add these missing refs
const selectedAnswer = ref(null)
const selectedAnswers = ref([])
const answerSubmitted = ref(false)
const feedback = ref(null)
const startTime = ref(Date.now())

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
        if (!lesson.currentSession || !lesson.currentQuestion) {
            if (!auth.user?.selected_skills?.length) {
                console.log('No skills found, redirecting to skills page')
                router.push('/skills')
                return
            }
            
            await lesson.startLesson('initial', auth.user.selected_skills)
            const nextQuestion = await lesson.fetchNextQuestion()
            question.value = nextQuestion
            currentQuestion.value = 1
            console.log('Initial question loaded:', question.value)
        } else {
            question.value = lesson.currentQuestion
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
    startTime.value = Date.now()  // Reset timer for new question
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

async function handleAnswerSubmitted({ answer, is_correct, response_time }) {
    const sessionId = lesson.currentSession?.session_id
    const questionId = question.value?.id
    
    if (sessionId && questionId) {
        try {
            await lessonService.submitAnswer(
                sessionId, 
                questionId, 
                answer,
                response_time
            )
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
        const nextQuestion = await lesson.fetchNextQuestion()
        if (nextQuestion) {
            question.value = nextQuestion
            currentQuestion.value++
        } else {
            // No more questions, finish the lesson
            router.push('/dashboard')
        }
    } catch (err) {
        error.value = err.message || 'Failed to load next question'
    }
}

// Add right after getting the question data
async function fetchCurrentQuestion() {
      try {
        loading.value = true
        const response = await lessonService.getNextQuestion(sessionData.value.session_id)
        console.log('Full question data received:', response)
        
        if (response.completed) {
          isSessionComplete.value = true
          return
        }
        
        question.value = response.question
        console.log('Parsed question data:', {
          id: question.value._id,
          type: question.value.type,
          text: question.value.text,
          options: question.value.options,
          correct_indices: question.value.correct_indices
        })
      } catch (err) {
        error.value = err.message || 'Error fetching question'
      } finally {
        loading.value = false
      }
    }
</script>

<style scoped>
/* Add any component-specific styles here */
</style>
