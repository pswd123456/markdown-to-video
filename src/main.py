import json
import argparse
import os
import asyncio
from typing import List

from src.core.models import SceneSpec
from src.core.config import settings
from src.core.graph import ParallelManimFlow
from src.components.assembler import Assembler
from src.components.rewriter import ScriptRewriter
from src.utils.logger import logger, metrics

async def load_script(file_path: str) -> List[SceneSpec]:
    """
    加载剧本文件 (异步操作)
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".json":
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            scenes_data = data.get("scenes", [])
            return [SceneSpec(**item) for item in scenes_data]
            
    elif ext in [".md", ".txt"]:
        logger.info(f"📄 Detected {ext} file. Invoking ScriptRewriter...")
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        rewriter = ScriptRewriter()
        result = await rewriter.rewrite(content)
        
        output_path = settings.OUTPUT_DIR / "storyboard.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        logger.info(f"💾 Saved storyboard to {output_path}")

        scenes_data = result.get("scenes", [])
        return [SceneSpec(**item) for item in scenes_data]
    
    else:
        raise ValueError(f"Unsupported file format: {ext}")

async def async_main():
    parser = argparse.ArgumentParser(description="Auto Manim Video Generator v3.0 (Parallel)")
    parser.add_argument("script", help="Path to the storyboard JSON or raw draft")
    args = parser.parse_args()

    # 1. 加载数据
    try:
        scenes = await load_script(args.script)
        logger.info(f"📂 Loaded script with {len(scenes)} scenes.")
    except Exception as e:
        logger.error(f"Failed to load script: {e}")
        return

    # 2. 初始化并行图
    logger.info("🚀 Initializing Parallel Workflow...")
    app = ParallelManimFlow().compile()
    
    # 3. 构造初始状态
    initial_state = {
        "scenes": scenes,
        "output_artifacts": [] # Reducer 的初始值
    }

    # 4. 执行并行图 (Map-Reduce)
    logger.info(f"⚡ Dispatching {len(scenes)} scenes in parallel...")
    try:
        # ainvoke 启动异步执行
        final_state = await app.ainvoke(initial_state)
        artifacts = final_state.get("output_artifacts", [])
        
        logger.info(f"✅ Workflow finished. Collected {len(artifacts)} artifacts.")
        
    except Exception as e:
        logger.error(f"❌ Parallel Execution Failed: {e}")
        return

    # 5. 组装 (Audio 路径需要从文件名推断，因为 TTS 现在是在 Graph 内部做的)
    # 假设 TTS 按照 scene_id 生成了文件
    if artifacts:
        logger.info("\n🧩 Assembling final video...")
        assembler = Assembler()
        
        # 按照场景顺序对 artifacts 排序 (并发执行可能导致乱序)
        # 建立 scene_id 到 index 的映射
        scene_order = {s.scene_id: i for i, s in enumerate(scenes)}
        artifacts.sort(key=lambda x: scene_order.get(x.scene_id, 999))
        
        # 收集对应的音频路径
        audio_paths = []
        for art in artifacts:
            audio_p = settings.OUTPUT_DIR / "audio" / f"{art.scene_id}.mp3"
            audio_paths.append(str(audio_p) if audio_p.exists() else None)

        try:
            assembler.assemble(artifacts, audio_paths, output_filename="full_movie.mp4")
        except Exception as e:
            logger.error(f"Assembly failed: {e}")
    else:
        logger.warning("No artifacts generated. Nothing to assemble.")

    # 6. 报告
    metrics.print_summary()
    metrics.save_report()

def main():
    # 异步入口封装
    asyncio.run(async_main())

if __name__ == "__main__":
    main()