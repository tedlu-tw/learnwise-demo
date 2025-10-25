<template>
  <div class="max-w-4xl mx-auto p-6 bg-white rounded-xl shadow-lg">
    <div class="mb-4">
      <span class="text-lg font-bold">Question {{ current }} of {{ total }}</span>
      <div class="mt-2 text-xl">
        <MathText :text="question.text" />
      </div>
    </div>
    <div class="grid grid-cols-1 gap-2 mb-4">
      <button v-for="(option, idx) in question.options" :key="idx"
        :class="['border rounded p-2', selectedAnswer === idx ? 'border-blue-500' : '', answerSubmitted && idx === question.correct_answer ? 'border-green-500' : '']"
        @click="selectAnswer(idx)"
        :disabled="answerSubmitted">
        <MathText :text="option" />
      </button>
    </div>
    <div v-if="answerSubmitted">
      <div v-if="selectedAnswer === question.correct_answer" class="text-green-600">Correct!</div>
      <div v-else class="text-red-600">
        Incorrect. 
        <MathText :text="question.explanation" />
      </div>
      <button class="mt-4 btn" @click="$emit('next-question')">Next</button>
    </div>
    <div v-else>
      <button class="btn" :disabled="selectedAnswer === null" @click="submitAnswer">Submit Answer</button>
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
const answerSubmitted = ref(false)
const progressPercentage = computed(() => Math.round((props.current / props.total) * 100))
function selectAnswer(idx) {
  if (!answerSubmitted.value) selectedAnswer.value = idx
}
function submitAnswer() {
  answerSubmitted.value = true
  const response_time = Math.floor(Math.random() * 10) + 1 // Simulate
  emit('answer-submitted', { answer_index: selectedAnswer.value, response_time })
}
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
