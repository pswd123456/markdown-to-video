import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

import pytest
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
    graph.critic.review_layout.return_value = CritiqueFeedback(
        passed=False,
        score=2,
        suggestion="Colors are too dark."
    )
    
    # 3. Setup State
    scene = SceneSpec(
        scene_id="test_001",
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
        "visual_retries": 1,
        "retries": 0,
        "error_log": None,
        "critic_feedback": None
    }
    
    # 4. Execute Node
    result = graph.node_critic(state)
    
    # 5. Verify Result
    assert result["critic_feedback"] == "Colors are too dark."
    
    # 6. Verify File Created
    debug_dir = mock_output / "debug"
    assert debug_dir.exists()
    
    # Check for the file. Note: scene_id is test_001, vis_try is 1.
    expected_file = debug_dir / "scene_test_001_failed_vis_retry_1.py"
    assert expected_file.exists()
    
    with open(expected_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert content == "class TestScene(Scene): pass # Err code"
