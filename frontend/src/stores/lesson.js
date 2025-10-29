import { defineStore } from 'pinia'
import { lessonService } from '@/services/lesson.service'

// Helper function to normalize question object
function normalizeQuestion(question) {
  if (!question) return null
  return {
    ...question,
    id: question.id || question._id, // Ensure we always have an id field
    correct_indices: question.correct_indices || question.correct_answer || [], // Support both field names
    type: question.type || 'single' // Default to single choice if not specified
  }
}

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
        const sessionInfo = await lessonService.startLesson({ 
          type: lessonType, 
          skill_ids: skillIds 
        })
        this.currentSession = sessionInfo
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
        
        // Handle session complete signal from server
        if (response?.completed) {
          this.currentQuestion = null
          return null
        }
        
        if (!response.question) {
          // Gracefully treat as completed if backend didn't include a question
          this.currentQuestion = null
          return null
        }
        
        this.setCurrentQuestion(response.question)
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

    setCurrentQuestion(question) {
      console.log('Setting current question:', question)
      this.currentQuestion = normalizeQuestion(question)
      console.log('Normalized current question:', this.currentQuestion)
    },

    async submitAnswer(questionId, answerArray) {
      try {
        this.loading = true
        this.error = null
        
        if (!this.currentSession?.session_id) {
          throw new Error('No active session')
        }
        
        console.log('Submitting answer:', { 
          sessionId: this.currentSession.session_id,
          questionId,
          answerArray
        })
        
        const response = await lessonService.submitAnswer(
          this.currentSession.session_id,
          questionId,
          answerArray
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
