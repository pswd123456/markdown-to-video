import json
import argparse
import os
from typing import List

from src.core.models import SceneSpec
from src.core.config import settings
from src.core.graph import ManimGraph
from src.components.assembler import Assembler
from src.components.rewriter import ScriptRewriter
from src.components.tts import TTSEngine
from src.utils.logger import logger, metrics


def load_script(file_path: str) -> List[SceneSpec]:
    """加载剧本文件，支持 JSON (直接加载) 或 MD/TXT (通过 LLM 重写)"""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".json":
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 假设 JSON 结构是: {"title": "...", "scenes": [...]}
            scenes_data = data.get("scenes", [])
            return [SceneSpec(**item) for item in scenes_data]
            
    elif ext in [".md", ".txt"]:
        logger.info(f"📄 Detected {ext} file. Invoking ScriptRewriter to generate storyboard...")
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        rewriter = ScriptRewriter()
        # rewrite() 返回 {"scenes": [dict, ...]}，且已通过 SceneSpec 校验
        result = rewriter.rewrite(content)
        
        # Save generated storyboard to output directory
        output_path = settings.OUTPUT_DIR / "storyboard.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        logger.info(f"💾 Saved generated storyboard to {output_path}")

        scenes_data = result.get("scenes", [])
        return [SceneSpec(**item) for item in scenes_data]
    
    else:
        raise ValueError(f"Unsupported file format: {ext}. Use .json, .md, or .txt")

def main():
    parser = argparse.ArgumentParser(description="Auto Manim Video Generator v2.2")
    parser.add_argument("script", help="Path to the storyboard JSON file or raw Markdown/Text draft")
    args = parser.parse_args()

    # 1. 加载数据
    try:
        scenes = load_script(args.script)
        logger.info(f"📂 Loaded script with {len(scenes)} scenes.")
    except Exception as e:
        logger.error(f"Failed to load script: {e}")
        return

    # 2. 初始化组件
    # 注意：ManimGraph 初始化开销较大，可以复用
    graph_app = ManimGraph().compile()
    tts = TTSEngine()
    assembler = Assembler()

    artifacts = []
    audio_paths = []

    # 3. 逐个场景处理
    for i, scene in enumerate(scenes):
        logger.info(f"\n🎬 Processing Scene {i+1}/{len(scenes)}: ID={scene.scene_id}")
        
        # A. 生成音频 (并行或串行均可，这里串行)
        audio_path = tts.generate(scene.audio_script, scene.scene_id)
        audio_paths.append(audio_path)
        
        # [Fix] Update scene duration based on actual audio length
        if audio_path:
             audio_dur = tts.get_duration(audio_path)
             if audio_dur > 0:
                 # Add small buffer (0.5s) to ensure audio finishes
                 old_dur = scene.duration
                 scene.duration = round(audio_dur + 0.5, 2)
                 logger.info(f"   ⏱️  Adjusted scene duration from {old_dur}s to {scene.duration}s based on audio.")
        
        # B. 运行 LangGraph 流水线 (Code -> Lint -> Render -> Critic)
        state_input = {
            "scene_spec": scene,
            "retries": 0,
            "visual_retries": 0,
            "code": None,
            "error_log": None,
            "artifact": None,
            "critic_feedback": None
        }
        
        try:
            final_state = graph_app.invoke(state_input)
            
            artifact = final_state.get("artifact")
            if artifact:
                artifacts.append(artifact)
                metrics.log_scene_finish(
                    scene.scene_id, 
                    success=True, 
                    retries=final_state.get("retries", 0),
                    vis_retries=final_state.get("visual_retries", 0)
                )
            else:
                logger.error(f"❌ Scene {scene.scene_id} Failed completely.")
                
                # --- Debug Info ---
                if final_state.get("error_log"):
                    logger.error(f"🔎 [Debug] Last Error Log:\n{final_state.get('error_log')}")
                
                if final_state.get("critic_feedback"):
                    logger.error(f"🔎 [Debug] Critic Feedback:\n{final_state.get('critic_feedback')}")

                logger.error(f"🔎 [Debug] Stats: Retries={final_state.get('retries')}, VisualRetries={final_state.get('visual_retries')}")
                # ------------------

                metrics.log_scene_finish(scene.scene_id, False, 0, 0)
                # 可以在这里决定是中断还是插入一个黑色占位视频
                
        except Exception as e:
            logger.error(f"❌ System Crash on scene {scene.scene_id}: {e}")

    # 4. 组装最终视频
    if artifacts:
        logger.info("\n🧩 Assembling final video...")
        try:
            assembler.assemble(artifacts, audio_paths, output_filename="full_movie.mp4")
        except Exception as e:
            logger.error(f"Assembly failed: {e}")
    else:
        logger.warning("No artifacts generated. Nothing to assemble.")

    # 5. 输出报告
    metrics.print_summary()
    metrics.save_report()

if __name__ == "__main__":
    main()