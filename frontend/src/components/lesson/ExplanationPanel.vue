<template>
  <div class="border rounded-lg p-4 bg-gray-50 relative mt-4 mb-4">
    <div v-if="isValid">
      <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-white bg-opacity-90 rounded-lg z-50">
        <div class="flex items-center space-x-2">
          <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
          <span class="text-gray-600 text-lg">正在生成解釋...</span>
        </div>
      </div>

      <div v-else-if="explanation" class="space-y-4">
        <div class="text-lg font-medium text-gray-700 border-b pb-2 flex items-center justify-between">
          <span>詳細解釋</span>
          <button
            class="text-sm px-3 py-1 rounded bg-indigo-600 text-white hover:bg-indigo-700"
            @click="openChat()"
          >追問</button>
        </div>
        <div class="prose prose-sm max-w-none bg-white p-4 rounded-lg shadow-sm">
          <template v-for="(section, index) in formattedExplanation" :key="index">
            <div v-if="section.type === 'step'" class="mb-6">
              <div class="flex items-center justify-between mb-3">
                <h3 class="font-bold text-lg text-gray-800">
                  <MathDisplay :text="section.title" />
                </h3>
                <button
                  class="text-xs px-2 py-1 rounded border border-indigo-200 text-indigo-700 hover:bg-indigo-50"
                  @click="openChat(section.title)"
                >步驟追問</button>
              </div>
              <div class="pl-4">
                <template v-for="(content, contentIndex) in section.contents" :key="contentIndex">
                  <ul v-if="content.type === 'list'" class="list-disc ml-6 my-2">
                    <li v-for="(item, i) in content.items" :key="i">
                      <MathDisplay :text="item" />
                    </li>
                  </ul>
                  <template v-else>
                    <MathDisplay :text="content.text" />
                  </template>
                </template>
              </div>
            </div>
            <div v-else>
              <MathDisplay :text="section.text" />
            </div>
          </template>
        </div>
        <!-- Disclaimer -->
        <div class="mt-2 text-xs text-gray-500 italic">AI 生成結果僅供參考。</div>
      </div>

      <div v-else-if="error" class="mt-4 text-red-600 p-4 bg-red-50 rounded-lg flex items-center justify-between">
        <div class="flex items-center">
          <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {{ error }}
        </div>
        <button @click="getExplanation" class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">
          重試
        </button>
      </div>

      <div v-else class="mt-4">
        <button @click="getExplanation" class="flex items-center justify-center w-full py-4 px-6 text-lg font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors duration-200 shadow-md hover:shadow-lg">
          <svg class="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
          </svg>
          點擊查看學習提示
        </button>
      </div>
    </div>

    <div v-else class="mt-2 text-red-500 text-sm space-y-1">
      <div>Debug info:</div>
      <div>Question ID: {{ questionId || 'missing' }}</div>
      <div>Selected Indices: {{ selectedIndices ? JSON.stringify(selectedIndices) : 'missing' }}</div>
      <div>Valid: {{ isValid }}</div>
    </div>
  </div>

  <!-- Follow-up Chat Drawer -->
  <ChatDrawer
    :open="chatOpen"
    :messages="chatMessages"
    :loading="chatLoading"
    :error="chatError"
    @close="chatOpen = false"
    @send="onSendFollowUp"
  />
  <div v-if="explanation && chatOpen" class="fixed bottom-4 right-4 z-40 hidden md:flex gap-2">
    <button class="text-xs px-2 py-1 rounded bg-gray-100 hover:bg-gray-200" @click="onSendFollowUp('可以更直白地解釋嗎？')">更直白</button>
    <button class="text-xs px-2 py-1 rounded bg-gray-100 hover:bg-gray-200" @click="onSendFollowUp('可以舉一個例子嗎？')">舉例</button>
    <button class="text-xs px-2 py-1 rounded bg-gray-100 hover:bg-gray-200" @click="onSendFollowUp('哪一步最容易錯？')">易錯點</button>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import MathDisplay from '@/components/common/MathDisplay.vue'
import ChatDrawer from '@/components/lesson/ChatDrawer.vue'
import { lessonService } from '@/services/lesson.service'

const props = defineProps({
  questionId: {
    type: String,
    required: true
  },
  selectedIndices: {
    type: Array,
    required: true
  }
})

const explanation = ref(null)
const loading = ref(false)
const error = ref(null)

// follow-up chat state
const chatOpen = ref(false)
const chatMessages = ref([])
const chatLoading = ref(false)
const chatError = ref(null)
const chatThreadId = ref(null)
const chatStepKey = ref(null)

function openChat(stepTitle = null) {
  if (!explanation.value) return
  chatOpen.value = true
  chatStepKey.value = stepTitle
  // seed with system context as assistant message to show scope
  if (chatMessages.value.length === 0) {
    chatMessages.value.push({ role: 'assistant', content: '針對上面的解釋提出你的問題吧～' })
  }
}

