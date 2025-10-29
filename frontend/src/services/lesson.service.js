import api from './axios'

class LessonService {
  constructor() {
    this.api = api
  }
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

      // Do not fetch the first question here; caller will fetch explicitly
      return res.data
      
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
      if (res.data.completed || res.data.message === 'Session complete') {
        return { completed: true }
      }

      if (!res.data.question) {
        return { completed: true }
      }

      // Normalize the question ID and ensure it's a string
      const question = res.data.question

      // Normalize text field for legacy records
      if (!question.text && question.question_text) {
        question.text = question.question_text
      }

      question.id = String(question._id || question.id || '')
      console.log('Normalized question ID:', question.id)

      if (!question.id) {
        throw new Error('Question ID is missing')
      }

      // Ensure question type is set
      if (!res.data.question.type) {
        console.warn('Question type not set, defaulting to single')
        res.data.question.type = 'single'
      }

      // Validate type is either single or multiple
      if (!['single', 'multiple'].includes(res.data.question.type)) {
        console.error('Invalid question type:', res.data.question.type)
        throw new Error('Invalid question type received from server')
      }

      console.log('Processed question:', {
        ...res.data.question,
        type: res.data.question.type,
        options: res.data.question.options.length
      })

      return res.data
    } catch (error) {
      console.error('Error getting next question:', error.response?.data || error)
      throw error
    }
  }

  async submitAnswer(session_id, question_id, answer, response_time) {
    try {
      // Ensure response_time is a positive number
      if (typeof response_time !== 'number' || response_time <= 0) {
        response_time = 1; // Default to 1 second if invalid
      }
      
      const res = await api.post('/lessons/submit', {
        session_id,
        question_id,
        answer_indices: Array.isArray(answer) ? answer : [answer],
        response_time: Math.max(0.1, Math.round(response_time * 100) / 100)  // Round to 2 decimals, minimum 0.1s
      })

      // Process feedback
      if (res.data.feedback) {
        const feedback = res.data.feedback
        console.log('Learning feedback:', {
          nextReview: new Date(feedback.next_review),
          daysUntilReview: feedback.days_until_review,
          state: feedback.state,
          difficulty: feedback.difficulty
        })
      }

      return {
        ...res.data,
        streak: res.data.streak || 0,
        correct: res.data.feedback?.correct,
        correct_indices: res.data.feedback?.correct_indices,
        selected_indices: res.data.selected_indices
      }
    } catch (error) {
      console.error('Error submitting answer:', error.response?.data || error)
      throw error
    }
  }

  async getProgressSummary() {
    try {
      const res = await api.get('/lessons/progress-summary')
      return {
        total_questions: res.data.total_questions || 0,
        accuracy_rate: res.data.accuracy_rate || 0,
        mastery_rate: res.data.mastery_rate || 0,
        skills_progress: res.data.skills_progress || {},
        learning_stats: res.data.learning_stats || { learning: 0, review: 0, relearning: 0 }
      }
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

  async getExplanation(questionId, selectedIndices) {
    try {
      console.log('Requesting explanation for question:', questionId, 'with selected indices:', selectedIndices)
      const res = await api.post('/lessons/explain', {
        question_id: questionId,
        selected_indices: selectedIndices
      })
      console.log('Explanation response:', res.data)
      if (!res.data.explanation) {
        throw new Error('No explanation received from server')
      }
      return res.data
    } catch (error) {
      console.error('Error getting explanation:', error.response?.data || error)
      throw new Error(error.response?.data?.message || error.message || '無法獲取解釋')
    }
  }

  async sendFollowUp({ questionId, selectedIndices, message, threadId, stepKey, history, explanation }) {
    try {
      const { data } = await api.post('/lessons/explain/chat', {
        question_id: questionId,
        selected_indices: selectedIndices,
        message,
        thread_id: threadId,
        step_key: stepKey,
        history,
        explanation_text: explanation
      })
      return data
    } catch (error) {
      console.error('Error sending follow-up question:', error.response?.data || error)
      throw new Error(error.response?.data?.message || error.message || '無法發送後續問題')
    }
  }
}

export const lessonService = new LessonService()
