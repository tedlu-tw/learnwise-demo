<template>
  <div class="max-w-4xl mx-auto p-6 bg-white rounded-xl shadow-lg">
    <div class="mb-4">
      <span class="text-lg font-bold">Question {{ current }} of {{ total }}</span>
      <div class="mt-2 text-xl">
        <MathText :text="question.text" />
      </div>
    </div>
    <div class="mb-2">
      <div class="text-sm text-gray-600 mb-1">{{ question.category }} - {{ question.sub_topic }}</div>
      <div class="text-sm font-medium text-gray-700">
        {{ question.type === 'multiple' ? '選擇所有正確答案' : '選擇一個答案' }}
      </div>
    </div>
    <div class="grid grid-cols-1 gap-2 mb-4">
      <button v-for="(option, idx) in question.options" :key="idx"
        :class="[
          'border rounded p-2 flex items-center', 
          question.type === 'multiple' 
            ? (selectedAnswers.includes(idx) ? 'border-blue-500 bg-blue-50' : '')
            : (selectedAnswer === idx ? 'border-blue-500 bg-blue-50' : ''),
          answerSubmitted && question.correct_answer.includes(idx) ? 'border-green-500 bg-green-50' : '',
          answerSubmitted && !question.correct_answer.includes(idx) && 
            (question.type === 'multiple' ? selectedAnswers.includes(idx) : selectedAnswer === idx)
            ? 'border-red-500 bg-red-50' : ''
        ]"
        @click="selectAnswer(idx)"
        :disabled="answerSubmitted">
        <div class="mr-2">
          <div v-if="question.type === 'multiple'" 
               class="w-5 h-5 border rounded flex items-center justify-center">
            <svg v-if="selectedAnswers.includes(idx)" class="w-4 h-4 text-blue-600" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
            </svg>
          </div>
          <div v-else class="w-5 h-5 border rounded-full flex items-center justify-center">
            <div v-if="selectedAnswer === idx" class="w-3 h-3 bg-blue-600 rounded-full"></div>
          </div>
        </div>
        <MathText :text="option" />
      </button>
    </div>
    <div v-if="answerSubmitted" class="mt-4">
      <div v-if="isCorrect" class="text-green-600 font-medium">
        答對了！
      </div>
      <div v-else class="text-red-600">
        答錯了
      </div>
      <div class="mt-2 flex flex-wrap gap-1">
        <span v-for="tag in question.tags" :key="tag"
              class="px-2 py-1 bg-gray-100 text-sm rounded-full text-gray-700">
          {{ tag }}
        </span>
      </div>
      <button class="mt-4 btn" @click="$emit('next-question')">下一題</button>
    </div>
    <div v-else>
      <button class="btn" 
        :disabled="question.type === 'multiple' ? selectedAnswers.length === 0 : selectedAnswer === null" 
        @click="submitAnswer">
        提交答案
      </button>
    </div>
    <div class="mt-2 text-sm text-gray-500">
      難度: {{ '★'.repeat(question.difficulty) }}{{ '☆'.repeat(5 - question.difficulty) }}
    </div>
    <div class="mt-4 text-sm text-gray-500">Progress: {{ progressPercentage }}%</div>
  </div>
</template>
<script setup>
import { ref, computed } from 'vue'
import MathText from '@/components/common/MathText.vue'
const props = defineProps({
  question: Object,
  current: Number,
  total: Number
})
const selectedAnswer = ref(null)
const selectedAnswers = ref([])
const answerSubmitted = ref(false)

const progressPercentage = computed(() => Math.round((props.current / props.total) * 100))
const isCorrect = computed(() => {
  if (props.question.type === 'multiple') {
    const selected = selectedAnswers.value
    const correct = props.question.correct_answer
    return selected.length === correct.length && 
           selected.every(ans => correct.includes(ans)) &&
           correct.every(ans => selected.includes(ans))
  }
  return selectedAnswer.value !== null && 
         props.question.correct_answer.includes(selectedAnswer.value)
})

function selectAnswer(idx) {
  if (answerSubmitted.value) return
  
  if (props.question.type === 'multiple') {
    const index = selectedAnswers.value.indexOf(idx)
    if (index === -1) {
      selectedAnswers.value.push(idx)
    } else {
      selectedAnswers.value.splice(index, 1)
    }
  } else {
    selectedAnswer.value = idx
  }
}

function submitAnswer() {
  if (selectedAnswer.value === null && selectedAnswers.value.length === 0) return

  answerSubmitted.value = true
  const response_time = Math.floor(Math.random() * 10) + 1 // Simulate
  
  // For single choice, send the selected index
  // For multiple choice, send the first selected index (we'll enhance this later)
  const answer_index = props.question.type === 'multiple' 
    ? selectedAnswers.value[0]
    : selectedAnswer.value

  emit('answer-submitted', { 
    answer_index,
    is_correct: isCorrect.value,
    response_time 
  })
}

// Reset selections when question changes
watch(() => props.question, () => {
  selectedAnswer.value = null
  selectedAnswers.value = []
  answerSubmitted.value = false
})
const emit = defineEmits(['answer-submitted', 'next-question'])
</script>
<style scoped>
.btn {
  background-color: #3b82f6;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  border: none;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn:hover {
  background-color: #2563eb;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
