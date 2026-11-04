import unittest,tempfile,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from core import *
class CoreTests(unittest.TestCase):
 def test_project_and_versions(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/"episode";init(p,"测试书");source=Path(t)/"text.md";source.write_text("## 章节一\n为什么读书。\n## 章节二\n因为理解人生。",encoding="utf-8")
   result=ingest(p,source);self.assertEqual(result["chapters"],2);self.assertGreater(result["hanzi"],0);self.assertTrue(status(p)["artifacts"]["script"]["valid"])
   (p/"script.md").write_text("changed",encoding="utf-8");self.assertFalse(status(p)["artifacts"]["script"]["valid"])
 def test_timeline(self):
  b=dict(duration=20,shots=[dict(id="1",start=0,end=10),dict(id="2",start=10,end=20)])
  self.assertTrue(validate(b))
  for start in [9,11,float("nan")]:
   b["shots"][1]["start"]=start
   with self.assertRaises(ValueError): validate(b)
 def test_missing_dependency(self):
  with self.assertRaisesRegex(ValueError,"Missing dependency"): tool("azheng_nonexistent_dependency")
 def test_storyboard_and_images(self):
  from PIL import Image
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/"episode";init(p,"测试");(p/"script.md").write_text("示例",encoding="utf-8")
   (p/"audio/mock.wav").write_bytes(b"MOCK not real audio")
   save(p/"audio/final.json",dict(file="audio/mock.wav",sha256=digest(p/"audio/mock.wav"),duration=20))
   record(p,"audio",p/"audio/final.json",{"script.md":digest(p/"script.md")})
   cue=Path(t)/"cues.json";save(cue,dict(audio_sha256=digest(p/"audio/mock.wav"),script_sha256=digest(p/"script.md"),cues=[dict(start=0,end=10,text="一"),dict(start=10,end=20,text="二")]))
   b=storyboard(p,cue,"mock-style");self.assertTrue(validate(b))
   with self.assertRaisesRegex(ValueError,"Missing image"): images(p)
   Image.new("RGB",(108,192)).save(p/"images/mock.png")
   for shot in b["shots"]: shot["image"]="images/mock.png"
   save(p/"storyboard.json",b);self.assertEqual(len(images(p)["shots"]),1)
   wrong=read(cue);wrong["audio_sha256"]="wrong";save(cue,wrong)
   with self.assertRaisesRegex(ValueError,"Version mismatch"): storyboard(p,cue,"mock")
 def test_protocol(self):
  from doubao_protocol import pack
  self.assertGreater(len(pack(1,{})),8)
if __name__=="__main__": unittest.main()
