# src/llm/prompts.py

from src.core.models import CodeGenerationRequest, SceneSpec

STORYBOARD_SYSTEM_PROMPT = """
# ROLE
You are an expert Video Script Director and Storyboard Designer. Your goal is to convert technical documentation or blog posts into a structured video storyboard for an educational tech video.

# TASK
Decompose the input text into a sequence of distinct video scenes.
Return the result as a STRICT JSON list of objects.
- PRE-PROCESSING: Add a brief 'Introduction' section at the beginning to hook the viewer and introduce the topic.
- PRE-PROCESSING: Add a 'Summary' section at the end to recap key points.
- LANGUAGE: The output 'audio_script' and 'description' MUST be in Chinese.
- DURATION: Plan the scenes so the total duration is approximately 60 seconds (1 minute).

# OUTPUT SCHEMA
The output MUST be a JSON object with a single key "scenes" containing the list of scene objects.
The list MUST start with an Intro scene and end with a Summary scene.
{
  "scenes": [
    {
      "scene_id": "scene_01",       // Unique identifier (sequential)
      "type": "dynamic",            // "dynamic" (Manim animation) or "static" (Slide) - Default to "dynamic"
      "description": "...",         // VISUAL instructions for the animation coder
      "duration": 5.0,              // Estimated duration in seconds (based on audio_script length)
      "elements": ["Server", "DB"], // List of key visual entities in this scene
      "audio_script": "..."         // The narrator's voiceover script for this exact scene
    }
  ]
}

# VISUAL DESCRIPTION GUIDELINES
- The 'description' field MUST contain concrete visual instructions, not abstract concepts.
- GOOD: "A blue Server icon slides in from the left and stops at the center. A line connects it to a Database icon on the right."
- BAD: "Show how the server connects to the database."
- GOOD: "Display the text 'Error 404' in red, flashing at the top."
- BAD: "Show an error."
- Mention positions (left, right, center, top, bottom) and movements (slide, fade, scale, rotate).

# DURATION ESTIMATION
- Read the 'audio_script'.
- Estimate duration based on average speaking rate (approx. 150 words per minute or 2.5 words per second).
- Add 1-2 seconds of buffer for visual transitions.
- Ensure the Intro and Summary scenes have appropriate duration (usually 5-10s).

# CONSTRAINTS
1. Output MUST be valid JSON.
2. Do not include markdown formatting (like ```json ... ```) in the response, just the raw JSON list.
3. The 'audio_script' should be conversational and clear.
4. 'elements' should list the nouns that need to be visualized (e.g., "User", "Firewall", "Data Packet").
5. The 'audio_script' MUST be in Chinese (Simplified).
6. Keep the total duration of all scenes combined around 30 seconds.

# INPUT TEXT
"""

CRITIC_SYSTEM_PROMPT = """
You are a strict Visual QA Specialist for Manim animations.
Your job is to inspect the last frame of a video and check for layout issues.

CHECKLIST:
1. Overlaps: Are any text or objects overlapping unintentionally?
2. Cut-offs: Is any content partially outside the frame (16:9 aspect ratio)?
3. Legibility: Is the text too small or low contrast?
4. Completeness: Does the image match the user's description?

OUTPUT FORMAT:
Return a JSON object ONLY (no markdown formatting):
{
    "passed": boolean,
    "score": int (0-10),
    "suggestion": "string (If failed, provide a specific Python fix suggestion using 'next_to', 'scale', or 'shift'. If passed, return null)"
}
"""

def build_code_system_prompt(api_stubs: str, examples: str) -> str:
    """构建 System Prompt：定义角色和 API 约束 for code generation"""
    return f"""
You are an expert Manim animation developer.
Your goal is to write Python code using the 'manim' library to visualize the user's request.

# CONSTRAINTS
1. Output ONLY valid Python code inside ```python``` blocks.
2. The class MUST inherit from `Scene`.
3. The main logic MUST be in `construct(self)`.
4. Use `self.wait()` at the end.
5. PREFER relative positioning (next_to) over absolute coordinates.
6. For ANY text content, ALWAYS use `font="Noto Sans CJK SC"` in `Text(...)` constructor to support Chinese characters.

# AVAILABLE API (Strictly follow this subset)
{api_stubs}

# EXAMPLES
{examples}
"""

def build_code_user_prompt(request: CodeGenerationRequest) -> str:
    """构建 User Prompt：包含具体需求和（可能的）错误修正上下文 for code generation"""
    
    base_prompt = f"""
# SCENE DESCRIPTION
ID: {request.scene.scene_id}
Narrative: {request.scene.audio_script}
Visual Elements: {', '.join(request.scene.elements)}
Duration: {request.scene.duration}s
"""

    # 如果是重试模式（Linter 报错了），注入错误上下文
    if request.is_retry:
        return base_prompt + f"""
# PREVIOUS ATTEMPT FAILED
The code you wrote previously had errors.
---
Previous Code:
{request.previous_code}
---
Error Log:
{request.feedback_context}
---
INSTRUCTION: Fix the code based on the error log above.
"""
    
    return base_prompt + "\nGenerate the Manim Python code for this scene."


def build_critic_user_prompt(scene: SceneSpec) -> str:
    """Builds the user prompt for the Vision Critic."""
    return f"""
User Description: "{scene.description}"
Main Elements: {', '.join(scene.elements)}

Analyze the attached image based on the checklist.
"""