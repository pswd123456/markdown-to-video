# tests/test_fix_plan_output.py
import pytest
from unittest.mock import patch, AsyncMock

from src.core.graph import ParallelManimFlow
from src.core.state import GraphState
from src.core.models import SceneSpec
from src.core.config import settings

@pytest.fixture
def manim_graph_instance(tmp_path, monkeypatch):
    with patch('src.core.graph.LLMClient') as MockLLMClient, \
         patch('src.core.graph.ContextBuilder') as MockContextBuilder:
        
        # Configure mocks
        # MockLLMClient is the class, its return_value is the instance
        mock_llm_client = MockLLMClient.return_value
        mock_llm_client.generate_text = AsyncMock(return_value="Mock fix instructions")
        
        mock_context_builder = MockContextBuilder.return_value
        mock_context_builder.api_stubs = "mock_api_stubs"
        mock_context_builder.examples = "mock_examples"

        # Patch settings.OUTPUT_DIR
        mock_output = tmp_path / "output"
        mock_output.mkdir()
        monkeypatch.setattr(settings, "OUTPUT_DIR", mock_output)

        # Instantiate ParallelManimFlow
        graph = ParallelManimFlow()
        # graph.planner_llm is already mock_llm_client because of the patch
        return graph, mock_llm_client

@pytest.mark.asyncio
async def test_fix_plan_saves_to_file(manim_graph_instance, tmp_path):
    graph, mock_llm_client = manim_graph_instance
    
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
        visual_retries=0,
        retries=0, # Added missing field
    )

    # Call the node_analyze_error function
    result = await graph.node_analyze_error(state)

    # Assert that fix_instructions are returned
    assert "fix_instructions" in result
    assert result["fix_instructions"] == "Mock fix instructions"

    # Assert that a file was created in the temporary directory
    expected_file_dir = settings.OUTPUT_DIR / "fix_plan"
    expected_file = expected_file_dir / f"{scene_spec.scene_id}_fix_v{state['visual_retries']}_s{state['retries']}.md"
    assert expected_file.exists()

    # Read the content and assert it's correct
    with open(expected_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    expected_error_context = "EXECUTION TRACEBACK:\nsome error"
    expected_content = f"# Fix Plan (Runtime_Linter)\n\n## Input Error Context\n{expected_error_context}\n\n## Generated Instructions\nMock fix instructions"
    assert content == expected_content

@pytest.mark.asyncio
async def test_fix_plan_saves_visual_retry_to_file(manim_graph_instance, tmp_path):
    graph, mock_llm_client = manim_graph_instance
    
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
        visual_retries=1,
        retries=0, # Added missing field
    )

    # Call the node_analyze_error function
    result = await graph.node_analyze_error(state)

    # Assert that fix_instructions are returned
    assert "fix_instructions" in result
    assert result["fix_instructions"] == "Mock fix instructions"

    # Assert that a file was created in the temporary directory
    expected_file_dir = settings.OUTPUT_DIR / "fix_plan"
    expected_file = expected_file_dir / f"{scene_spec.scene_id}_fix_v{state['visual_retries']}_s{state['retries']}.md"
    assert expected_file.exists()

    # Read the content and assert it's correct
    with open(expected_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    expected_error_context = "VISUAL REPORT FROM QA:\nvisual feedback\n(Note: Translate this visual issue into Manim API corrections)"
    expected_content = f"# Fix Plan (Visual_Critic)\n\n## Input Error Context\n{expected_error_context}\n\n## Generated Instructions\nMock fix instructions"
    assert content == expected_content