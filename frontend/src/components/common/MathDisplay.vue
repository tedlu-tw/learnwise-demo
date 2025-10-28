<template>
  <span class="math-text" ref="container"></span>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import katex from 'katex'
import 'katex/dist/katex.min.css'

const props = defineProps({
  text: {
    type: String,
    required: true
  }
})

const container = ref(null)

const renderContent = () => {
  if (!container.value || !props.text) return
  
  try {
    const parts = []
    const segments = props.text.split(/(\$[^$]+\$)/g)
    
    segments.forEach(segment => {
      if (!segment) return
      
      const span = document.createElement('span')
      
      if (segment.startsWith('$') && segment.endsWith('$')) {
        const math = segment.slice(1, -1).trim()
        if (math) {
          span.className = 'math-inline'
          try {
            katex.render(math, span, {
              throwOnError: false,
              displayMode: false,
              maxSize: 500,
              maxExpand: 1000
            })
          } catch (err) {
            console.error('KaTeX error:', err)
            span.textContent = math
          }
        }
      } else {
        span.innerHTML = segment.replace(/\n/g, '<br>')
      }
      
      parts.push(span)
    })
    
    container.value.innerHTML = ''
    parts.forEach(part => container.value.appendChild(part))
  } catch (error) {
    console.error('Render error:', error)
    container.value.textContent = props.text
  }
}

onMounted(renderContent)

watch(() => props.text, renderContent)
</script>

<style>
.math-text {
  display: inline;
}

.math-inline {
  display: inline-block;
  vertical-align: middle;
  margin: 0 0.15em;
}

.katex {
  text-indent: 0;
  font-size: 1.1em !important;
}
</style>
