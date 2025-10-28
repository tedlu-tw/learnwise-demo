<template>
  <span ref="katexElement" class="katex-container"></span>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import katex from 'katex'
import 'katex/dist/katex.min.css'

const props = defineProps({
  expression: {
    type: String,
    required: true
  }
})

const katexElement = ref(null)

const renderKatex = () => {
  if (!katexElement.value || !props.expression) return
  
  try {
    katex.render(props.expression, katexElement.value, {
      throwOnError: false,
      strict: false,
      maxSize: 500,
      maxExpand: 1000
    })
  } catch (error) {
    console.error('KaTeX error:', error)
    katexElement.value.textContent = props.expression
  }
}

onMounted(() => {
  renderKatex()
})

watch(() => props.expression, () => {
  renderKatex()
})
</script>

<style scoped>
.katex-container {
  display: inline-block;
  vertical-align: middle;
}

:deep(.katex) {
  font-size: 1.1em !important;
}
</style>
