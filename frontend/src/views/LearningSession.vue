<template>
  <div class="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg">
    <div v-if="question">
      <div class="mb-6">
        <h2 class="text-2xl font-bold text-gray-800">{{ question.text }}</h2>
      </div>
      <div class="space-y-3">
        <div v-for="(option, index) in question.options" :key="index">
          <label class="flex items-center space-x-2">
            <input
              type="radio"
              :value="index"
              v-model="selectedAnswer"
              name="answer"
            />
            <span>{{ option }}</span>
          </label>
        </div>
      </div>
      <div v-if="feedback">
        <div v-if="feedback.correct" class="text-green-600 mt-4">Correct!</div>
        <div v-else class="text-red-600 mt-4">Incorrect. Correct answer: {{ question.options[feedback.correct_index] }}<br/>Explanation: {{ feedback.explanation }}</div>
      </div>
      <div class="mt-6 flex justify-between">
        <span class="text-sm text-gray-500">
          Progress: {{ currentQuestion }}/{{ totalQuestions }}
        </span>
        <button
          @click="submitAnswer"
          :disabled="selectedAnswer === null"
          class="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          Submit
        </button>
      </div>
    </div>
    <div v-else>
      <p class="text-gray-500">Loading question...</p>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { useLessonStore } from '@/stores/lesson'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import { lessonService } from '@/services/lesson.service'
const lesson = useLessonStore()
const auth = useAuthStore()
const router = useRouter()
const question = ref(null)
const selectedAnswer = ref(null)
const currentQuestion = ref(1)
const totalQuestions = ref(10)
const feedback = ref(null)

onMounted(async () => {
  // Only start lesson if not already started
  if (!lesson.currentSession || !lesson.currentSession.question) {
    if (!auth.user?.selected_skills?.length) {
      router.push('/skills')
      return
    }
    await lesson.startLesson('initial', auth.user.selected_skills)
  }
  question.value = lesson.currentSession?.question
})

function selectAnswer(idx) {
  selectedAnswer.value = idx
}
async function submitAnswer() {
  if (selectedAnswer.value === null) return
  // Submit answer to backend for judging
  const sessionId = lesson.currentSession?.session_id
  const questionId = question.value?.id
  const answerIndex = selectedAnswer.value
  feedback.value = null
  if (sessionId && questionId) {
    const res = await lessonService.submitAnswer(sessionId, questionId, answerIndex)
    feedback.value = res
  }
  selectedAnswer.value = null
  currentQuestion.value++
  if (currentQuestion.value > totalQuestions.value) {
    router.push('/dashboard')
    return
  }
  // Get next question from backend
  if (!sessionId) {
    router.push('/dashboard')
    return
  }
  const nextRes = await lessonService.getNextQuestion(sessionId)
  if (nextRes && nextRes.question) {
    question.value = nextRes.question
  } else {
    // Session complete or no more questions
    router.push('/dashboard')
  }
}
</script>
