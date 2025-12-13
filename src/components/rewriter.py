# src/components/rewriter.py
from src.llm.client import LLMClient
from src.core.config import settings

class ScriptRewriter:
    def __init__(self):
        self.llm_client = LLMClient(model=settings.REWRITER_MODEL)

    def rewrite_script(self, markdown_draft: str) -> str:
        """
        Rewrites a non-structured Markdown/text draft into a structured JSON format
        suitable for the system requirements using the REWRITER_MODEL.

        Args:
            markdown_draft: The non-structured Markdown or text content.

        Returns:
            A string containing the structured JSON data.
        """
        system_prompt = "You are a script rewriter assistant. Your task is to transform raw markdown or text drafts into a structured JSON format. Ensure the output is valid JSON and follows the specified schema."
        user_prompt = f"Rewrite the following draft into a structured JSON format:\n\n{markdown_draft}\n\nSchema: {{ \"title\": \"string\", \"scenes\": [ {{ \"scene_number\": \"integer\", \"title\": \"string\", \"script\": \"string\" }} ] }}"
        
        # Placeholder for actual LLM call and parsing
        # The actual output format needs to be defined and enforced by the prompt
        # For now, it returns a string which is expected to be JSON.
        return self.llm_client.generate_code(system_prompt, user_prompt)
