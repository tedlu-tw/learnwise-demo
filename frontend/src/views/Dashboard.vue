<template>
  <div class="max-w-2xl mx-auto mt-10">
    <h2 class="text-2xl font-bold mb-4">Progress Dashboard</h2>
    <div class="bg-white p-4 rounded shadow">
      <div>Total Questions Answered: {{ progress.total_questions }}</div>
      <div>Accuracy Rate: {{ progress.accuracy_rate }}%</div>
      <div>Study Streak: {{ progress.study_streak }}</div>
      <div v-for="(skill, name) in progress.skills_progress" :key="name">
        <strong>{{ name }}</strong>: {{ skill.answered }}
      </div>
    </div>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { useLessonStore } from '@/stores/lesson'
const lesson = useLessonStore()
const progress = ref({
  total_questions: 0,
  accuracy_rate: 0,
  study_streak: 0,
  skills_progress: {}
})
onMounted(async () => {
  await lesson.getProgressSummary()
  progress.value = lesson.progress
})
</script>
