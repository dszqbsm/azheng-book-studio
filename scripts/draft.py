from pathlib import Path
import uuid, shutil, math
from core import read, images, status, record, digest

def export(p,width=None,height=None,fps=None,chapter_timeline=None):
 import pyJianYingDraft as d
 p=Path(p).resolve();b=images(p)
 if not all(x["valid"] for x in status(p)["artifacts"].values()): raise ValueError("Stale artifacts; regenerate affected stages")
 a=read(p/"audio/final.json");name="book_"+uuid.uuid4().hex[:12]
 config_root=Path(__file__).resolve().parents[1]/"configs"
 defaults=read(config_root/"defaults.json")
 width=defaults["width"] if width is None else width
 height=defaults["height"] if height is None else height
 fps=defaults["fps"] if fps is None else fps
 chapter_data=None
 state_path=p/"STORY_PROJECT.json"
 if chapter_timeline is None and state_path.is_file():
  chapter_timeline=read(state_path).get("chapter_timeline")
 if chapter_timeline is None and (p/"subtitles/chapter_timeline.json").is_file():
  chapter_timeline="subtitles/chapter_timeline.json"
 if chapter_timeline is not None:
  from chapter_bar import load_chapters
  chapter_path=(p/chapter_timeline).resolve()
  if not chapter_path.is_relative_to(p):
   raise ValueError("Chapter timeline must be inside the project")
  chapter_data=load_chapters(p,chapter_path,a,fps)
 enabled=read(p/"book.json").get("subtitles",defaults.get("subtitles",True))
 captions=None
 if enabled:
  from subtitles import clean_cues, validate_short_cues
  caption_path=p/"subtitles/captions.json"
  if not caption_path.exists(): raise ValueError("Missing aligned short-sentence subtitles/captions.json; complete subtitle stage first")
  captions=clean_cues(read(caption_path))
  if captions.get("audio_sha256")!=a["sha256"] or captions.get("script_sha256")!=digest(p/"script.md"): raise ValueError("Subtitle audio/script version mismatch")
  if not captions["cues"] or captions["cues"][-1]["end"]>a["duration"]+1/fps: raise ValueError("Subtitle timing outside narration")
  validate_short_cues(captions["cues"])
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
   script.add_segment(d.TextSegment(cue["text"],d.Timerange(start,end-start),style=d.TextStyle(size=style["size"],bold=style["bold"],color=tuple(style["color"]),align=1,auto_wrapping=style["auto_wrapping"],max_line_width=style["max_line_width"]),border=d.TextBorder(color=tuple(style["border_color"]),width=style["border_width"]),clip_settings=d.ClipSettings(transform_y=style["position_y"])),"Subtitles")
 if chapter_data:
  from chapter_bar import add_chapter_bar
  add_chapter_bar(d,script,materials,width,height,fps,*chapter_data)
 from brand_overlay import add_brand_overlay
 seal_asset=config_root.parent/"assets/azheng-seal.png"
 add_brand_overlay(d,script,seal_asset,materials,width,height,end,bool(chapter_data))
 script.save()
 inputs={"storyboard.json":digest(p/"storyboard.json"),"audio/final.json":digest(p/"audio/final.json"),**{s["image"]:digest(p/s["image"]) for s in b["shots"]}}
 if captions:
  inputs["subtitles/captions.json"]=digest(caption_path)
 if chapter_data:
  inputs[str(chapter_path.relative_to(p))]=digest(chapter_path)
 record(p,"draft",root/name/"draft_content.json",inputs)
 return str(root/name)