const isValid = computed(() => {
  const valid = Boolean(props.questionId && Array.isArray(props.selectedIndices))
  return valid
})

function processInlineMath(text) {
  return text
}

const formattedExplanation = computed(() => {
  if (!explanation.value) return []
  const sections = []
  let currentStep = null
  const paragraphs = explanation.value.split(/\n\s*\n/).filter(p => p.trim())
  for (const paragraph of paragraphs) {
    const normalized = paragraph.trim()
    const lines = normalized.split(/\r\n|\n|\r|\u2028|\u2029/)
    const listItems = []
    for (const line of lines) {
      const m = line.match(/^\s*(?:[\*\-–—－−•·・▪◦●○])\s*(.+)$/u)
      if (m) listItems.push(m[1])
    }
    if (listItems.length >= 2 && listItems.length === lines.filter(l => l.trim()).length) {
      if (currentStep) {
        currentStep.contents.push({ type: 'list', items: listItems })
      } else {
        sections.push({ type: 'list', items: listItems })
      }
      continue
    }

    const stepMatch = normalized.match(/^\s*(?:\*\*|__)?\s*(步驟[零一二三四五六七八九十\d]+：.*?)\s*(?:\*\*|＊＊|__)?\s*$/)
    if (stepMatch) {
      if (currentStep) sections.push(currentStep)
      currentStep = { type: 'step', title: stepMatch[1], contents: [] }
      continue
    }

    const boldOnlyHeading = normalized.match(/^\s*(\*\*|__)([\s\S]+?)\1\s*$/)
    if (boldOnlyHeading) {
      if (currentStep) sections.push(currentStep)
      currentStep = { type: 'step', title: boldOnlyHeading[2].trim(), contents: [] }
      continue
    }

    const processedText = processInlineMath(paragraph)
    if (currentStep) {
      currentStep.contents.push({ type: 'text', text: processedText })
    } else {
      sections.push({ type: 'text', text: processedText })
    }
  }
  if (currentStep) sections.push(currentStep)
  return sections
})

async function getExplanation() {
  loading.value = true
  error.value = null
  try {
    const result = await lessonService.getExplanation(props.questionId, props.selectedIndices)
    explanation.value = result.explanation
  } catch (err) {
    error.value = err.message || '無法獲取解釋'
  } finally {
    loading.value = false
  }
}

async function onSendFollowUp(message) {
  try {
    chatError.value = null
    chatLoading.value = true
    chatMessages.value.push({ role: 'user', content: message })

    const history = chatMessages.value.map(m => ({ role: m.role, content: m.content }))
    const res = await lessonService.sendFollowUp({
      questionId: props.questionId,
      selectedIndices: props.selectedIndices,
      message,
      threadId: chatThreadId.value,
      stepKey: chatStepKey.value,
      history,
      explanation: explanation.value
    })

    chatThreadId.value = res.thread_id || chatThreadId.value
    const msgs = res.messages || []
    for (const m of msgs) {
      chatMessages.value.push({ role: m.role || 'assistant', content: m.content})
    }
  } catch (e) {
    chatError.value = e.message || '發送失敗'
  } finally {
    chatLoading.value = false
  }
}
</script>

<style>
/* Typography and layout */
.prose {
  color: #1f2937;
  line-height: 1.8;
}

.prose h3 {
  font-weight: 600;
  color: #111827;
  margin-bottom: 1em;
}

/* Content blocks */
.explanation-paragraph {
  margin-bottom: 1.5em;
  text-align: justify;
  hyphens: auto;
}

.explanation-paragraph:last-child {
  margin-bottom: 0;
}

.math-content :deep(.katex) {
  font-size: 1.1em;
  display: inline;
  text-align: left;
  vertical-align: middle;
  line-height: inherit;
}

.math-content :deep(.katex-inline) {
  display: inline;
  vertical-align: middle;
  white-space: nowrap;
  padding: 0 0.15em;
}

/* Fix line height and alignment */
.math-content {
  line-height: 2;
  word-spacing: 0.05em;
  text-align: justify;
  word-break: normal;
  overflow-wrap: break-word;
}

/* Lists */
.math-content ul {
  margin: 1em 0;
  padding-left: 1.5em;
  list-style-type: disc;
}

.math-content li {
  margin: 0.5em 0;
  line-height: 1.8;
}

/* Math text integration */
.explanation-paragraph :deep(.math-text) {
  display: inline;
  vertical-align: baseline;
  line-height: inherit;
  white-space: nowrap;
}

.explanation-paragraph :deep(.katex) {
  font-size: 1.1em;
  line-height: inherit;
  display: inline;
  text-align: left;
}

.explanation-paragraph :deep(.katex-html) {
  white-space: nowrap;
}
</style>
