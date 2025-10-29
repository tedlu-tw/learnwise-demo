import os
import replicate
import itertools
from typing import Dict, Any, List
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

logger = logging.getLogger(__name__)

class LLMHelper:
    def __init__(self):
        self.api_token = os.environ.get('REPLICATE_API_TOKEN')
        if not self.api_token:
            raise ValueError("REPLICATE_API_TOKEN environment variable is not set")

    def generate_explanation(self, question_data: Dict[str, Any]) -> str:
        """Generate explanation for a math question using Replicate's Llama model."""
        try:
            # Format the prompt based on the question and answer data
            prompt = self._create_prompt(question_data)
            
            # Call Replicate API
            output = ""
            for event in replicate.stream(
                "meta/meta-llama-3-70b-instruct",
                input={
                    "top_k": 0,
                    "top_p": 0.9,
                    "prompt": prompt,
                    "max_tokens": 1024,
                    "temperature": 0.7,
                    "system_prompt": """你是一位專業的數學老師，負責指導學生理解他們的錯誤並提供詳細的解釋。

請嚴格遵循以下排版與數學格式規範：

1. 使用繁體中文回答。

2. 段落與標題分隔：
   - 每個步驟必須有明確的標題，標題必須使用粗體：**步驟N：標題**。
   - 標題必須獨立成行，且「標題前後都要各留一個空行」。
   - 其餘段落之間也必須以一個空行分隔。

3. 列表格式（重要）：
   - 務必以「條列式」呈現內容（每個重點一行）。
   - 列表項以 * 或 - 作為項目符號，示例：
     * 這是一個重點（行內公式如 $x^2+y^2=r^2$）
     * 這是另一個重點（保持行內 LaTeX）
   - 不要使用編號清單（1. 2. 3.），也不要使用多層巢狀清單。

4. 所有數學符號和公式必須使用 LaTeX 行內格式：
   - 一律使用單個 $ 作為行內公式，例如：$x + y = 10$。
   - 不要使用 $$ 或 \\[...\\]，長式公式也請用行內 $...$。
   - 座標點置於同一個 $ 中，如：$(3, 7)$。
   - 下標與上標：$x_{i}$、$x^{2}$；分數：$\\frac{a}{b}$；根號：$\\sqrt{n}$。
   - 集合：$\\mathbb{R}$；不等號：$\\lt, \\gt, \\leq, \\geq$；三角函數：$\\sin, \\cos$。
   - 方程組：$\\begin{cases} x+y=1 \\\\ x-y=2 \\end{cases}$（仍置於單一行內 $ 中）。

5. 文字強調：
   - 關鍵字可使用 **粗體** 強調（請勿使用其他 HTML 標籤）。

6. 禁止事項：
   - 禁止使用雙 $$、\\[...\\]、HTML 標籤、或任何非行內 $...$ 的數學格式。

範例結構（務必比照空行與條列）：

**步驟一：理解題目**

* 說明題目的已知條件與目標（保持行內公式，如 $f(x)$、$(a, b)$）。
* 指出可能造成混淆之處。

**步驟二：正確的解題思路**

* 依序列出解題步驟與理由，搭配行內 LaTeX（例如 $\\frac{-b \\pm \\sqrt{b^2-4ac}}{2a}$）。
* 說明關鍵性質或定理的使用方式。

**步驟三：錯誤分析**

* 為何原本選擇不正確。
* 常見迷思與澄清。

**步驟四：學習重點**

* 總結重要觀念（條列）。
* 類題提示（條列）。

請嚴格按照以上格式要求撰寫解答，切勿使用雙 $$ 或 \\[...\\] 格式。每段文字與每個步驟標題前後都必須有空行。""",
                    "presence_penalty": 1.15,
                }
            ):
                output += str(event)
            
            # Post-process the output to ensure proper formatting
            processed_output = self._process_explanation(output.strip())
            return processed_output
        except Exception as e:
            logger.error(f"Error generating explanation: {str(e)}")
            raise

    def generate_followup(self, ctx: Dict[str, Any]) -> str:
        """Generate a concise, step-focused follow-up reply based on prior explanation and user question."""
        try:
            prompt = self._create_followup_prompt(ctx)
            output = ""
            for event in replicate.stream(
                "meta/meta-llama-3-70b-instruct",
                input={
                    "top_k": 0,
                    "top_p": 0.9,
                    "prompt": prompt,
                    "max_tokens": 768,
                    "temperature": 0.7,
                    "system_prompt": """你是一位溫和且精煉的數學家教，正在針對學生的「追問」做對話式解答。

請遵守：
1) 使用繁體中文；2) 回覆短小精煉、切中重點；3) 只聚焦於學生此輪的問題（或指定的步驟），避免重覆完整解題；
4) 不要以條列式呈現，可以簡單分段，可用 **粗體** 標出關鍵字；
5) 公式一律使用單個 $ 的行內 LaTeX（禁止 $$ 與 \\[...\\]）；
6) 不要使用 **步驟N** 標題或新增章節標題；
7) 若需要示範，提供最小可行的簡短算式或例子即可。

回覆只包含內容本身，不要重覆學生的原話。""",
                    "presence_penalty": 1.0,
                }
            ):
                output += str(event)

            # Reuse formatting cleanup (lists, inline math normalization)
            processed = self._process_explanation(output.strip())
            return processed
        except Exception as e:
            logger.error(f"Error generating follow-up: {str(e)}")
            raise

    def _process_explanation(self, text: str) -> str:
        """Process the explanation to ensure proper formatting."""
        # Normalize newlines and strip trailing spaces
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        lines = text.split('\n')
        processed_lines: List[str] = []

        for i, raw in enumerate(lines):
            line = raw.strip()

            # Normalize block math to inline math
            if '$$' in line:
                line = line.replace('$$', '$')
            if '\\[' in line or '\\]' in line:
                line = line.replace('\\[', '$').replace('\\]', '$')

            # Insert blank line before step headers (if previous non-empty exists)
            if line.startswith('**步驟'):
                if processed_lines and processed_lines[-1] != '':
                    processed_lines.append('')
                processed_lines.append(line)
                # Ensure a blank line after the header as well
                processed_lines.append('')
                continue

            # Convert lines starting with bullets to bullet items (keep as-is; frontend renders lists)
            if line.startswith('* ') or line.startswith('- '):
                processed_lines.append(line)
                continue

            # Add spaces around inline math markers to avoid sticking to CJK words
            if '$' in line:
                line = line.replace('$(', ' $(').replace(')$', ')$ ')
                line = line.replace('$', ' $ ')  # simple spacing
                line = ' '.join(line.split())

            processed_lines.append(line)

        # Collapse multiple blank lines to single
        compact: List[str] = []
        for s in processed_lines:
            if s == '' and (not compact or compact[-1] == ''):
                continue
            compact.append(s)

        return '\n'.join(compact).strip()

    def _create_prompt(self, data: Dict[str, Any]) -> str:
        """Create a structured prompt for the LLM."""
        question_text = data.get('question_text', '')
        correct_indices = data.get('correct_indices', [])
        selected_indices = data.get('selected_indices', [])
        options = data.get('options', [])
        is_correct = data.get('is_correct', False)

        # Format selected and correct answers
        selected_options = [options[i] for i in selected_indices if i < len(options)]
        correct_options = [options[i] for i in correct_indices if i < len(options)]

        if is_correct:
            prompt = f"""
題目：{question_text}

您選擇了正確答案：{', '.join(selected_options)}

請提供詳細的解題思路，並遵循以下結構：
1. 首先說明您理解題目的關鍵點
2. 分步驟列出解題過程，每個步驟都要標明標題
3. 解釋為什麼這是正確的解法
4. 總結這題的重要觀念

請確保使用 LaTeX 格式書寫所有數學符號和公式
"""
        else:
            prompt = f"""
題目：{question_text}

您選擇了：{', '.join(selected_options)}
正確答案是：{', '.join(correct_options)}

請按照以下結構來説明：
步驟一：理解題目
- 分析題目的關鍵信息
- 指出可能造成混淆的地方

步驟二：正確的解題思路
- 詳細列出解題步驟
- 使用 LaTeX 格式表示所有公式

步驟三：錯誤分析
- 解釋為什麼原本的選擇不正確
- 指出可能的迷思概念

步驟四：學習重點
- 總結這題的關鍵概念
- 提供類似題目的解題技巧

請確保使用繁體中文回答，並適當分段排版。
"""
        return prompt

    def _create_followup_prompt(self, ctx: Dict[str, Any]) -> str:
        """Create a focused follow-up prompt using question, prior explanation, history, and the user's message."""
        question_text = ctx.get('question_text') or ''
        options = ctx.get('options') or []
        selected_indices = ctx.get('selected_indices') or []
        correct_indices = ctx.get('correct_indices') or []
        is_correct = ctx.get('is_correct', False)
        step_key = (ctx.get('follow_up') or {}).get('step_key')
        user_msg = (ctx.get('follow_up') or {}).get('message') or ''
        explanation_text = (ctx.get('explanation_text') or '')
        history = ctx.get('history') or []

        # Keep explanation short in prompt to save tokens
        expl_snippet = explanation_text.strip()
        if len(expl_snippet) > 1800:
            expl_snippet = expl_snippet[:1800] + "\n...（已截斷）"

        def fmt_msg(m):
            role = m.get('role', 'user')
            content = (m.get('content') or '').strip()
            return f"[{role}] {content}"
        history_block = "\n".join(fmt_msg(m) for m in history[-6:])  # last 6 turns

        def opt_str(indices):
            return ", ".join(options[i] for i in indices if i < len(options))

        selected_str = opt_str(selected_indices)
        correct_str = opt_str(correct_indices)
        focus = step_key or '本題'

        prompt = f"""
原始題目：{question_text}
已選擇：{selected_str if selected_str else '（無）'}
正確答案：{correct_str if correct_str else '（無）'}
是否答對：{'是' if is_correct else '否'}

原先的解釋（供參考）：
{expl_snippet}

對話歷史（近幾輪）：
{history_block if history_block else '（無）'}

學生的追問（焦點：{focus}）：
{user_msg}

請根據以上資訊，輸出「簡潔、條列式、重點式」的追問回覆（繁體中文、行內 $LaTeX$、禁止 $$）：
- 直接回答學生這一輪的疑問；
- 若涉及計算，給最小必要步驟；
- 建議常見錯誤的避錯提醒；
- 最後以一行「下一步建議：...」結尾。
"""
        return prompt
