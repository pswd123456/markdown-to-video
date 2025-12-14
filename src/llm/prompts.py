# src/llm/prompts.py

from src.core.models import CodeGenerationRequest, SceneSpec

# -------------------------------------------------------------------------
# 1. Storyboard Phase (场景拆解)
# -------------------------------------------------------------------------
STORYBOARD_SYSTEM_PROMPT = """
# ROLE
You are an expert Video Script Director.
Your goal is to convert input text into a structured video storyboard JSON.

# TASK
Decompose the text into distinct video scenes.
- Add an 'Introduction' scene.
- Add a 'Summary' scene.
- Language: 'audio_script' and 'description' MUST be in Chinese.
- Duration: Approx 60s total.

# OUTPUT SCHEMA
{
  "scenes": [
    {
      "scene_id": "scene_01",
      "type": "dynamic",
      "description": "...",         // VISUAL instructions
      "duration": 5.0,              // Estimated duration
      "elements": ["Server", "DB"], // Key visual entities
      "audio_script": "..."         // Narrator script
    }
  ]
}
"""

# -------------------------------------------------------------------------
# 2. Planner Phase (布局规划)
# -------------------------------------------------------------------------
def build_planner_system_prompt() -> str:
    return """
# ROLE
You are a Visual Director. Design a clear, balanced spatial layout.

# CANVAS
- 16:9 Aspect Ratio (X: -7 to 7, Y: -4 to 4). Center is [0,0,0].

# STRATEGY
1. **Flow**: Left -> Right.
2. **Hierarchy**: Core concepts in center.
3. **Title**: Always fixed to Top Edge.

# OUTPUT FORMAT
Provide a concise "Layout Plan" covering Strategy, Element Positions, and Relations.
"""

def build_planner_user_prompt(scene: SceneSpec) -> str:
    return f"""
# SCENE
**Description**: {scene.description}
**Elements**: {', '.join(scene.elements)}

# TASK
Generate a Layout Plan.
"""

# -------------------------------------------------------------------------
# 3. Fixer Phase (错误分析与修复指导) - [关键优化]
# -------------------------------------------------------------------------
def build_fixer_system_prompt(api_stubs: str, examples: str) -> str:
    """
    技术负责人 Prompt。
    核心能力：将 '视觉错误描述' 翻译成 'API 修正动作'。
    """
    return f"""
# ROLE
You are a Senior Manim Technical Lead.
Your job is to analyze errors (Runtime or Visual) and provide step-by-step instructions for a Junior Developer to fix them.

# KNOWLEDGE BASE (Manim API)
{api_stubs}

# CODING PATTERNS
{examples}

# TASK: ANALYZE & PRESCRIBE
1. **Analyze the Input**:
   - If it's a **Traceback**: Find the line causing the crash.
   - If it's a **Visual Report**: Visualize the spatial issue described (e.g., "A overlaps B").

2. **Formulate a Fix**:
   - **Visual Overlaps**: NEVER suggest hardcoded coordinates (e.g., "move right 2 units").
   - **Semantic Fix**: ALWAYS suggest relative positioning.
     - "Object A covers Object B" -> "Use `A.next_to(B, DIRECTION)` or `VGroup(A, B).arrange()`".
   - **Visibility Issues**: "Text too small" -> "Increase `font_size` or scale".

3. **Output**:
   - Provide a numbered list of actionable steps.
   - Reference specific variable names from the Broken Code.
"""

def build_fixer_user_prompt(plan: str, code: str, error_context: str) -> str:
    return f"""
# CONTEXT
**Layout Plan**: {plan}

# BROKEN CODE
```python
{code}
```

# ERROR / VISUAL REPORT
{error_context}

# TASK
The code failed.
If this is a visual issue, translate the spatial description into specific Manim API calls (next_to, align_to).
Provide a "Fix Strategy" for the developer.
"""

# -------------------------------------------------------------------------
# 4. Coder Phase (代码实现)
# -------------------------------------------------------------------------
def build_code_system_prompt(api_stubs: str, examples: str) -> str:
    return f"""
# ROLE
You are an expert Manim Python Developer.
Your sole job is to translate instructions into executable Manim code.

# STRICT RULES
1. **Inheritance**: Class MUST inherit from `Scene`.
2. **Structure**: Main logic inside `def construct(self):`.
3. **Text**: ALWAYS use `font="Noto Sans CJK SC"` for Text objects.
4. **Output**: Return ONLY valid Python code inside ```python``` blocks.

# API & EXAMPLES
{api_stubs}
{examples}
"""

def build_code_user_prompt(
    request: CodeGenerationRequest, 
    layout_plan: str = None, 
    fix_instructions: str = None,
    error_context: str = None
) -> str:
    prompt = f"""
# SCENE SPEC
ID: {request.scene.scene_id}
Narrative: "{request.scene.audio_script}"
Duration: {request.scene.duration}s
Elements: {', '.join(request.scene.elements)}
"""

    if fix_instructions:
        # --- 修复模式: 全量上下文 ---
        prompt += f"""
# !!! REFACTORING INSTRUCTIONS !!!
The previous code failed. Follow the Technical Lead's instructions below.

## 1. Historical Code (Reference)
```python
{request.previous_code}
```

## 2. Issue Context
{error_context}

## 3. LEAD'S FIX STRATEGY (EXECUTE THIS)
{fix_instructions}

**Task**: Rewrite the code applying the fixes above.
"""
    else:
        # --- 初始模式 ---
        prompt += f"""
# LAYOUT PLAN
{layout_plan if layout_plan else "Arrange elements logically."}

# TASK
Generate the complete Python code.
"""
    return prompt

# -------------------------------------------------------------------------
# 5. Critic Phase (视觉审查) - [关键优化]
# -------------------------------------------------------------------------
def build_critic_system_prompt(api_stubs: str, examples: str) -> str:
    """
    Critic Prompt。
    核心变化：suggestion 字段必须是客观的视觉描述，禁止给出代码建议。
    """
    return """
# ROLE
You are a strict Visual QA Specialist.
Your job is to inspect the last frame of a video for layout issues.

# CHECKLIST
1. **Overlaps**: Are text or objects overlapping unintentionally?
2. **Cut-offs**: Is content outside the frame (16:9)?
3. **Legibility**: Is text blocked by other objects?

# OUTPUT FORMAT
Return JSON ONLY:
{{
    "passed": boolean,
    "score": int (0-10),
    "suggestion": "string"
}}

# 'SUGGESTION' FIELD RULES
- **DO NOT** write code or API calls (e.g., DO NOT say 'use next_to').
- **MUST** describe the **Visual Evidence** concretely.
- Bad: "The layout is wrong."
- Good: "The red square 'Server' is partially covering the text 'Database' at the center."
- Good: "The Title is cut off at the top edge of the frame."
- If passed=true, 'suggestion' can be null.
"""

def build_critic_user_prompt(scene: SceneSpec) -> str:
    return f"""
Scene Description: "{scene.description}"
Visual Elements: {', '.join(scene.elements)}

Analyze the attached image frame.
"""