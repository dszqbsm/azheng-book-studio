import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from subtitles import clean_ending, clean_cues


class SubtitleTests(unittest.TestCase):
    def test_preserve_book_marks_and_inner_punctuation(self):
        self.assertEqual(clean_ending('今天，我们听《菜根谭》。'), '今天，我们听《菜根谭》')
        self.assertEqual(clean_ending('他说：“慢一点！”'), '他说：“慢一点”')
        self.assertEqual(clean_ending('保留《菜根谭》'), '保留《菜根谭》')

    def test_cues_preserve_timing_and_source(self):
        original = {'cues': [{'start': 0, 'end': 2, 'text': '认真生活，'}]}
        result = clean_cues(original)
        self.assertEqual(result['cues'][0], {'start': 0, 'end': 2, 'text': '认真生活'})
        self.assertEqual(original['cues'][0]['text'], '认真生活，')

    def test_reject_invalid_cues(self):
        with self.assertRaises(ValueError):
            clean_cues({'cues': [{'start': 2, 'end': 1, 'text': '测试'}]})
