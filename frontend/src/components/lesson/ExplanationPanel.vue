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
        <div class="text-lg font-medium text-gray-700 border-b pb-2">詳細解釋</div>
        <div class="prose prose-sm max-w-none bg-white p-4 rounded-lg shadow-sm overflow-x-auto">
          <template v-for="(section, index) in formattedExplanation" :key="index">
            <div v-if="section.type === 'step'" class="mb-6">
              <h3 class="font-bold text-lg text-gray-800 mb-3" v-html="section.title"></h3>
              <div class="pl-4 space-y-2">
                <div v-for="(content, contentIndex) in section.contents" :key="contentIndex" :class="{ 'equation-container': content.type === 'math' }">
                  <template v-if="content.type === 'math' || content.type === 'inline-math'">
                    <MathText :text="content.text" :class="{ 'inline': content.type === 'inline-math' }" />
                  </template>
                  <div v-else class="text-gray-800 content-text" v-html="content.text"></div>
                </div>
              </div>
            </div>
            <div v-else class="mb-3" :class="{ 'equation-container': section.type === 'math' || section.type === 'inline-math' }">
              <template v-if="section.type === 'math' || section.type === 'inline-math'">
                <MathText :text="section.text" :class="{ 'inline': section.type === 'inline-math' }" />
              </template>
              <div v-else class="text-gray-800 content-text" v-html="section.text"></div>
            </div>
          </template>
        </div>
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
</template>

<script setup>
import { ref, computed } from 'vue'
import MathText from '@/components/common/MathText.vue'
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

// Add validation computed property
const isValid = computed(() => {
  const valid = Boolean(props.questionId && Array.isArray(props.selectedIndices))
  console.log('ExplanationPanel validation:', {
    questionId: props.questionId,
    selectedIndices: props.selectedIndices,
    validationResult: valid,
    questionIdType: typeof props.questionId,
    selectedIndicesType: typeof props.selectedIndices,
    hasQuestionId: Boolean(props.questionId),
    isArray: Array.isArray(props.selectedIndices)
  })
  return valid
})

function processContent(text) {
  const parts = []
  let buffer = ''
  let inMath = false
  let currMathType = null
  let displayMathBuffer = []
  let inDisplayMath = false
  let inList = false
  let listItems = []

  // Helper to add buffered content
  const addBuffer = () => {
    if (buffer) {
      if (currMathType === 'inline') {
        // For inline math, mark it specifically as inline math
        parts.push({
          type: 'inline-math',
          text: `$${buffer}$`
        })
      } else if (currMathType === 'display') {
        // For display math, add as a separate block
        parts.push({
          type: 'math',
          text: `$$${buffer}$$`
        })
      } else {
        // For regular text, process bold and combine with previous text if possible
        const processedText = buffer.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        const lastPart = parts[parts.length - 1]
        if (lastPart && lastPart.type === 'text') {
          lastPart.text += processedText
        } else {
          parts.push({
            type: 'text',
            text: processedText
          })
        }
      }
      buffer = ''
    }
  }

  const lines = text.split('\n')
  for (let lineIndex = 0; lineIndex < lines.length; lineIndex++) {
    const line = lines[lineIndex]
    
    // Process each character in the line
    for (let i = 0; i < line.length; i++) {
      const char = line[i]
      const nextChar = line[i + 1]

      if (!inDisplayMath && char === '$' && nextChar === '$') {
        // Start of display math block
        addBuffer()
        inDisplayMath = true
        inMath = true
        currMathType = 'display'
        i++ // Skip next $
        continue
      } else if (inDisplayMath && char === '$' && nextChar === '$') {
        // End of display math block
        addBuffer()
        inDisplayMath = false
        inMath = false
        currMathType = null
        i++ // Skip next $
        continue
      } else if (!inDisplayMath && char === '$' && !inMath && !nextChar?.match(/[$\\]/)) {
        // Start of inline math
        addBuffer()
        inMath = true
        currMathType = 'inline'
        continue
      } else if (!inDisplayMath && char === '$' && inMath && currMathType === 'inline') {
        // End of inline math
        addBuffer()
        inMath = false
        currMathType = null
        continue
      } else if (char === '\\' && nextChar === '$') {
        // Handle escaped $
        buffer += '$'
        i++ // Skip next $
      } else {
        buffer += char
      }
    }

    // Handle end of line
    if (inDisplayMath) {
      buffer += '\n'
    } else if (buffer) {
      addBuffer()
    }
  }

  // Add any remaining content
  if (buffer) {
    addBuffer()
  }

  return parts
}

