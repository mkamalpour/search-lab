"""Uploaded stories remain text in the original HTML-rich SetQA interface."""
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest


class SetQAHTMLTests(unittest.TestCase):
    def test_story_browser_and_walkthrough_escape_uploaded_html(self):
        path = Path(__file__).resolve().parents[1] / 'tools' / 'setqa' / 'app.py'
        payload = (b'1 Mary picked up the apple.\n'
                   b'2 <img src="https://invalid.example/tracker">.\n'
                   b'3 What is Mary carrying?\tapple\n')
        with patch.object(sys, 'path', [str(path.parent), *sys.path]), \
                patch('streamlit.file_uploader', return_value=io.BytesIO(payload)):
            app = AppTest.from_file(str(path)).run(timeout=30)
            self.assertFalse(app.exception)
            rendered = '\n'.join(item.value for item in app.markdown)
            self.assertNotIn('<img src=', rendered)
            self.assertGreaterEqual(rendered.count('&lt;img src='), 2)
            mode = next(item for item in app.radio if item.label == 'Mode')
            mode.set_value('Step Through').run(timeout=30)
            step = next(item for item in app.slider if item.label == 'Step')
            step.set_value(2).run(timeout=30)
            self.assertFalse(app.exception)
            rendered = '\n'.join(item.value for item in app.markdown)
            self.assertNotIn('<img src=', rendered)
            self.assertGreaterEqual(rendered.count('&lt;img src='), 2)
