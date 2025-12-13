import pytest
import os
import json
from unittest.mock import MagicMock
from src.main import load_script
from src.core.models import SceneSpec

@pytest.fixture
def mock_rewriter(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr("src.main.ScriptRewriter", mock_cls)
    return mock_cls

def test_load_script_json(tmp_path):
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
    scenes = load_script(str(file_path))
    
    # Verification
    assert len(scenes) == 1
    assert isinstance(scenes[0], SceneSpec)
    assert scenes[0].scene_id == "s1"

def test_load_script_md_integration(tmp_path, mock_rewriter):
    # Setup
    mock_instance = mock_rewriter.return_value
    mock_instance.rewrite.return_value = {
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
    scenes = load_script(str(file_path))
    
    # Verification
    mock_rewriter.assert_called_once()
    mock_instance.rewrite.assert_called_once_with("Markdown Content")
    assert len(scenes) == 1
    assert scenes[0].scene_id == "s2"

def test_load_script_unsupported(tmp_path):
    file_path = tmp_path / "image.png"
    file_path.touch()
    
    with pytest.raises(ValueError, match="Unsupported file format"):
        load_script(str(file_path))
