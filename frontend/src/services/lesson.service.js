import api from './axios'
class LessonService {
  async startLesson(data) {
    const res = await api.post('/lessons/start', data)
    return res.data
  }
  async getNextQuestion(session_id) {
    const res = await api.post('/lessons/next', { session_id })
    return res.data
  }
  async submitAnswer(session_id, question_id, answer_index) {
    const res = await api.post('/lessons/submit', { session_id, question_id, answer_index })
    return res.data
  }
  async getProgressSummary() {
    const res = await api.get('/lessons/progress-summary')
    return res.data
  }
}
export const lessonService = new LessonService()
