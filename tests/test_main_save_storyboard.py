import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.main import load_script
from src.core.config import settings

@pytest.fixture
def mock_rewriter(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr("src.main.ScriptRewriter", mock_cls)
    return mock_cls

def test_load_script_saves_storyboard(tmp_path, mock_rewriter, monkeypatch):
    # Setup output dir to tmp_path
    monkeypatch.setattr(settings, "OUTPUT_DIR", tmp_path)
    
    # Mock rewrite result
    mock_instance = mock_rewriter.return_value
    mock_result = {
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
    mock_instance.rewrite.return_value = mock_result
    
    # Input file
    input_file = tmp_path / "draft.md"
    input_file.write_text("# Draft Content")
    
    # Run
    load_script(str(input_file))
    
    # Verify file saved
    output_file = tmp_path / "storyboard.json"
    assert output_file.exists()
    
    content = json.loads(output_file.read_text(encoding="utf-8"))
    assert content == mock_result
    
    # Verify content formatting (roughly)
    text = output_file.read_text(encoding="utf-8")
    assert '\n' in text # Indentation check
    assert '  ' in text

