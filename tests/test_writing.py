import unittest,tempfile,sys,copy
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from writing import check,prepare,review
from core import read,save
ROOT=Path(__file__).resolve().parents[1]
class WritingTests(unittest.TestCase):
 def fixture(self,p):
  plan=read(ROOT/"examples/caigentan-v1/writing-plan.json");sources=read(ROOT/"examples/caigentan-v1/research/sources.json")
  save(p/"writing-plan.json",plan);save(p/"research/sources.json",sources);return plan,sources
 def test_prepare_without_transcripts(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);self.fixture(p);original=Path.open
   def guarded(path,*a,**kw):
    if "transcripts" in path.parts: raise AssertionError("Raw benchmark read")
    return original(path,*a,**kw)
   with patch.object(Path,"open",guarded): self.assertEqual(prepare(p),[])
   self.assertTrue((p/"outline.md").exists());self.assertEqual(len(list((p/"writing-tasks").glob("*.json"))),6)
   task=read(p/"writing-tasks/001.json")
   self.assertEqual(task["rules"],["references/writing-dna-v2.md","references/narrative-structures-v2.md"])
   self.assertTrue(all((ROOT/rule).is_file() for rule in task["rules"]))
 def test_broken_transition_and_evidence(self):
  with tempfile.TemporaryDirectory() as t:
   plan,sources=self.fixture(Path(t));plan["chapters"][0]["transition_question"]="无关问题";plan["chapters"][1]["evidence"]=[]
   issues=check(plan,sources);self.assertIn("001:broken_transition",issues);self.assertIn("002:missing_evidence",issues)
 def test_book_type_reaches_writing_task_and_review(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);plan,sources=self.fixture(p)
   plan["book_type"]="ideas";save(p/"writing-plan.json",plan)
   self.assertEqual(prepare(p),[])
   self.assertIn("原文证据",read(p/"writing-tasks/001.json")["body_structure"])
   report=review(p)
   self.assertEqual(report["book_type"],"ideas")
   self.assertTrue(any("回收开场" in item for item in report["manual_review_required"]))
   plan["book_type"]="unknown"
   self.assertIn("book_type",check(plan,sources))
 def test_duplicate_and_incomplete_script(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);self.fixture(p);(p/"chapters").mkdir();text="这是明确用于测试重复段落识别的文字，我们用同一段内容放入不同章节，检查统稿是否发现问题。"
   for cid in ["001","002"]: (p/"chapters"/(cid+".md")).write_text(text,encoding="utf-8")
   report=review(p);self.assertTrue(any("repeated_paragraph" in x for x in report["issues"]));self.assertIn("003:missing_chapter",report["issues"]);self.assertFalse(report["ready_for_voice"])
