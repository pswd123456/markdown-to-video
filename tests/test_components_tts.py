import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path


# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from src.components.tts import TTSEngine

class TestTTSEngine(unittest.TestCase):
    def setUp(self):
        self.tts = TTSEngine()

    def tearDown(self):
        # Clean up files created
        for scene_id in ["test_scene_url"]:
            p = self.tts.output_dir / f"{scene_id}.mp3"
            if p.exists():
                p.unlink()

    @patch('src.components.tts.dashscope.MultiModalConversation.call')
    @patch('src.components.tts.requests.get')
    def test_generate_with_url(self, mock_get, mock_call):
        # Ensure file doesn't exist so it doesn't skip
        scene_id = "test_scene_url"
        p = self.tts.output_dir / f"{scene_id}.mp3"
        if p.exists():
            p.unlink()

        # Mock the MultiModalConversation result
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        # Structure the mock to have output.audio.url
        mock_audio_info = MagicMock()
        mock_audio_info.url = "http://example.com/audio.mp3"
        # Make the mock support .get() just in case, though getattr is tried first or second
        # But simpler to just rely on getattr which MagicMock supports
        
        mock_output = MagicMock()
        mock_output.audio = mock_audio_info
        
        mock_response.output = mock_output
        mock_call.return_value = mock_response

        # Mock requests.get
        mock_http_response = MagicMock()
        mock_http_response.status_code = 200
        mock_http_response.content = b"fake audio content via url"
        mock_get.return_value = mock_http_response

        # Execute
        output_path = self.tts.generate("Hello world", scene_id)

        # Verify
        expected_path = str(self.tts.output_dir / f"{scene_id}.mp3")
        self.assertEqual(output_path, expected_path)
        
        # Check if file was written
        with open(output_path, "rb") as f:
            content = f.read()
        self.assertEqual(content, b"fake audio content via url")

        # Verify calls
        mock_call.assert_called_once()
        mock_get.assert_called_once_with("http://example.com/audio.mp3")

if __name__ == '__main__':
    unittest.main()