// Format explanation text into structured sections
const formattedExplanation = computed(() => {
  if (!explanation.value) return []

  const sections = []
  let currentStep = null

  // Split into paragraphs first
  const paragraphs = explanation.value.split(/\n\s*\n/).filter(p => p.trim())

  for (const paragraph of paragraphs) {
    // Detect step headers - matches both Chinese numerals and Arabic numbers
    const stepMatch = paragraph.match(/^\*\*(步驟[零一二三四五六七八九十\d]+：.*?)\*\*/)

    if (stepMatch) {
      if (currentStep) {
        sections.push(currentStep)
      }
      currentStep = {
        type: 'step',
        title: stepMatch[1],
        contents: []
      }
    } else if (currentStep) {
      // Process paragraph and merge adjacent text parts
      const processed = mergeAdjacentTextParts(processContent(paragraph))
      currentStep.contents.push(...processed)
    } else {
      // Process standalone paragraph and merge adjacent text parts
      const processed = mergeAdjacentTextParts(processContent(paragraph))
      sections.push(...processed)
    }
  }

  // Add the last step if exists
  if (currentStep) {
    sections.push(currentStep)
  }

  return sections
})

// Helper function to process bullet points
function processBulletPoints(text) {
  const lines = text.split('\n')
  const bulletPattern = /^\s*[\*\-•]\s+(.+)$/
  
  // Check if it's a bullet list
  if (!lines.some(line => bulletPattern.test(line))) {
    return text
  }

  // Process bullet points
  let formattedList = '<ul>'
  for (const line of lines) {
    const match = line.match(bulletPattern)
    if (match) {
      formattedList += `\n  <li>${match[1]}</li>`
    }
  }
  formattedList += '\n</ul>'
  
  return formattedList
}

// Helper function to merge adjacent text parts
function mergeAdjacentTextParts(parts) {
  return parts.reduce((acc, part) => {
    const lastPart = acc[acc.length - 1]
    
    if (lastPart && lastPart.type === 'text' && part.type === 'text') {
      // Check for bullet points in the combined text
      const combinedText = `${lastPart.text}\n${part.text}`
      const bulletPattern = /^[\*\-•]\s+/m
      
      if (bulletPattern.test(combinedText)) {
        // Process as bullet points
        lastPart.text = processBulletPoints(combinedText)
      } else {
        // Preserve line breaks for normal text
        lastPart.text = combinedText.trim()
      }
    } else if (part.type === 'inline-math') {
      // Always keep inline math as separate parts
      acc.push(part)
    } else {
      acc.push(part)
    }
    return acc
  }, [])
}

async function getExplanation() {
  console.log('Getting explanation for question:', props.questionId)
  loading.value = true
  error.value = null
  
  try {
    const result = await lessonService.getExplanation(props.questionId, props.selectedIndices)
    console.log('Got explanation result:', result)
    explanation.value = result.explanation
  } catch (err) {
    console.error('Error getting explanation:', err)
    error.value = err.message || '無法獲取解釋'
  } finally {
    loading.value = false
  }
}
</script>

<style>
.prose {
  color: #1f2937;
  line-height: 1.625;
}

.prose p {
  margin-bottom: 1rem;
}

.prose p:last-child {
  margin-bottom: 0;
}

.prose h1,
.prose h2,
.prose h3 {
  font-weight: 600;
  color: #111827;
  margin-bottom: 0.75em;
  margin-top: 1.5em;
}

.prose h3:first-child {
  margin-top: 0;
}

/* Enhanced content formatting */
.content-text {
  white-space: pre-line; /* Preserve line breaks */
  line-height: 1.6;
}

/* Bullet point styling */
.content-text ul {
  margin: 1rem 0;
  padding-left: 1.5rem;
  list-style-type: disc;
}

.content-text li {
  margin: 0.5rem 0;
  line-height: 1.6;
}

/* Equation container */
.equation-container {
  max-width: 100%;
  overflow-x: auto;
  padding: 0.5rem 0;
  scrollbar-width: thin;
}

/* Ensure inline math flows with text */
.inline {
  display: inline-block !important;
  margin: 0 0.2em;
  vertical-align: baseline;
}

.katex-display {
  overflow-x: auto;
  overflow-y: hidden;
  padding: 0.5em 0;
  margin: 0.5em 0;
}

/* Equation scrollbar styling */
.equation-container::-webkit-scrollbar {
  height: 6px;
}

.equation-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.equation-container::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 3px;
}

.equation-container::-webkit-scrollbar-thumb:hover {
  background: #666;
}

/* Display math styling */
.equation-container:has(.katex-display) {
  margin: 1rem 0;
  text-align: center;
}

/* Ensure inline math doesn't break text flow */
.katex-inline {
  display: inline-block;
  vertical-align: middle;
}
</style>
