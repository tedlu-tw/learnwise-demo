<template>
  <span class="math-text">
    <template v-for="(part, index) in parsedParts" :key="index">
      <KatexRenderer 
        v-if="part.isLatex" 
        :expression="part.content" 
        :display-mode="part.displayMode"
        class="inline-block"
      />
      <span v-else v-html="part.content"></span>
    </template>
  </span>
</template>

<script setup>
import { computed } from 'vue'
import KatexRenderer from './KatexRenderer.vue'

const props = defineProps({
  text: {
    type: String,
    required: true
  }
})

const parsedParts = computed(() => {
  if (!props.text) return []

  const parts = []
  let remaining = props.text
  
  // Regular expressions for different LaTeX delimiters
  const patterns = [
    { regex: /\$\$(.*?)\$\$/g, displayMode: true },   // $$...$$
    { regex: /\\\[(.*?)\\\]/g, displayMode: true },   // \[...\]
    { regex: /\$(.*?)\$/g, displayMode: false },      // $...$
    { regex: /\\\((.*?)\\\)/g, displayMode: false }   // \(...\)
  ]

  let lastIndex = 0
  const matches = []

  // Find all LaTeX matches
  patterns.forEach(pattern => {
    let match
    while ((match = pattern.regex.exec(props.text)) !== null) {
      matches.push({
        start: match.index,
        end: match.index + match[0].length,
        content: match[1],
        displayMode: pattern.displayMode,
        isLatex: true
      })
    }
  })

  // Sort matches by position
  matches.sort((a, b) => a.start - b.start)

  // Build parts array
  matches.forEach(match => {
    // Add text before the match
    if (match.start > lastIndex) {
      const textContent = props.text.substring(lastIndex, match.start)
      if (textContent) {
        parts.push({
          content: textContent,
          isLatex: false
        })
      }
    }
    
    // Add the LaTeX match
    parts.push(match)
    lastIndex = match.end
  })

  // Add remaining text
  if (lastIndex < props.text.length) {
    const textContent = props.text.substring(lastIndex)
    if (textContent) {
      parts.push({
        content: textContent,
        isLatex: false
      })
    }
  }

  // If no LaTeX found, return the whole text as regular content
  if (parts.length === 0) {
    parts.push({
      content: props.text,
      isLatex: false
    })
  }

  return parts
})
</script>

<style scoped>
.math-text {
  line-height: 1.5;
}

.math-text :deep(.katex) {
  font-size: 1em;
}

.math-text :deep(.katex-display) {
  margin: 0.5em 0;
}
</style>
