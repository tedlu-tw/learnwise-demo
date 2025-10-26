import api from './axios'

class LessonService {
  async startLesson(data) {
    try {
      if (!data.skill_ids || data.skill_ids.length === 0) {
        throw new Error('No skills selected')
      }

      const payload = {
        type: data.type || 'initial',
        skill_ids: Array.isArray(data.skill_ids) ? data.skill_ids : []
      }
      
      console.log('Starting lesson with payload:', payload)
      const res = await api.post('/lessons/start', payload)
      console.log('Lesson start response:', res.data)
      
      if (!res.data.session_id) {
        throw new Error('Invalid response: missing session_id')
      }

      // Immediately fetch first question
      const firstQuestion = await this.getNextQuestion(res.data.session_id)
      console.log('First question:', firstQuestion)

      return {
        ...res.data,
        question: firstQuestion.question
      }
      
    } catch (error) {
      console.error('Error starting lesson:', error.response?.data || error)
      throw error
    }
  }

  async getNextQuestion(session_id) {
    try {
      const res = await api.post('/lessons/next', { session_id })
      console.log('Next question response:', res.data)

      // Handle session completion
      if (res.data.message === 'Session complete') {
        return { completed: true }
      }

      // Validate question data
      if (!res.data.question || !res.data.question.text || !res.data.question.options) {
        console.error('Invalid question data:', res.data)
        throw new Error('Invalid question data received from server')
      }

      return res.data
    } catch (error) {
      console.error('Error getting next question:', error.response?.data || error)
      throw error
    }
  }

  async submitAnswer(session_id, question_id, answer_index) {
    try {
      const res = await api.post('/lessons/submit', { 
        session_id, 
        question_id, 
        answer_index 
      })
      return res.data
    } catch (error) {
      console.error('Error submitting answer:', error.response?.data || error)
      throw error
    }
  }

  async getProgressSummary() {
    try {
      const res = await api.get('/lessons/progress-summary')
      return res.data
    } catch (error) {
      console.error('Error getting progress summary:', error.response?.data || error)
      throw error
    }
  }

  async getDueCount() {
    try {
      const res = await api.get('/lessons/due-count')
      return res.data
    } catch (error) {
      console.error('Error getting due count:', error.response?.data || error)
      throw error
    }
  }
}

export const lessonService = new LessonService()
