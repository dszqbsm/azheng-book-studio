import json, hashlib, uuid, shutil, subprocess, re, math
from pathlib import Path

DEFAULT_IMAGE_ASPECT_RATIO = "16:9"

def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding="utf-8-sig"))
def save(p,data):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():
  h=p.parent/".history";h.mkdir(exist_ok=True);shutil.copy2(p,h/(p.name+"."+uuid.uuid4().hex))
 temp=p.with_suffix(p.suffix+".tmp");temp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8");temp.replace(p)
def init(p,title,minutes=30):
 p=Path(p).resolve()
 if p.exists(): raise ValueError("Project already exists")
 if not 20<=minutes<=40: raise ValueError("Target duration must be 20–40 minutes")
 for d in ["chapters","audio","subtitles","images","cover","draft","research","benchmarks"]: (p/d).mkdir(parents=True,exist_ok=True)
 save(p/"book.json",dict(title=title,author="",publisher="",edition="",isbn="",product_url="",recommendation="",topic="",minutes=minutes,mode="A",image_aspect_ratio=DEFAULT_IMAGE_ASPECT_RATIO))
 save(p/"project_state.json",dict(schema=1,artifacts={}))
 for name in ["outline.md","script.md"]: (p/name).write_text("",encoding="utf-8")
 return str(p)
def record(p,stage,file,inputs):
 p=Path(p);s=read(p/"project_state.json");s["artifacts"][stage]=dict(file=str(Path(file).relative_to(p)),sha256=digest(file),inputs=inputs);save(p/"project_state.json",s)
def status(p):
 p=Path(p);s=read(p/"project_state.json")
 for a in s["artifacts"].values():
  a["valid"]=all((p/f).is_file() and digest(p/f)==h for f,h in {a["file"]:a["sha256"],**a["inputs"]}.items())
 return s
def ingest(p,source):
 p=Path(p);text=Path(source).read_text(encoding="utf-8-sig");parts=re.split(r"(?m)^## +",text)
 chapters=[x.strip() for x in parts if x.strip()]
 if not chapters: raise ValueError("Empty script")
 for i,c in enumerate(chapters,1): save(p/"chapters"/f"{i:03}.json",dict(id=f"{i:03}",text=c))
 target=p/"script.md"
 if target.exists() and target.read_text(encoding="utf-8"): save(p/"chapters"/"previous-script.json",dict(text=target.read_text(encoding="utf-8")))
 target.write_text(text,encoding="utf-8");record(p,"script",target,{})
 sentences=[s.strip() for s in re.split(r"[。！？]",text) if len(s.strip())>10]
 return dict(chapters=len(chapters),hanzi=len(re.findall(r"[\u4e00-\u9fff]",text)),target=read(p/"book.json")["minutes"]*300,repeated=list({s for s in sentences if sentences.count(s)>1}))
def tool(name):
 v=shutil.which(name)
 if not v: raise ValueError(f"Missing dependency: {name}; configure PATH or use configured media Python")
 return v
def audio(p,source):
 p=Path(p);source=Path(source)
 result=subprocess.run([tool("ffprobe"),"-v","error","-show_format","-show_streams","-of","json",str(source)],capture_output=True,text=True,encoding="utf-8",check=True)
 info=json.loads(result.stdout);duration=float(info["format"]["duration"])
 if not math.isfinite(duration) or duration<=0 or not any(s["codec_type"]=="audio" for s in info["streams"]): raise ValueError("Invalid audio")
 subprocess.run([tool("ffmpeg"),"-v","error","-xerror","-i",str(source),"-f","null","-"],capture_output=True,check=True)
 target=p/"audio"/(digest(source)[:16]+source.suffix);shutil.copy2(source,target) if source.resolve()!=target.resolve() else None
 meta=p/"audio"/"final.json";save(meta,dict(file=str(target.relative_to(p)),sha256=digest(target),duration=duration))
 record(p,"audio",meta,{"script.md":digest(p/"script.md"),str(target.relative_to(p)):digest(target)});return read(meta)
def storyboard(p,cues_path,style):
 p=Path(p);a=read(p/"audio/final.json");c=read(cues_path)
 ratio=read(p/"book.json").get("image_aspect_ratio",DEFAULT_IMAGE_ASPECT_RATIO)
 width,height=image_ratio_parts(ratio)
 composition="横构图" if width>height else "竖构图" if width<height else "方形构图"
 if not status(p)["artifacts"]["audio"]["valid"]: raise ValueError("Stale audio")
 if c["audio_sha256"]!=a["sha256"] or c["script_sha256"]!=digest(p/"script.md"): raise ValueError("Version mismatch")
 previous=0
 if not c.get("cues"): raise ValueError("Empty cues")
 for cue in c["cues"]:
  if not all(math.isfinite(cue[k]) for k in ["start","end"]) or cue["start"]<previous or cue["end"]<=cue["start"] or cue["end"]>a["duration"]+0.001: raise ValueError("Invalid cue timing")
  previous=cue["end"]
 shots=[];start=0;group=[]
 for cue in c["cues"]:
  group.append(cue)
  kind=cue.get("type","knowledge");limit={"conflict":8,"history":12,"knowledge":16,"atmosphere":20}[kind]
  if cue["end"]-start>=limit or cue is c["cues"][-1]:
   end=cue["end"] if cue is not c["cues"][-1] else a["duration"]
   text="".join(x["text"] for x in group)
   shots.append(dict(id=f"s{len(shots)+1:04}",start=start,end=end,narration=text,type=kind,image=None,status="pending",prompt=f"{style}；{ratio} {composition}；{text}；时代服饰准确，书房或历史意象，主体清晰，无文字无水印"));start=end;group=[]
 data=dict(schema=1,audio_sha256=a["sha256"],script_sha256=digest(p/"script.md"),duration=a["duration"],image_aspect_ratio=ratio,shots=shots)
 validate(data);save(p/"storyboard.json",data);record(p,"storyboard",p/"storyboard.json",{"script.md":digest(p/"script.md"),"audio/final.json":digest(p/"audio/final.json")});return data
 def_unused=0
def validate(b):
 end=0;ids=set()
 for s in b["shots"]:
  if s["id"] in ids or not all(math.isfinite(s[k]) for k in ["start","end"]) or abs(s["start"]-end)>0.001 or s["end"]<=s["start"]: raise ValueError("Timeline overlap/gap/invalid ID")
  ids.add(s["id"]);end=s["end"]
 if not ids or abs(end-b["duration"])>0.001: raise ValueError("Timeline duration mismatch")
 return True
def image_ratio_parts(ratio):
 if not isinstance(ratio,str) or not re.fullmatch(r"[1-9][0-9]*:[1-9][0-9]*",ratio):
  raise ValueError("Image aspect ratio must have the form width:height")
 return tuple(map(int,ratio.split(":")))

def images(p):
 from PIL import Image
 p=Path(p);b=read(p/"storyboard.json");validate(b)
 for s in b["shots"]:
  if not s.get("image"): raise ValueError("Missing image: "+s["id"])
  f=(p/s["image"]).resolve()
  if not f.is_relative_to(p.resolve()): raise ValueError("Image outside project")
  with Image.open(f) as im:
   im.verify()
  with Image.open(f) as im:
   if min(im.size)<64: raise ValueError("Image too small")
   if "image_aspect_ratio" in b:
    width,height=image_ratio_parts(b["image_aspect_ratio"])
    if abs(im.width*height-im.height*width)>max(width,height):
     raise ValueError(f"Image aspect ratio mismatch: {s['id']} ({im.width}x{im.height}, expected {b['image_aspect_ratio']})")
 return b
