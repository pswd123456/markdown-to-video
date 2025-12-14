import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))


from unittest.mock import MagicMock
from src.core.graph import ManimGraph
from src.core.models import SceneSpec, RenderArtifact, CritiqueFeedback, SceneType

def test_node_critic_saves_debug_code(tmp_path, monkeypatch):
    # 1. Setup Environment: Mock output directory
    mock_output = tmp_path / "output"
    mock_output.mkdir()
    
    # Patch settings.OUTPUT_DIR
    import src.core.config
    monkeypatch.setattr(src.core.config.settings, "OUTPUT_DIR", mock_output)
    
    # 2. Setup Graph and Critic Mock
    # We instantiate ManimGraph. If it interacts with external APIs in init, we might need more mocking.
    # Assuming __init__ is safe (just object creation).
    graph = ManimGraph()
    graph.critic = MagicMock()
    
    # Configure mock to fail
    mock_suggestion = "Colors are too dark."
    graph.critic.review_layout.return_value = CritiqueFeedback(
        passed=False,
        score=2,
        suggestion=mock_suggestion
    )
    
    # 3. Setup State
    scene_id = "test_001"
    vis_try = 1
    scene = SceneSpec(
        scene_id=scene_id,
        description="Test Scene",
        duration=5.0,
        audio_script="Test Audio",
        type=SceneType.DYNAMIC
    )
    
    artifact = RenderArtifact(
        video_path="dummy.mp4",
        last_frame_path="dummy.png",
        code_content="print('Hello World')",
        scene_id="test_001"
    )
    
    state = {
        "scene_spec": scene,
        "code": "class TestScene(Scene): pass # Err code",
        "artifact": artifact,
        "visual_retries": vis_try,
        "retries": 0,
        "error_log": None,
        "critic_feedback": None
    }
    
    # 4. Execute Node
    result = graph.node_critic(state)
    
    # 5. Verify Result
    assert result["critic_feedback"] == mock_suggestion
    
    # 6. Verify File Created
    critic_dir = mock_output / "critic"
    assert critic_dir.exists()
    
    # Check for the file.
    expected_file = critic_dir / f"{scene_id}_critic_v{vis_try}.txt"
    assert expected_file.exists()
    
    with open(expected_file, "r", encoding="utf-8") as f:
        content = f.read()
        expected_content = f"Passed: False\nScore: 2\nEvidence: {mock_suggestion}"
        assert content == expected_content
