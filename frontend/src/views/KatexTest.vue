<template>
  <div class="max-w-4xl mx-auto p-6">
    <h1 class="text-3xl font-bold mb-6">KaTeX Test Page</h1>
    
    <div class="space-y-6">
      <div class="bg-white p-4 rounded-lg shadow">
        <h2 class="text-xl font-semibold mb-3">Inline Math</h2>
        <p>The quadratic formula is: <MathText text="$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$" /></p>
        <p>The area of a circle is: <MathText text="$A = \\pi r^2$" /></p>
      </div>

      <div class="bg-white p-4 rounded-lg shadow">
        <h2 class="text-xl font-semibold mb-3">Display Math</h2>
        <div class="text-center">
          <MathText text="$$\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}$$" />
        </div>
        <div class="text-center mt-4">
          <MathText text="$$f(x) = \\sum_{n=0}^{\\infty} \\frac{f^{(n)}(a)}{n!}(x-a)^n$$" />
        </div>
      </div>

      <div class="bg-white p-4 rounded-lg shadow">
        <h2 class="text-xl font-semibold mb-3">Mixed Content</h2>
        <p>
          <MathText text="To solve the equation $x^2 - 5x + 6 = 0$, we can factor it as $(x-2)(x-3) = 0$, giving us solutions $x = 2$ and $x = 3$." />
        </p>
      </div>

      <div class="bg-white p-4 rounded-lg shadow">
        <h2 class="text-xl font-semibold mb-3">Question Preview</h2>
        <div class="border-l-4 border-blue-500 pl-4">
          <h3 class="font-medium mb-2">Sample Math Question:</h3>
          <MathText text="What is the derivative of $f(x) = x^3 + 2x^2 - 5x + 1$? <br>$f(x) = x^3 + 2x^2 - 5x + 1$?" />
          <div class="mt-3 space-y-2">
            <div class="flex items-center space-x-2">
              <input type="radio" name="test-question" value="0" />
              <MathText text="$3x^2 + 4x - 5$" />
            </div>
            <div class="flex items-center space-x-2">
              <input type="radio" name="test-question" value="1" />
              <MathText text="$x^4 + 2x^3 - 5x^2 + x$" />
            </div>
            <div class="flex items-center space-x-2">
              <input type="radio" name="test-question" value="2" />
              <MathText text="$3x^2 + 2x - 5$" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="mt-8 text-center">
      <router-link to="/session" class="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700">
        Go to Learning Session
      </router-link>
    </div>
  </div>
</template>

<script setup>
import MathText from '@/components/common/MathText.vue'
</script>
