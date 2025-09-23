import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import QuestionCard from '@/components/lesson/QuestionCard.vue'

describe('QuestionCard', () => {
  let wrapper
  const mockQuestion = {
    id: '1',
    text: 'What is 2 + 2?',
    options: ['3', '4', '5', '6'],
    correct_answer: 1,
    explanation: 'Basic addition: 2 + 2 = 4',
    skill_category: 'arithmetic',
    difficulty: 1
  }
  beforeEach(() => {
    wrapper = mount(QuestionCard, {
      props: { question: mockQuestion, current: 1, total: 10 }
    })
  })
  it('renders question text correctly', () => {
    expect(wrapper.text()).toContain('What is 2 + 2?')
  })
  it('renders all answer options', () => {
    const options = wrapper.findAll('button')
    expect(options.length).toBeGreaterThanOrEqual(mockQuestion.options.length)
  })
  it('allows selecting an answer', async () => {
    const firstOption = wrapper.find('button')
    await firstOption.trigger('click')
    expect(wrapper.vm.selectedAnswer).toBe(0)
  })
  it('emits answer-submitted event when submitting', async () => {
    wrapper.vm.selectedAnswer = 1
    await wrapper.vm.$nextTick()
    const submitButton = wrapper.find('button')
    await submitButton.trigger('click')
    expect(wrapper.emitted('answer-submitted')).toBeTruthy()
    expect(wrapper.emitted('answer-submitted')[0][0]).toEqual({
      answer_index: 1,
      response_time: expect.any(Number)
    })
  })
  it('shows correct answer after submission', async () => {
    wrapper.vm.selectedAnswer = 0
    wrapper.vm.answerSubmitted = true
    await wrapper.vm.$nextTick()
    const options = wrapper.findAll('.border-green-500')
    expect(options.length).toBeGreaterThan(0)
  })
  it('displays progress correctly', () => {
    expect(wrapper.text()).toContain('Question 1 of 10')
    expect(wrapper.vm.progressPercentage).toBe(10)
  })
})
