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

請遵循以下格式要求：
1. 使用繁體中文回答
2. 將解釋分成清楚的段落，使用換行分隔
3. 所有數學符號和公式必須使用 LaTeX 格式，並確保：
   - 使用單個 $ 符號包圍簡單行內公式，如：$x + y = 10$
   - 使用雙 $$ 符號包圍複雜公式，如：$$\\frac{x^2 + y^2}{2}$$
   - 座標點必須使用括號並在同一個 $ 內，如：$(3, 7)$，不要分開寫
   - 變數名使用 \\_，如：$x_{\\text{center}}$, $y_{\\text{max}}$
   - 複雜下標使用 \\text，如：$x_{\\text{circumcenter}}$
   - 分數使用 \\frac{分子}{分母}，如：$\\frac{1}{2}$
   - 乘法使用 \\times 或 \\cdot，如：$2 \\times 3$
   - 次方使用 ^，如：$x^2$
   - 根號使用 \\sqrt{}，如：$\\sqrt{16}$
   - 集合使用 \\mathbb{}，如：$\\mathbb{R}$, $\\mathbb{Z}$
   - 不等號使用 \\lt, \\gt, \\leq, \\geq，如：$x \\lt 0$
   - 希臘字母使用 \\alpha, \\beta 等，如：$\\alpha + \\beta$
   - 三角函數使用 \\sin, \\cos 等，如：$\\sin(x)$
4. 使用**粗體文字**來標示重要觀念或關鍵字
5. 每個步驟都要有明確的標題，使用**步驟標題**格式
6. 使用適當的分段和空行來區分不同部分
7. 對於多行或複雜的數學公式，使用 $$...$$：
   $$
   x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}
   $$

範例格式：
**步驟一：理解題目**
在這個問題中，我們需要找到點 $(x_0, y_0)$ 滿足方程式 $ax + by = c$ 其中 $a,b,c \\in \\mathbb{R}$。

數學公式：
$$
\\begin{cases}
x_{\\text{center}} = \\frac{x_1 + x_2}{2} \\\\
y_{\\text{center}} = \\frac{y_1 + y_2}{2}
\\end{cases}
$$

請嚴格按照以上格式要求撰寫解答。""",
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

    def _process_explanation(self, text: str) -> str:
        """Process the explanation to ensure proper formatting."""
        # Split into lines and clean up
        lines = text.split('\n')
        processed_lines = []
        in_math_block = False
        math_buffer = []
        
        for line in lines:
            line = line.strip()
            
            # Handle empty lines
            if not line:
                if math_buffer:
                    # If we have a math buffer, don't add empty line
                    continue
                processed_lines.append('')
                continue
            
            # Handle math blocks
            if line.startswith('$$') or line.endswith('$$'):
                if not in_math_block:
                    # Start of math block
                    in_math_block = True
                    math_buffer = [line]
                else:
                    # End of math block
                    math_buffer.append(line)
                    # Join and clean up math block
                    math_content = '\n'.join(math_buffer)
                    # Ensure proper spacing around math blocks
                    processed_lines.extend(['', math_content, ''])
                    math_buffer = []
                    in_math_block = False
                continue
            
            # Collect lines in math block
            if in_math_block:
                math_buffer.append(line)
                continue
            
            # Fix inline math formatting issues
            if '$' in line:
                # Fix coordinate pairs
                line = line.replace('$(', ' $(').replace(')$', ')$ ')
                # Add spaces around inline math
                line = line.replace('$', ' $ ').replace('  $  ', ' $ ')
                # Clean up excess spaces
                line = ' '.join(line.split())
            
            # Add proper step formatting
            if line.startswith('**步驟'):
                line = f"\n{line}" if processed_lines else line
            
            processed_lines.append(line)
        
        # Join lines and clean up
        text = '\n'.join(processed_lines)
        # Remove multiple consecutive empty lines
        text = '\n'.join(line for line, _ in itertools.groupby(text.split('\n')))
        return text

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
