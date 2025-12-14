# src/components/rewriter.py
import json
from typing import Dict, Any

from pydantic import ValidationError

from src.llm.client import LLMClient
from src.core.config import settings
from src.core.models import SceneSpec
from src.llm.prompts import STORYBOARD_SYSTEM_PROMPT
from src.utils.code_ops import extract_json
from src.utils.logger import logger

class ScriptRewriter:
    def __init__(self):
        self.llm_client = LLMClient(model=settings.REWRITER_MODEL)

    async def rewrite(self, markdown_draft: str, retries: int = 3) -> Dict[str, Any]:
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
                raw_response = await self.llm_client.generate_code(system_prompt, user_prompt)
                
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
                
                # Data Validation using Pydantic
                validated_scenes = []
                for scene in parsed_data["scenes"]:
                    # This will raise ValidationError if data is invalid
                    # model_dump() converts back to dict (Pydantic v2)
                    validated_scenes.append(SceneSpec(**scene).model_dump())
                
                parsed_data["scenes"] = validated_scenes
                
                return parsed_data

            except (json.JSONDecodeError, ValueError, ValidationError) as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1}/{retries} failed: {e}. Raw output snippet: {raw_response[:200]}...")
                # Optional: You could update the prompt here to ask for correction, 
                # but simple retry often works for stochastic LLM errors.
            except Exception as e:
                # Catching LLM connection errors etc.
                last_exception = e
                logger.error(f"Attempt {attempt + 1}/{retries} failed with error: {e}")
        
        logger.error("Max retries exceeded for ScriptRewriter.")
        raise last_exception or RuntimeError("Unknown error in ScriptRewriter")
