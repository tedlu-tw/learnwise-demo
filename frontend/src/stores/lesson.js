import { defineStore } from 'pinia'
import { lessonService } from '@/services/lesson.service'

export const useLessonStore = defineStore('lesson', {
  state: () => ({
    currentSession: null,
    progress: null
  }),
  getters: {
    accuracyRate: (state) => state.progress?.accuracy_rate || 0
  },
  actions: {
    async startLesson(lessonType, skillIds) {
      this.currentSession = await lessonService.startLesson({ type: lessonType, skill_ids: skillIds })
    },
    async getProgressSummary() {
      this.progress = await lessonService.getProgressSummary()
    }
  }
})
