<template>
  <span ref="katexElement" class="katex-container"></span>
</template>

<script setup>
import { ref, onMounted, watchEffect } from 'vue'
import katex from 'katex'
import 'katex/dist/katex.min.css'

const props = defineProps({
  expression: {
    type: String,
    required: true
  },
  displayMode: {
    type: Boolean,
    default: false
  },
  throwOnError: {
    type: Boolean,
    default: false
  }
})

const katexElement = ref(null)

const renderKatex = () => {
  if (!katexElement.value || !props.expression) return

  try {
    katex.render(props.expression, katexElement.value, {
      displayMode: props.displayMode,
      throwOnError: props.throwOnError,
      strict: false,
      trust: false
    })
  } catch (error) {
    console.warn('KaTeX rendering error:', error)
    katexElement.value.textContent = props.expression
  }
}

onMounted(() => {
  renderKatex()
})

watchEffect(() => {
  renderKatex()
})
</script>

<style scoped>
.katex-container {
  display: inline-block;
}
</style>
