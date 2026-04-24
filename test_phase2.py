import sys
import os
import unittest
from unittest.mock import MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import engine
import themes

class TestPhase2(unittest.TestCase):
    def test_theme_swapping_logic(self):
        # We mock tk.Tk and widgets because we are in headless environment
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
        except Exception as e:
            print(f"Skipping UI test due to headless environment: {e}")
            return
        
        import ui
        # We need to mock windnd as it might fail to init without a window
        ui.windnd = MagicMock()
        
        # Mock some Tkinter methods that might fail or are not needed
        app = ui.RetroBranderUI(root)
        
        # Initial should be LIGHT
        self.assertEqual(app.current_theme_name, "LIGHT")
        self.assertEqual(app.theme, themes.LIGHT)
        
        # Toggle to DARK
        app.toggle_theme()
        self.assertEqual(app.current_theme_name, "DARK")
        self.assertEqual(app.theme, themes.DARK)
        
        # Toggle back to LIGHT
        app.toggle_theme()
        self.assertEqual(app.current_theme_name, "LIGHT")
        self.assertEqual(app.theme, themes.LIGHT)
        
        root.destroy()

    def test_pro_export_command(self):
        settings = {
            'out_res': '720p',
            'out_crf': 30,
            'use_nvenc': False,
            'audio_mode': 'Original'
        }
        cmd = engine.get_ffmpeg_command("input.mp4", "logo.png", "overlay.gif", settings)
        
        # Check for 720p resolution flag
        # cmd might look like [..., '-s', '1280x720', ...]
        has_res = False
        for i in range(len(cmd)-1):
            if cmd[i] == '-s' and cmd[i+1] == '1280x720':
                has_res = True
                break
        self.assertTrue(has_res, f"720p resolution flags not found in {cmd}")
        
        # Check for CRF 30 flag
        has_crf = False
        for i in range(len(cmd)-1):
            if cmd[i] == '-crf' and cmd[i+1] == '30':
                has_crf = True
                break
        self.assertTrue(has_crf, f"CRF 30 flag not found in {cmd}")
        
        # Check that it uses libx264 since use_nvenc is False
        self.assertIn('libx264', cmd)

if __name__ == '__main__':
    unittest.main()
