<template>
  <span 
    ref="katexElement" 
    class="katex-container"
    :class="{
      'block text-center my-4': displayMode,
      'inline-block align-middle mx-1': !displayMode
    }"
  ></span>
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
    katex.render(props.expression.trim(), katexElement.value, {
      displayMode: props.displayMode,
      throwOnError: props.throwOnError,
      strict: false,
      trust: true,
      output: 'html'
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
.katex-container:not(.block) {
  vertical-align: middle;
}

.katex {
  font-size: 1.1em;
  line-height: 1.2;
  text-indent: 0;
}
</style>
