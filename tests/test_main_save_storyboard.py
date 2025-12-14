import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch
from src.main import load_script
from src.core.config import settings
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
async def test_load_script_saves_storyboard(tmp_path, mock_rewriter, monkeypatch):
    # Setup output dir to tmp_path
    monkeypatch.setattr(settings, "OUTPUT_DIR", tmp_path)
    
    # Mock rewrite result
    mock_rewriter.return_value = {
        "scenes": [
            {
                "scene_id": "intro",
                "description": "intro",
                "duration": 5.0,
                "elements": [],
                "audio_script": "intro audio",
                "type": "dynamic"
            }
        ]
    }
    
    # Input file
    input_file = tmp_path / "draft.md"
    input_file.write_text("# Draft Content")
    
    # Run
    await load_script(str(input_file))
    
    # Verify file saved
    output_file = tmp_path / "storyboard.json"
    assert output_file.exists()
    
    content = json.loads(output_file.read_text(encoding="utf-8"))
    assert content == mock_rewriter.return_value
    
    # Verify content formatting (roughly)
    text = output_file.read_text(encoding="utf-8")
    assert '\n' in text # Indentation check
    assert '  ' in text

