from pathlib import Path
import uuid, shutil
from core import read, images, status, record, digest

def export(p,width=1080,height=1920,fps=30):
 import pyJianYingDraft as d
 p=Path(p).resolve();b=images(p)
 if not all(x["valid"] for x in status(p)["artifacts"].values()): raise ValueError("Stale artifacts; regenerate affected stages")
 a=read(p/"audio/final.json");name="book_"+uuid.uuid4().hex[:12]
 root=p/"draft";script=d.DraftFolder(str(root)).create_draft(name,width,height,fps,maintrack_adsorb=False)
 materials=root/name/"materials";materials.mkdir()
 def copy(f):
  f=p/f;t=materials/(digest(f)[:16]+f.suffix);shutil.copy2(f,t);return str(t)
 script.append_track(d.TrackSpec(d.TrackType.video,"Images"))
 for s in b["shots"]:
  start=round(s["start"]*1000000);duration=round(s["end"]*1000000)-start
  seg=d.VideoSegment(d.VideoMaterial(copy(s["image"])),d.Timerange(start,duration),volume=0)
  seg.add_keyframe(d.KeyframeProperty.uniform_scale,0,1.05)
  seg.add_keyframe(d.KeyframeProperty.uniform_scale,duration-1,1.15)
  script.add_segment(seg,"Images")
 script.append_track(d.TrackSpec(d.TrackType.audio,"Narration"))
 mat=d.AudioMaterial(copy(a["file"]));script.add_segment(d.AudioSegment(mat,d.Timerange(0,mat.duration)),"Narration");script.save()
 record(p,"draft",root/name/"draft_content.json",{"storyboard.json":digest(p/"storyboard.json"),"audio/final.json":digest(p/"audio/final.json"),**{s["image"]:digest(p/s["image"]) for s in b["shots"]}})
 return str(root/name)
