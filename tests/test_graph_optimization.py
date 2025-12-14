import pytest
from unittest.mock import MagicMock, AsyncMock
from src.core.graph import ParallelManimFlow
from src.core.state import GraphState
from src.core.models import CritiqueFeedback, SceneSpec

# Mock artifact object
class MockArtifact:
    def __init__(self, path):
        self.last_frame_path = path

@pytest.mark.asyncio
async def test_visual_retry_optimization():
    """
    Verify that when MAX_VISUAL_RETRIES is reached, the graph 
    skips the final expensive Critic call and finishes.
    """
    graph = ParallelManimFlow()
    
    # 1. Setup Mocks
    
    # Mock LLM generation to return dummy code
    graph.coder_llm = AsyncMock()
    graph.coder_llm.generate_code.return_value = "```python\nclass MyScene(Scene): pass\n```"
    
    # Mock Planner LLM as it's called in node_plan_layout
    graph.planner_llm = AsyncMock()
    graph.planner_llm.generate_text.return_value = "## Layout Plan\n\nDummy plan"

    # Mock Linter to always pass
    graph.linter = MagicMock()
    mock_lint_res = MagicMock()
    mock_lint_res.passed = True
    graph.linter.validate.return_value = mock_lint_res
    
    # Mock Runner to return a dummy artifact
    graph.runner = MagicMock()
    # graph.runner.render needs to be awaitable
    graph.runner.render = AsyncMock(return_value=MockArtifact("/tmp/fake_image.png"))
    
    # Mock Critic to ALWAYS FAIL
    # This forces the graph to retry until max retries
    graph.critic = AsyncMock()
    graph.critic.review_layout.return_value = CritiqueFeedback(
        passed=False, 
        score=0, 
        suggestion="Move it left"
    )
    
    # 2. Configure Logic
    # We want to retry 1 time.
    # Flow:
    # 1. Generate -> Render -> Critic (Fail) -> Retry? Yes (0 < 1).
    # 2. Retry Logic (prep_vis) -> Generate -> Render -> Critic (Fail) -> Retry? No (1 >= 1) -> Finish.
    # Total Critic Calls: 2
    # 
    # Optimized Flow:
    # 1. Generate -> Render -> Critic (Fail) -> Retry? Yes.
    # 2. Retry Logic -> Generate -> Render -> CHECK MAX -> Finish.
    # Total Critic Calls: 1
    
    graph.MAX_VISUAL_RETRIES = 1
    
    # 3. Compile and Run
    app = graph.compile()
    
    initial_state = GraphState(
        scene_spec=SceneSpec(
            scene_id="test", 
            description="desc", 
            elements=[],
            duration=5.0,
            audio_script="hello"
        ),
        retries=0,
        visual_retries=0,
        code=None,
        error_log=None,
        critic_feedback=None
    )
    
    # Run the graph
    # We expect it to finish.
    await app.ainvoke(initial_state)

    
    # 4. Assertions
    # We want 1 call, but currently it likely does 2.
    print(f"Critic call count: {graph.critic.review_layout.call_count}")
    
    assert graph.critic.review_layout.call_count == 1
