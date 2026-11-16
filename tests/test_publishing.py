import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from publishing import CONFIG_PATH, validate_description_and_tags, validate_titles, validate_chapters


class PublishingTests(unittest.TestCase):
    def test_description_and_fixed_tag_order(self):
        config = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
        tags = ['#读书', '#听书助眠', '#睡前听书', '#精读名著', '#容斋随笔']
        validate_description_and_tags('《容斋随笔》：读史最怕的，是把故事当真。', tags, '《容斋随笔》', config)
        with self.assertRaises(ValueError):
            validate_description_and_tags('先看故事。再读历史。', tags, '容斋随笔', config)
        with self.assertRaises(ValueError):
            validate_description_and_tags('一句话。', tags[::-1], '容斋随笔', config)

    def test_chapter_name_limit(self):
        self.assertEqual(validate_chapters({'chapters': [{'title': '字' * 12}]} )[0]['characters'], 12)
        with self.assertRaises(ValueError):
            validate_chapters({'chapters': [{'title': '字' * 12 + '？'}]})
    def titles(self):
        return dict(xiaohongshu='字' * 20, douyin='字' * 30,
                    weixin_channels='字' * 16, kuaishou='字' * 200)

    def test_exact_limits_and_unlimited_kuaishou(self):
        self.assertEqual([r['characters'] for r in validate_titles(self.titles())], [20, 30, 16, 200])

    def test_each_limited_platform_rejects_extra_punctuation(self):
        for key in ['xiaohongshu', 'douyin', 'weixin_channels']:
            with self.subTest(key=key):
                titles = self.titles()
                titles[key] += '？'
                with self.assertRaises(ValueError):
                    validate_titles(titles)

    def test_all_platforms_required(self):
        for key in self.titles():
            titles = self.titles()
            del titles[key]
            with self.assertRaises(ValueError):
                validate_titles(titles)

    def test_blank_or_multiline_rejected(self):
        for text in ['', '  ', '标题\n下一行']:
            titles = self.titles()
            titles['kuaishou'] = text
            with self.assertRaises(ValueError):
                validate_titles(titles)
