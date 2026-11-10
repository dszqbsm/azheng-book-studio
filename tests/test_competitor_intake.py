import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from competitor_intake import FIELDS, ROOT, inventory


class CompetitorIntakeTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.raw = self.root / "raw"
        self.raw.mkdir()

    def write_metadata(self, *rows):
        with (self.raw / "metadata.csv").open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)

    def test_template_lists_all_ids_as_missing(self):
        (self.raw / "metadata.csv").write_bytes((ROOT / "raw/metadata.template.csv").read_bytes())
        result = inventory(self.root)
        self.assertEqual(result["metadata_rows"], 68)
        self.assertEqual(len(result["missing_metadata"]), 68)
        self.assertEqual(len(result["assets"]["covers"]["missing"]), 68)
        self.assertEqual(result["errors"], [])

    def test_partial_intake_keeps_videos_of_same_book_distinct(self):
        self.write_metadata(
            dict(video_id="V001", book_id="B001", transcript_file="transcripts/V001.md",
                 views="0", captured_at="2026-11-09T12:00:00+08:00"),
            dict(video_id="V002", book_id="B001", member_only="true"),
        )
        (self.raw / "transcripts").mkdir()
        (self.raw / "transcripts/V001.md").write_text("transcript fixture", encoding="utf-8")
        result = inventory(self.root)
        self.assertEqual(result["populated_metadata"], ["V001", "V002"])
        self.assertEqual(result["assets"]["transcripts"]["received"], ["transcripts/V001.md"])
        self.assertEqual(result["warnings"], [])
        self.assertEqual(result["errors"], [])

    def test_invalid_values_and_file_references(self):
        self.write_metadata(
            dict(video_id="V001", duration_seconds="NaN", likes="-2", member_only="yes",
                 cover_file="../V001.jpg", published_at="2026-11-09T12:00:00+08:00",
                 captured_at="2026-11-08T12:00:00+08:00"),
            dict(video_id="V001"),
            dict(video_id="V069"),
        )
        errors = "\n".join(inventory(self.root)["errors"])
        for marker in ("duration_seconds", "likes", "member_only", "cover_file",
                       "capture precedes", "V001'", "V069'", "missing or empty"):
            self.assertIn(marker, errors)


if __name__ == "__main__":
    unittest.main()
