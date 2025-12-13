import unittest
import tempfile
import shutil
from unittest.mock import MagicMock, patch, call
from pathlib import Path
import sys

# Add project root
sys.path.append(str(Path(__file__).parent.parent))

from src.components.assembler import Assembler
from src.core.models import RenderArtifact

class TestAssembler(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.patcher_settings = patch('src.components.assembler.settings')
        self.mock_settings = self.patcher_settings.start()
        self.mock_settings.OUTPUT_DIR = Path(self.test_dir)
        
        self.assembler = Assembler()

    def tearDown(self):
        self.patcher_settings.stop()
        shutil.rmtree(self.test_dir)

    @patch('src.components.assembler.subprocess.run')
    @patch('src.components.assembler.subprocess.check_output')
    def test_assemble_with_spacer(self, mock_check_output, mock_run):
        # Setup real files
        p_v1 = Path(self.test_dir) / "v1.mp4"
        p_v1.touch()
        p_v2 = Path(self.test_dir) / "v2.mp4"
        p_v2.touch()
        p_a1 = Path(self.test_dir) / "a1.mp3"
        p_a1.write_bytes(b'0' * 200) # > 100 bytes
        p_a2 = Path(self.test_dir) / "a2.mp3"
        p_a2.write_bytes(b'0' * 200)

        # Mocks
        mock_check_output.return_value = "1920x1080\n"
        
        # Inputs
        artifacts = [
            RenderArtifact(scene_id="s1", video_path=str(p_v1), last_frame_path="i1.png", code_content=""),
            RenderArtifact(scene_id="s2", video_path=str(p_v2), last_frame_path="i2.png", code_content="")
        ]
        audio_paths = [str(p_a1), str(p_a2)]
        
        # Run
        self.assembler.assemble(artifacts, audio_paths)
        
        # Check resolution call
        self.assertTrue(mock_check_output.called)
        
        # Check spacer generation
        spacer_gen_called = False
        for call_args in mock_run.call_args_list:
            cmd = call_args[0][0]
            if "color=c=black:s=1920x1080:d=1.0" in cmd or \
               any("color=c=black" in arg for arg in cmd if isinstance(arg, str)):
                 spacer_gen_called = True
        self.assertTrue(spacer_gen_called, "Spacer generation command should be called")

        # Check concat list
        concat_file = Path(self.test_dir) / "concat_list.txt"
        self.assertTrue(concat_file.exists())
        content = concat_file.read_text()
        
        self.assertIn("black_spacer.mp4", content)
        self.assertIn("segment_000.mp4", content)
        self.assertIn("segment_001.mp4", content)

if __name__ == '__main__':
    unittest.main()
