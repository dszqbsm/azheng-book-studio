import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from subtitles import caption_boundaries, clean_ending, clean_cues, validate_short_cues


class SubtitleTests(unittest.TestCase):
    def test_require_short_cues(self):
        for text in ('人人知之；清官尤可恨', '贾魏氏屈打成招,百姓无处伸冤', '前一句。后一句'):
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, 'cue 1'):
                validate_short_cues([{'text': text}])
        validate_short_cues([{'text': '人人知之'}, {'text': '清官尤可恨'}, {'text': '“慢一点！”'}])

    def test_split_quoted_verse_without_dangling_quotes(self):
        text = '“海内存知己，天涯若比邻”'
        self.assertEqual(caption_boundaries(text), ([(7, True)], {0, len(text) - 1}))

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
