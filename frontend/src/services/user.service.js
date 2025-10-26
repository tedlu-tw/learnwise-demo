import api from './axios'

export const userService = {
  async updateSkills(selected_skills) {
    const res = await api.patch('/auth/skills', { selected_skills })
    return res.data
  },

  async getCategories() {
    try {
      const res = await api.get('/skills/categories')
      console.log('Categories API response:', res.data)  // Debug log
      if (!res.data.success) {
        throw new Error(res.data.error || 'Failed to fetch categories')
      }
      return res.data.categories || []
    } catch (error) {
      console.error('Error fetching categories:', error.response || error)
      return []  // Return empty array as fallback
    }
  }
}
