from pathlib import Path
import uuid, shutil, math
from core import read, images, status, record, digest

def export(p,width=1080,height=1920,fps=30):
 import pyJianYingDraft as d
 p=Path(p).resolve();b=images(p)
 if not all(x["valid"] for x in status(p)["artifacts"].values()): raise ValueError("Stale artifacts; regenerate affected stages")
 a=read(p/"audio/final.json");name="book_"+uuid.uuid4().hex[:12]
 config_root=Path(__file__).resolve().parents[1]/"configs"
 defaults=read(config_root/"defaults.json")
 enabled=read(p/"book.json").get("subtitles",defaults.get("subtitles",True))
 captions=None
 if enabled:
  from subtitles import clean_cues
  caption_path=p/"subtitles/captions.json"
  if not caption_path.exists(): raise ValueError("Missing aligned short-sentence subtitles/captions.json; complete subtitle stage first")
  captions=clean_cues(read(caption_path))
  if captions.get("audio_sha256")!=a["sha256"] or captions.get("script_sha256")!=digest(p/"script.md"): raise ValueError("Subtitle audio/script version mismatch")
  if not captions["cues"] or captions["cues"][-1]["end"]>a["duration"]+1/fps: raise ValueError("Subtitle timing outside narration")
 root=p/"draft";script=d.DraftFolder(str(root)).create_draft(name,width,height,fps,maintrack_adsorb=False)
 materials=root/name/"materials";materials.mkdir()
 def copy(f):
  f=p/f;t=materials/(digest(f)[:16]+f.suffix);shutil.copy2(f,t);return str(t)
 script.append_track(d.TrackSpec(d.TrackType.video,"Images"))
 for index,s in enumerate(b["shots"]):
  start=round(round(s["start"]*fps)*1000000/fps)
  end=round((math.ceil(s["end"]*fps) if index==len(b["shots"])-1 else round(s["end"]*fps))*1000000/fps)
  duration=end-start
  seg=d.VideoSegment(d.VideoMaterial(copy(s["image"])),d.Timerange(start,duration),volume=0)
  inward=s.get("motion","slow_push_in")!="slow_pull_out"
  seg.add_keyframe(d.KeyframeProperty.uniform_scale,0,1.05 if inward else 1.15)
  seg.add_keyframe(d.KeyframeProperty.uniform_scale,duration-1,1.15 if inward else 1.05)
  script.add_segment(seg,"Images")
 script.append_track(d.TrackSpec(d.TrackType.audio,"Narration"))
 mat=d.AudioMaterial(copy(a["file"]));script.add_segment(d.AudioSegment(mat,d.Timerange(0,mat.duration)),"Narration")
 if captions:
  style=read(config_root/"subtitles.json")
  script.append_track(d.TrackSpec(d.TrackType.text,"Subtitles"))
  for cue in captions["cues"]:
   start=round(round(cue["start"]*fps)*1000000/fps);end=round(round(cue["end"]*fps)*1000000/fps)
   if end<=start: raise ValueError("Subtitle shorter than one frame")
   script.add_segment(d.TextSegment(cue["text"],d.Timerange(start,end-start),style=d.TextStyle(size=style["size"],bold=style["bold"],color=tuple(style["color"]),align=1,auto_wrapping=style["auto_wrapping"],max_line_width=style["max_line_width"]),border=d.TextBorder(width=style["border_width"]),clip_settings=d.ClipSettings(transform_y=style["position_y"])),"Subtitles")
 script.save()
 record(p,"draft",root/name/"draft_content.json",{"storyboard.json":digest(p/"storyboard.json"),"audio/final.json":digest(p/"audio/final.json"),**{s["image"]:digest(p/s["image"]) for s in b["shots"]}})
 if captions:
  state=read(p/"project_state.json");state["artifacts"]["draft"]["inputs"]["subtitles/captions.json"]=digest(p/"subtitles/captions.json")
  from core import save
  save(p/"project_state.json",state)
 return str(root/name)
