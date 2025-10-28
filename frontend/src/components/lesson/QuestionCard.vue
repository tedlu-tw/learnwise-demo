<template>
  <div class="max-w-4xl mx-auto p-6 bg-white rounded-xl shadow-lg">
    <div class="mb-4">
      <span class="text-lg font-bold">Question {{ current }} of {{ total }}</span>
      <div class="mt-2 text-xl">
        <MathText :text="question?.text || ''" />
      </div>
    </div>
    <div class="mb-2">
      <div class="text-sm text-gray-600 mb-1">{{ question?.category || '' }} - {{ question?.sub_topic || '' }}</div>
      <div class="text-sm font-medium text-gray-700">
        {{ question?.type === 'multiple' ? '選擇所有正確答案' : '選擇一個答案' }}
      </div>
    </div>
    <div class="grid grid-cols-1 gap-2 mb-4">
      <button v-for="(option, idx) in question?.options || []" :key="idx"
        :class="[
          'border rounded p-2 flex items-center', 
          question?.type === 'multiple' 
            ? (selectedAnswers.includes(idx) ? 'border-blue-500 bg-blue-50' : '')
            : (selectedAnswer === idx ? 'border-blue-500 bg-blue-50' : ''),
          answerSubmitted && getCorrectIndices.includes(idx) ? 'border-green-500 bg-green-50' : '',
          answerSubmitted && !getCorrectIndices.includes(idx) && 
            (question?.type === 'multiple' ? selectedAnswers.includes(idx) : selectedAnswer === idx)
            ? 'border-red-500 bg-red-50' : ''
        ]"
        @click="selectAnswer(idx)"
        :disabled="answerSubmitted">
        <div class="mr-2">
          <div v-if="question?.type === 'multiple'" 
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
        <span v-for="tag in question?.tags || []" :key="tag"
              class="px-2 py-1 bg-gray-100 text-sm rounded-full text-gray-700">
          {{ tag }}
        </span>
      </div>

      <div class="mt-6 space-y-4">
        <div class="border-t pt-4">
          <ExplanationPanel 
            :questionId="String(question?._id || question?.id || '')"
            :selectedIndices="question?.type === 'multiple' ? 
              selectedAnswers : 
              (selectedAnswer !== null ? [selectedAnswer] : [])"
          />
        </div>
        <div class="flex justify-end space-x-4 mt-4">
          <button class="btn" @click="$emit('next-question')">下一題</button>
        </div>
      </div>
    </div>
    <div v-else>
      <button class="btn" 
        :disabled="question?.type === 'multiple' ? selectedAnswers.length === 0 : selectedAnswer === null" 
        @click="submitAnswer">
        提交答案
      </button>
    </div>
    <div class="mt-2 text-sm text-gray-500">
      難度: {{ '★'.repeat(question?.difficulty || 0) }}{{ '☆'.repeat(5 - (question?.difficulty || 0)) }}
    </div>
    <div class="mt-4 text-sm text-gray-500">Progress: {{ progressPercentage }}%</div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import MathText from '@/components/common/MathText.vue'
import ExplanationPanel from './ExplanationPanel.vue'

const props = defineProps({
  question: {
    type: Object,
    required: true,
    default: () => ({
      type: 'single',
      correct_indices: [],
      correct_answer: [],
      options: [],
      text: '',
      category: '',
      sub_topic: '',
      difficulty: 1,
      tags: []
    })
  },
  current: Number,
  total: Number
})

// Add debug logging for question data
console.log('QuestionCard received question:', {
  id: props.question?.id,
  _id: props.question?._id,
  type: props.question?.type,
  correct_indices: props.question?.correct_indices,
  correct_answer: props.question?.correct_answer,
  questionData: props.question
})

const selectedAnswer = ref(null)
const selectedAnswers = ref([])
const answerSubmitted = ref(false)
const startTime = ref(Date.now())  // Track when question is shown

const progressPercentage = computed(() => Math.round((props.current / props.total) * 100))

// Helper to get correct indices, supporting both correct_indices and correct_answer properties for backward compatibility
const getCorrectIndices = computed(() => {
  console.log('Checking correct indices for question:', {
    correct_indices: props.question?.correct_indices,
    questionData: props.question
  })
  return props.question?.correct_indices || []
})

// Safe computed property for checking correctness
const isCorrect = computed(() => {
  console.log('Checking answer correctness:', {
    correctIndices: getCorrectIndices.value,
    selectedAnswer: selectedAnswer.value,
    selectedAnswers: selectedAnswers.value,
    questionType: props.question?.type
  })
  
  const correctIndices = getCorrectIndices.value
  if (!correctIndices.length) {
    console.log('No correct indices found')
    return false
  }
  
  if (props.question?.type === 'multiple') {
    const selected = selectedAnswers.value
    const isCorrect = selected.length === correctIndices.length && 
           selected.every(ans => correctIndices.includes(ans)) &&
           correctIndices.every(ans => selected.includes(ans))
    console.log('Multiple choice answer check:', { isCorrect, selected, correctIndices })
    return isCorrect
  }
  
  const isSingleCorrect = selectedAnswer.value !== null && 
         correctIndices.includes(selectedAnswer.value)
  console.log('Single choice answer check:', { isSingleCorrect, selectedAnswer: selectedAnswer.value, correctIndices })
  return isSingleCorrect
})

function selectAnswer(idx) {
  if (answerSubmitted.value) return
  
  if (props.question?.type === 'multiple') {
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
  if (!props.question) {
    console.error('No question data available')
    return
  }

  if (selectedAnswer.value === null && selectedAnswers.value.length === 0) {
    console.log('No answer selected')
    return
  }

  console.log('Submitting answer:', {
    questionType: props.question.type,
    selectedAnswer: selectedAnswer.value,
    selectedAnswers: selectedAnswers.value,
    questionId: props.question._id || props.question.id
  })
  
  answerSubmitted.value = true
  const response_time = (Date.now() - startTime.value) / 1000  // Convert to seconds
  
  // Handle both single and multiple choice questions
  const answer = props.question.type === 'multiple' 
    ? [...selectedAnswers.value]     // Create copy of array for multiple choice
    : [selectedAnswer.value]    // Wrap single choice in array for consistency

  const payload = { 
    answer,
    is_correct: isCorrect.value,
    response_time 
  }

  console.log('Emitting answer-submitted event:', payload)
  emit('answer-submitted', payload)
}

// Reset selections and start time when question changes
watch(() => props.question, (newQuestion) => {
  console.log('Question changed, resetting state:', newQuestion)
  selectedAnswer.value = null
  selectedAnswers.value = []
  answerSubmitted.value = false
  startTime.value = Date.now()  // Reset start time for new question
}, { deep: true })

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
