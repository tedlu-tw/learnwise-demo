# KaTeX Rendering Guide

## Overview
KaTeX is used to render LaTeX mathematical expressions throughout the app (questions, options, and AI explanations).

## Current Components

### MathDisplay.vue (`/src/components/common/MathDisplay.vue`)
- Unified renderer for text and math.
- Features:
  - Inline ($...$) and display ($$...$$) math via KaTeX
  - **Bold** markdown parsing (**text** or __text__)
  - Bullet list detection (-, *, •, etc.) with Unicode normalization
  - Safe DOM construction (no innerHTML injection)
  - Cleans legacy wrappers and hidden unicode characters

### ExplanationPanel.vue
- Renders LLM-generated explanations.
- Parses step titles and bullet lists and feeds each line through `MathDisplay`.
- Shows disclaimer: 「AI 生成結果僅供參考。」

## Removed Legacy
- KatexRenderer.vue and MathText.vue have been superseded by `MathDisplay.vue`.
- Old backups/suffixed files are removed.

## Test Page (optional)
- `KatexTest.vue` remains as a manual test page and is routed at `/katex-test` for local verification.

## Usage Examples

Inline math in a sentence:
```vue
<MathDisplay text="The area is $A = \\pi r^2$." />
```

Display math block:
```vue
<MathDisplay text="$$\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}$$" />
```

Bullet list with math and bold:
```vue
<MathDisplay text="- **Key**: use $x^2$\n- Next: $\\frac{a}{b}$" />
```

## Notes
- Keep all math inline if possible; the backend prompt prefers single-$ inline math.
- The renderer normalizes NBSP, zero-width, and bidi marks to improve parsing.
