import pytest
from unittest.mock import MagicMock
from src.components.rewriter import ScriptRewriter
from src.llm.client import LLMClient

@pytest.fixture
def mock_llm_client(monkeypatch):
    mock_client = MagicMock(spec=LLMClient)
    monkeypatch.setattr("src.components.rewriter.LLMClient", lambda model: mock_client)
    return mock_client

def test_validation_success(mock_llm_client):
    # Valid JSON response
    mock_response = """
    {
      "scenes": [
        {
          "scene_id": "scene_01",
          "type": "dynamic",
          "description": "Valid scene.",
          "duration": 5.0,
          "elements": ["Element"],
          "audio_script": "Script."
        }
      ]
    }
    """
    mock_llm_client.generate_code.return_value = mock_response
    rewriter = ScriptRewriter()
    result = rewriter.rewrite("Draft")
    
    assert len(result["scenes"]) == 1
    assert result["scenes"][0]["duration"] == 5.0
    assert result["scenes"][0]["scene_id"] == "scene_01"
    assert result["scenes"][0]["type"] == "dynamic"

def test_validation_failure_missing_field_then_success(mock_llm_client):
    # First attempt: Missing 'duration'
    bad_response = """
    {
      "scenes": [
        {
          "scene_id": "scene_01",
          "description": "Valid scene.",
          "elements": ["Element"],
          "audio_script": "Script."
        }
      ]
    }
    """
    # Second attempt: Valid
    good_response = """
    {
      "scenes": [
        {
          "scene_id": "scene_01",
          "description": "Valid scene.",
          "duration": 5.0,
          "elements": ["Element"],
          "audio_script": "Script."
        }
      ]
    }
    """
    mock_llm_client.generate_code.side_effect = [bad_response, good_response]
    
    rewriter = ScriptRewriter()
    result = rewriter.rewrite("Draft", retries=2)
    
    assert mock_llm_client.generate_code.call_count == 2
    assert result["scenes"][0]["duration"] == 5.0

def test_validation_failure_wrong_type_exhaust_retries(mock_llm_client):
    # 'duration' is a string "five seconds", which Pydantic cannot verify as float
    bad_response = """
    {
      "scenes": [
        {
          "scene_id": "scene_01",
          "description": "Valid scene.",
          "duration": "five seconds",
          "elements": ["Element"],
          "audio_script": "Script."
        }
      ]
    }
    """
    mock_llm_client.generate_code.return_value = bad_response
    
    rewriter = ScriptRewriter()
    
    with pytest.raises(ValueError): # The rewriter re-raises the last exception
        rewriter.rewrite("Draft", retries=2)
    
    assert mock_llm_client.generate_code.call_count == 2
