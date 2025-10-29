<template>
  <transition name="slide">
    <div v-if="open" class="fixed inset-0 z-50 flex">
      <!-- Backdrop -->
      <div class="fixed inset-0 bg-black/30" @click="emit('close')"></div>

      <!-- Drawer -->
      <div class="relative ml-auto h-full w-full max-w-md bg-white shadow-xl flex flex-col">
        <div class="flex items-center justify-between p-4 border-b">
          <h2 class="text-lg font-semibold">追問對話</h2>
          <button class="text-gray-500 hover:text-gray-700" @click="emit('close')">✕</button>
        </div>

        <!-- Messages -->
        <div ref="scrollArea" class="flex-1 overflow-y-auto p-4 space-y-4">
          <div v-if="!messages || messages.length === 0" class="text-sm text-gray-500">
            針對上面的解釋提出你的問題吧～
          </div>
          <div v-for="(m, i) in messages" :key="i" class="flex" :class="m.role === 'user' ? 'justify-end' : 'justify-start'">
            <div :class="[
              'max-w-[80%] rounded-lg px-3 py-2 shadow',
              m.role === 'user' ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-800'
            ]">
              <MathDisplay :text="m.content" />
            </div>
          </div>
          <div v-if="loading" class="text-sm text-gray-500">正在思考…</div>
          <div v-if="error" class="text-sm text-red-600">{{ error }}</div>
        </div>

        <!-- Input -->
        <form class="p-3 border-t flex items-end space-x-2" @submit.prevent="onSendInternal">
          <textarea
            v-model="draft"
            class="flex-1 border rounded-md p-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            rows="2"
            placeholder="請輸入問題（支援粗體與 LaTeX，如 $x^2$）"
          ></textarea>
          <button
            type="submit"
            :disabled="!draft.trim() || loading"
            class="px-3 py-2 bg-indigo-600 text-white rounded-md disabled:opacity-50"
          >送出</button>
        </form>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, watch, onMounted, nextTick } from 'vue'
import MathDisplay from '@/components/common/MathDisplay.vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  messages: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  error: { type: String, default: null }
})

const emit = defineEmits(['close', 'send'])

const draft = ref('')
const scrollArea = ref(null)

function scrollToBottom() {
  nextTick(() => {
    if (scrollArea.value) {
      scrollArea.value.scrollTop = scrollArea.value.scrollHeight
    }
  })
}

watch(() => props.messages, scrollToBottom, { deep: true })
watch(() => props.open, (v) => { if (v) scrollToBottom() })

function onSendInternal() {
  const text = draft.value.trim()
  if (!text) return
  emit('send', text)
  draft.value = ''
}
</script>

<style>
.slide-enter-active, .slide-leave-active { transition: transform 0.2s ease, opacity 0.2s ease; }
.slide-enter-from, .slide-leave-to { transform: translateX(100%); opacity: 0; }
</style>
