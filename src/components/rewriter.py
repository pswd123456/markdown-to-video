# src/components/rewriter.py
import json
import logging
from typing import Dict, Any

from src.llm.client import LLMClient
from src.core.config import settings
from src.llm.prompts import STORYBOARD_SYSTEM_PROMPT
from src.utils.code_ops import extract_json
from src.utils.logger import logger

class ScriptRewriter:
    def __init__(self):
        self.llm_client = LLMClient(model=settings.REWRITER_MODEL)

    def rewrite(self, markdown_draft: str, retries: int = 3) -> Dict[str, Any]:
        """
        Rewrites a non-structured Markdown/text draft into a structured JSON storyboard.

        Args:
            markdown_draft: The non-structured Markdown or text content.
            retries: Number of retries for LLM call and parsing errors.

        Returns:
            A dictionary containing the structured storyboard (e.g., {"scenes": [...]}).
        """
        system_prompt = STORYBOARD_SYSTEM_PROMPT
        user_prompt = f"""# INPUT TEXT

{markdown_draft}"""
        
        last_exception = None

        for attempt in range(retries):
            try:
                raw_response = self.llm_client.generate_code(system_prompt, user_prompt)
                
                # Post-processing: Extract JSON using code_ops
                json_str = extract_json(raw_response)
                
                parsed_data = json.loads(json_str)
                
                # Basic validation: ensure 'scenes' key exists
                if "scenes" not in parsed_data:
                    # If LLM returned just a list, wrap it
                    if isinstance(parsed_data, list):
                         parsed_data = {"scenes": parsed_data}
                    else:
                        raise ValueError("JSON output missing 'scenes' key")
                
                return parsed_data

            except (json.JSONDecodeError, ValueError) as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1}/{retries} failed to parse JSON: {e}. Raw output snippet: {raw_response[:200]}...")
                # Optional: You could update the prompt here to ask for correction, 
                # but simple retry often works for stochastic LLM errors.
            except Exception as e:
                # Catching LLM connection errors etc.
                last_exception = e
                logger.error(f"Attempt {attempt + 1}/{retries} failed with error: {e}")
        
        logger.error("Max retries exceeded for ScriptRewriter.")
        raise last_exception or RuntimeError("Unknown error in ScriptRewriter")
