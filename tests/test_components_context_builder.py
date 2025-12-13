import unittest
from pathlib import Path
import sys

# Add project root
sys.path.append(str(Path(__file__).parent.parent))

from src.components.context_builder import ContextBuilder

class TestContextBuilder(unittest.TestCase):
    def test_build_system_prompt_includes_font_constraint(self):
        builder = ContextBuilder()
        prompt = builder.build_system_prompt()
        
        self.assertIn('font="Noto Sans CJK SC"', prompt)
        self.assertIn('support Chinese characters', prompt)

if __name__ == '__main__':
    unittest.main()
