import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch
from src.main import load_script
from src.core.models import SceneSpec
from src.components.rewriter import ScriptRewriter

@pytest.fixture
def mock_rewriter(monkeypatch):
    # Mock the ScriptRewriter class itself
    mock_rewriter_class = MagicMock(spec=ScriptRewriter)
    # Mock the rewrite method to be an AsyncMock
    mock_rewrite_method = AsyncMock()
    mock_rewriter_class.return_value.rewrite = mock_rewrite_method
    
    monkeypatch.setattr("src.main.ScriptRewriter", mock_rewriter_class)
    return mock_rewrite_method # Return the mock of the rewrite method

@pytest.mark.asyncio
async def test_load_script_json(tmp_path):
    # Setup
    data = {
        "scenes": [
            {
                "scene_id": "s1",
                "description": "desc",
                "duration": 5.0,
                "elements": [],
                "audio_script": "audio"
            }
        ]
    }
    file_path = tmp_path / "script.json"
    with open(file_path, "w") as f:
        json.dump(data, f)
        
    # Execution
    scenes = await load_script(str(file_path))
    
    # Verification
    assert len(scenes) == 1
    assert isinstance(scenes[0], SceneSpec)
    assert scenes[0].scene_id == "s1"

@pytest.mark.asyncio
async def test_load_script_md_integration(tmp_path, mock_rewriter):
    # Setup
    # Mock the rewriter.rewrite method to return a dict directly
    mock_rewriter.return_value = {
        "scenes": [
            {
                "scene_id": "s2",
                "description": "desc md",
                "duration": 10.0,
                "elements": ["E1"],
                "audio_script": "audio md"
            }
        ]
    }
    
    file_path = tmp_path / "draft.md"
    file_path.write_text("Markdown Content")
    
    # Execution
    scenes = await load_script(str(file_path))
    
    # Verification
    # Ensure rewrite was called once
    mock_rewriter.assert_called_once()
    assert len(scenes) == 1
    assert scenes[0].scene_id == "s2"
    assert scenes[0].duration == 10.0

@pytest.mark.asyncio
async def test_load_script_unsupported(tmp_path):
    file_path = tmp_path / "image.png"
    file_path.touch()
    
    with pytest.raises(ValueError, match="Unsupported file format"):
        await load_script(str(file_path))
