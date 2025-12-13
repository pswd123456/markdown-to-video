from src.core.graph import ManimGraph
from src.core.models import SceneSpec

def main():
    # 1. 初始化图
    graph_app = ManimGraph().compile()
    
    # (可选) 生成流程图的可视化 (需要安装 pygraphviz，这里先略过)
    # print(graph_app.get_graph().draw_ascii())

    # 2. 准备输入数据
    test_scene = SceneSpec(
        scene_id="visual_test_01",
        description="Draw a very large red Circle. Draw a Text 'Hello World' exactly in the center of the screen.",
        # 这通常会导致 Text 被 Circle 的线条穿过或遮挡，或者颜色混杂
        duration=4.0,
        elements=["Big Circle", "Center Text"],
        audio_script="Testing visual critique."
    )

    # 3. 运行图
    print("🚀 Starting LangGraph Workflow...")
    initial_state = {
        "scene_spec": test_scene,
        "retries": 0,
        "code": None,
        "error_log": None,
        "artifact": None
    }

    # invoke 会同步运行直到图结束 (END)
    final_state = graph_app.invoke(initial_state)

    # 4. 检查结果
    print("\n=== Workflow Finished ===")
    if final_state.get("artifact"):
        print(f"✅ Success! Video: {final_state['artifact'].video_path}")
    else:
        print(f"❌ Failed. Final Error: {final_state.get('error_log')}")

if __name__ == "__main__":
    main()