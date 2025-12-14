# tests/test_fix_plan_output.py
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import json

from src.core.graph import ManimGraph
from src.core.state import GraphState
from src.core.models import SceneSpec

@pytest.fixture
def manim_graph_instance():
    with patch('src.llm.client.LLMClient') as MockLLMClient, \
         patch('src.components.context_builder.ContextBuilder') as MockContextBuilder, \
         patch('src.components.linter.CodeLinter') as MockCodeLinter, \
         patch('src.components.renderer.ManimRunner') as MockManimRunner, \
         patch('src.components.critic.VisionCritic') as MockVisionCritic:
        
        # Configure mocks
        mock_llm_client = MockLLMClient.return_value
        mock_llm_client.generate_text.return_value = "Mock fix instructions"
        
        mock_context_builder = MockContextBuilder.return_value
        mock_context_builder.api_stubs = "mock_api_stubs"
        mock_context_builder.examples = "mock_examples"

        # Instantiate ManimGraph
        graph = ManimGraph()
        graph.planner_llm = mock_llm_client # Ensure the actual instance uses the mock
        return graph, mock_llm_client

def test_fix_plan_saves_to_file(manim_graph_instance, tmp_path):
    graph, mock_llm_client = manim_graph_instance
    
    # Override FIX_PLAN_OUTPUT_DIR to use a temporary directory for testing
    graph.FIX_PLAN_OUTPUT_DIR = tmp_path / "fix_plan"
    graph.FIX_PLAN_OUTPUT_DIR.mkdir()

    scene_spec = SceneSpec(
        scene_id="test_scene", 
        description="a test scene", 
        duration=10.0,  # Added required field
        audio_script="This is a test audio script." # Added required field
    )
    
    state = GraphState(
        scene_spec=scene_spec,
        code="some code",
        layout_plan="initial plan",
        error_log="some error",
        visual_retries=0
    )

    # Call the node_analyze_error function
    result = graph.node_analyze_error(state)

    # Assert that fix_instructions are returned
    assert "fix_instructions" in result
    assert result["fix_instructions"] == "Mock fix instructions"

    # Assert that a file was created in the temporary directory
    expected_file = graph.FIX_PLAN_OUTPUT_DIR / f"{scene_spec.scene_id}_fix_v{state['visual_retries']}.json"
    assert expected_file.exists()

    # Read the content and assert it's correct
    with open(expected_file, "r", encoding="utf-8") as f:
        content = json.load(f)
    
    assert content["error_context"] == "Runtime/Syntax Error: some error"
    assert content["fix_instructions"] == "Mock fix instructions"

def test_fix_plan_saves_visual_retry_to_file(manim_graph_instance, tmp_path):
    graph, mock_llm_client = manim_graph_instance
    
    # Override FIX_PLAN_OUTPUT_DIR to use a temporary directory for testing
    graph.FIX_PLAN_OUTPUT_DIR = tmp_path / "fix_plan"
    graph.FIX_PLAN_OUTPUT_DIR.mkdir()

    scene_spec = SceneSpec(
        scene_id="another_scene", 
        description="another test scene",
        duration=5.0, # Added required field
        audio_script="Another test audio script." # Added required field
    )
    
    state = GraphState(
        scene_spec=scene_spec,
        code="some code",
        layout_plan="initial plan",
        critic_feedback="visual feedback",
        visual_retries=1
    )

    # Call the node_analyze_error function
    result = graph.node_analyze_error(state)

    # Assert that fix_instructions are returned
    assert "fix_instructions" in result
    assert result["fix_instructions"] == "Mock fix instructions"

    # Assert that a file was created in the temporary directory
    expected_file = graph.FIX_PLAN_OUTPUT_DIR / f"{scene_spec.scene_id}_fix_v{state['visual_retries']}.json"
    assert expected_file.exists()

    # Read the content and assert it's correct
    with open(expected_file, "r", encoding="utf-8") as f:
        content = json.load(f)
    
    assert content["error_context"] == "Visual QA Failed: visual feedback"
    assert content["fix_instructions"] == "Mock fix instructions"