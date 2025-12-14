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
Decompose the text into distinct video scenes based strictly on the content.
- Language: 'audio_script' and 'description' MUST be in Chinese (Simplified).
- **Duration Calculation**: Estimate the 'duration' strictly based on the Chinese character count of 'audio_script'. 
  - **Rule**: **1 second ≈ 4 Chinese characters**. 
  - Formula: `duration = max(2.0, len(audio_script) / 4.0)`
  - Example: 12 chars -> 3.0s; 20 chars -> 5.0s.

# OUTPUT SCHEMA
{
  "scenes": [
    {
      "scene_id": "unique_id_01",
      "type": "dynamic",
      "description": "...",         // VISUAL instructions: Describe specific shapes, colors, movements.
      "duration": 5.0,              // Calculated: len(audio_script) / 4
      "elements": ["Server", "DB"], // List specific visual entities to be drawn
      "audio_script": "..."         // Narrator script (Chinese)
    }
  ]
}

# FEW-SHOT EXAMPLES

## Example 1: Binary Search
[INPUT]
"二分查找通过将搜索区间分成两半来查找有序数组中的目标值。如果中间值小于目标，则在右半部分继续查找。"

[OUTPUT]
{
  "scenes": [
    {
      "scene_id": "01_split",
      "type": "dynamic",
      "description": "显示一个包含数字 1-10 的有序蓝色方块数组。数组中间的元素（数字5）变成黄色高亮。一个红色箭头指向它。目标值 '7' 显示在右侧。",
      "duration": 8.0,
      "elements": ["Sorted Array", "Arrow", "Target Label"],
      "audio_script": "二分查找通过将搜索区间分成两半来查找目标。首先检查中间的元素。如果它不是我们要找的，我们就把范围缩小一半。"
    },
    {
      "scene_id": "02_narrow",
      "type": "dynamic",
      "description": "左半部分（1-5）变灰并淡出。右半部分（6-10）放大并移动到中心。新的中间值（8）高亮。",
      "duration": 8.0,
      "elements": ["Remaining Array", "Highlight"],
      "audio_script": "因为目标值更大，我们丢弃左半部分，只在右边继续寻找，直到找到目标。"
    }
  ]
}

## Example 2: Client-Server Model
[INPUT]
"解释客户端-服务器模型。客户端发送请求，服务器处理并返回响应。"

[OUTPUT]
{
  "scenes": [
    {
      "scene_id": "cs_01_setup",
      "type": "dynamic",
      "description": "左侧显示一个小电脑图标（Client），右侧显示一个大服务器图标（Server）。中间是空白。",
      "duration": 5.0,
      "elements": ["Laptop Icon", "Server Icon"],
      "audio_script": "在网络世界中，客户端和服务器是两个核心角色。"
    },
    {
      "scene_id": "cs_02_request",
      "type": "dynamic",
      "description": "一个黄色的信封（Request）从左侧电脑飞向右侧服务器。服务器图标轻微震动表示接收。",
      "duration": 7.0,
      "elements": ["Laptop", "Server", "Envelope"],
      "audio_script": "客户端发起请求，就像寄出一封信，告诉服务器它需要什么数据。"
    },
    {
      "scene_id": "cs_03_response",
      "type": "dynamic",
      "description": "服务器上方出现齿轮转动动画（Processing）。然后一个绿色的包裹（Response）飞回左侧。",
      "duration": 5.5,
      "elements": ["Server", "Gears", "Package"],
      "audio_script": "服务器处理请求后，将结果打包成响应，发送回客户端。"
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

# INSTRUCTION
1. the background should be always remaining black

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
    return f"""
# ROLE
You are a Senior Manim Technical Lead.
Your goal is to fix errors by enforcing **Robust Layouts**.

# KNOWLEDGE BASE
{api_stubs}

# STRATEGY: HOW TO FIX VISUAL BUGS
When you see a Visual Issue (Overlap/Cut-off), standard "shifting" is BANNED. You MUST refactor the code to use Relative Positioning.

1. **The "Anchor" Strategy**:
   - Identify a central object (usually the most important one) as the **Anchor**.
   - Position all other objects relative to the Anchor using `next_to` or `align_to`.
   - *Example*: Instead of `text.move_to(RIGHT*3)`, use `text.next_to(box, RIGHT, buff=1.0)`.

2. **The "Group & Arrange" Strategy (Best for Lists/Flows)**:
   - If multiple items overlap, put them in a `VGroup` and use `.arrange()`.
   - *Code*: `VGroup(item1, item2, item3).arrange(DOWN, buff=0.5, center=True)`

3. **The "Safety Margin" Strategy (For Cut-offs)**:
   - If an element is cut off at the edge, DO NOT just move it. **Scale it down**.
   - *Code*: `group.scale_to_fit_width(config.frame_width - 1.0)`

# OUTPUT INSTRUCTIONS
1. Analyze the `Visual Report` to find WHICH spatial relationship is broken.
2. Provide Python code snippets that REPLACE the absolute positioning with `next_to`, `arrange`, or `scale`.
3. Be explicit: "Replace line X with..."
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

# LAYOUT SAFETY PROTOCOLS (STRICT)
1. **Safe Area**: Keep all critical content within X=[-6, 6] and Y=[-3.5, 3.5].
2. **Text Scaling**: Avoid fixed font sizes like `font_size=60` if text is long. Use `.scale_to_fit_width()` if necessary.
3. **Collision Avoidance**: 
   - When creating a label for a shape, ALWAYS use `label.next_to(shape, DIRECTION)`.
   - NEVER manually calculate coordinates like `shape.get_center() + UP*2` unless necessary.

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
    return """
# ROLE
You are a strict Visual QA Specialist. 
Inspect the image for Layout Collisions and Boundary Violations.

# OUTPUT SCHEMA (JSON)
{
    "passed": boolean,
    "score": int (0-10),
    "issues": [
        {
            "object": "Label 'Server'",
            "issue_type": "overlap" | "cutoff" | "small",
            "description": "The label covers the bottom-right of the box.",
            "fix_hint": "move_down" | "move_left" | "scale_down"  // Directional hint
        }
    ],
    "suggestion": "Summarized instructions for the fixer..."
}

# CRITICAL RULES
1. **Be Specific**: Don't say "Overlap". Say "Object A overlaps the Top-Right corner of Object B".
2. **Safe Zone**: Content must stay within X: [-6.5, 6.5], Y: [-3.5, 3.5].
3. **Legibility**: If text is on top of a complex shape, it fails unless it has a background.
"""

def build_critic_user_prompt(scene: SceneSpec) -> str:
    return f"""
Scene Description: "{scene.description}"
Visual Elements: {', '.join(scene.elements)}

Analyze the attached image frame.
"""