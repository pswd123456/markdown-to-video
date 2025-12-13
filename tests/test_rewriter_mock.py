import json
import pytest
from unittest.mock import MagicMock
from src.components.rewriter import ScriptRewriter
from src.llm.client import LLMClient

@pytest.fixture
def mock_llm_client(monkeypatch):
    mock_client = MagicMock(spec=LLMClient)
    monkeypatch.setattr("src.components.rewriter.LLMClient", lambda model: mock_client)
    return mock_client

def test_rewrite_success(mock_llm_client):
    # Mock LLM response: Valid JSON wrapped in markdown
    mock_response = """
    ```json
    {
      "scenes": [
        {
          "scene_id": "scene_01",
          "description": "A blue server icon slides in.",
          "duration": 5.0,
          "elements": ["Server"],
          "audio_script": "This is a server."
        }
      ]
    }
    ```
    """
    mock_llm_client.generate_code.return_value = mock_response

    rewriter = ScriptRewriter()
    result = rewriter.rewrite("Draft text")

    assert "scenes" in result
    assert len(result["scenes"]) == 1
    assert result["scenes"][0]["scene_id"] == "scene_01"

def test_rewrite_retry_mechanism(mock_llm_client):
    # Mock LLM response: Fail first 2 times, succeed on 3rd
    bad_response = "Not valid JSON"
    good_response = '{"scenes": []}'
    
    mock_llm_client.generate_code.side_effect = [bad_response, bad_response, good_response]

    rewriter = ScriptRewriter()
    result = rewriter.rewrite("Draft text", retries=3)

    assert "scenes" in result
    assert mock_llm_client.generate_code.call_count == 3

def test_rewrite_fail_all_retries(mock_llm_client):
    # Mock LLM response: Always fail
    bad_response = "Not valid JSON"
    mock_llm_client.generate_code.return_value = bad_response

    rewriter = ScriptRewriter()
    
    with pytest.raises(json.JSONDecodeError):
        rewriter.rewrite("Draft text", retries=2)
    
    assert mock_llm_client.generate_code.call_count == 2

def test_rewrite_prompt_content(mock_llm_client):
    mock_llm_client.generate_code.return_value = '{"scenes": []}'
    
    rewriter = ScriptRewriter()
    rewriter.rewrite("Draft text")
    
    # Check call args
    args, _ = mock_llm_client.generate_code.call_args
    sys_prompt = args[0]
    
    assert "Intro" in sys_prompt
    assert "Summary" in sys_prompt
    assert "Chinese" in sys_prompt
    assert "60 seconds" in sys_prompt