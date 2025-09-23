<template>
  <div class="max-w-4xl mx-auto p-6 bg-white rounded-xl shadow-lg">
    <div class="mb-4">
      <span class="text-lg font-bold">Question {{ current }} of {{ total }}</span>
      <div class="mt-2 text-xl">{{ question.text }}</div>
    </div>
    <div class="grid grid-cols-1 gap-2 mb-4">
      <button v-for="(option, idx) in question.options" :key="idx"
        :class="['border rounded p-2', selectedAnswer === idx ? 'border-blue-500' : '', answerSubmitted && idx === question.correct_answer ? 'border-green-500' : '']"
        @click="selectAnswer(idx)"
        :disabled="answerSubmitted">
        {{ option }}
      </button>
    </div>
    <div v-if="answerSubmitted">
      <div v-if="selectedAnswer === question.correct_answer" class="text-green-600">Correct!</div>
      <div v-else class="text-red-600">Incorrect. {{ question.explanation }}</div>
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
  @apply bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600;
}
</style>
