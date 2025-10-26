import { defineStore } from 'pinia'
import { lessonService } from '@/services/lesson.service'

export const useLessonStore = defineStore('lesson', {
  state: () => ({
    currentSession: null,
    currentQuestion: null,
    progress: null,
    error: null,
    loading: false
  }),
  
  getters: {
    accuracyRate: (state) => state.progress?.accuracy_rate || 0,
    sessionId: (state) => state.currentSession?.session_id,
    hasActiveSession: (state) => !!state.currentSession?.session_id
  },
  
  actions: {
    resetState() {
      this.currentSession = null
      this.currentQuestion = null
      this.error = null
      this.loading = false
    },
    
    async startLesson(lessonType, skillIds) {
      try {
        this.loading = true
        this.error = null
        
        // Reset state when starting new lesson
        this.resetState()
        
        console.log('Starting lesson:', { lessonType, skillIds })
        this.currentSession = await lessonService.startLesson({ 
          type: lessonType, 
          skill_ids: skillIds 
        })
        
        console.log('Session started:', this.currentSession)
        return this.currentSession
      } catch (error) {
        console.error('Error starting lesson:', error)
        this.error = error.message || 'Failed to start lesson'
        throw error
      } finally {
        this.loading = false
      }
    },

    async fetchNextQuestion() {
      try {
        this.loading = true
        this.error = null
        
        if (!this.currentSession?.session_id) {
          throw new Error('No active session')
        }
        
        console.log('Fetching next question for session:', this.currentSession.session_id)
        const response = await lessonService.getNextQuestion(this.currentSession.session_id)
        
        if (!response.question) {
          throw new Error('No question returned from server')
        }
        
        this.currentQuestion = response.question
        console.log('Question fetched:', this.currentQuestion)
        return this.currentQuestion
      } catch (error) {
        console.error('Error fetching next question:', error)
        this.error = error.message || 'Failed to fetch question'
        throw error
      } finally {
        this.loading = false
      }
    },

    async submitAnswer(questionId, answerIndex) {
      try {
        this.loading = true
        this.error = null
        
        if (!this.currentSession?.session_id) {
          throw new Error('No active session')
        }
        
        console.log('Submitting answer:', { 
          sessionId: this.currentSession.session_id,
          questionId,
          answerIndex
        })
        
        const response = await lessonService.submitAnswer(
          this.currentSession.session_id,
          questionId,
          answerIndex
        )
        
        console.log('Answer submission response:', response)
        return response
      } catch (error) {
        console.error('Error submitting answer:', error)
        this.error = error.message || 'Failed to submit answer'
        throw error
      } finally {
        this.loading = false
      }
    },

    async getProgressSummary() {
      try {
        this.progress = await lessonService.getProgressSummary()
        return this.progress
      } catch (error) {
        console.error('Error getting progress:', error)
        this.error = error.message || 'Failed to get progress'
        throw error
      }
    }
  }
})
