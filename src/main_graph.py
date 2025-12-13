from src.core.graph import ManimGraph
from src.core.models import SceneSpec

def main():
    # 1. 初始化图
    graph_app = ManimGraph().compile()
    
    # (可选) 生成流程图的可视化 (需要安装 pygraphviz，这里先略过)
    # print(graph_app.get_graph().draw_ascii())

    # 2. 准备输入数据
    test_scene = SceneSpec(
        scene_id="graph_demo_01",
        description="Visualize a sine wave.",
        duration=4.0,
        elements=["Axes", "Sine Curve"],
        audio_script="This is a sine wave function."
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