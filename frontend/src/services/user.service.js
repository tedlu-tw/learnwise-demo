import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
export const userService = {
  async updateSkills(selected_skills) {
    const auth = useAuthStore()
    const res = await axios.patch('/api/auth/skills', { selected_skills }, {
      headers: { Authorization: `Bearer ${auth.token}` }
    })
    return res.data
  }
}
