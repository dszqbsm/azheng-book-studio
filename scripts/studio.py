import argparse,json,os,asyncio,uuid,subprocess
from pathlib import Path
from core import *


def voice_api_key():
 key = os.environ.get("AZHENG_DOUBAO_API_KEY", "").strip()
 if key:
  return key
 local_scripts = Path(__file__).resolve().parents[2] / ".agents/skills/story-studio/scripts"
 if (local_scripts / "voice_settings.py").is_file():
  import sys
  sys.path.insert(0, str(local_scripts))
  try:
   from voice_settings import read_api_key
   return read_api_key()
  except Exception:
   raise ValueError("Unable to read the local Doubao credential. Check it with voice_settings.py check.") from None
  finally:
   sys.path.pop(0)
 raise ValueError("Missing AZHENG_DOUBAO_API_KEY; never print credentials")


def main():
 ap=argparse.ArgumentParser();ap.add_argument("command",choices=["init","status","script","audio","merge-audio","storyboard","queue","images","draft","doctor","voice","asr"]);ap.add_argument("project",type=Path);ap.add_argument("--input",type=Path);ap.add_argument("--title",default="新书");ap.add_argument("--minutes",type=int,default=30);ap.add_argument("--style",default="historical-realism");ap.add_argument("--paid-authorized",action="store_true");args=ap.parse_args();p=args.project.resolve();c=args.command
 if c=="init": result=init(p,args.title,args.minutes)
 elif c=="status": result=status(p)
 elif c=="script": result=ingest(p,args.input)
 elif c=="audio": result=audio(p,args.input)
 elif c=="merge-audio":
  from merge_audio import merge_audio
  result=merge_audio(p,args.input)
 elif c=="storyboard": result=storyboard(p,args.input,args.style)
 elif c=="images": result=images(p)
 elif c=="queue":
  b=read(p/"storyboard.json")
  image_format={"aspect_ratio":b["image_aspect_ratio"]} if "image_aspect_ratio" in b else {}
  result=[dict(id=s["id"],prompt=s["prompt"],status=s["status"],references=[],**image_format) for s in b["shots"] if not s.get("image")]
  save(p/"images/queue.json",result)
 elif c=="draft":
  from draft import export
  result=export(p,chapter_timeline=args.input.resolve() if args.input else None)
 elif c=="doctor":
  import importlib.util
  result={n:bool(shutil.which(n)) for n in ["ffmpeg","ffprobe","coli"]};result.update({n:bool(importlib.util.find_spec(n)) for n in ["PIL","pyJianYingDraft","websockets"]})
 elif c=="voice":
  from doubao_protocol import synthesize,validate_audio
  if not args.paid_authorized: raise ValueError("Paid synthesis disabled; confirm chapter text and parameters before --paid-authorized")
  profile=read(Path(__file__).resolve().parents[1]/"configs/voice.json");key=voice_api_key()
  text=args.input.read_text(encoding="utf-8-sig");out=p/"audio"/(uuid.uuid4().hex+".mp3")
  asyncio.run(synthesize(text,profile,key,out));duration=validate_audio(out,tool("ffprobe"),tool("ffmpeg"));save(out.with_suffix(".json"),dict(text_sha256=digest(args.input),audio_sha256=digest(out),profile=profile,duration=duration));result=str(out)
 elif c=="asr":
  a=read(p/"audio/final.json");cmd=[tool("coli"),"asr","-j","--model","sensevoice","--language","zh",str(p/a["file"])];proc=subprocess.run(cmd,capture_output=True,text=True,encoding="utf-8",check=True);result=json.loads(proc.stdout);save(p/"subtitles"/("raw_"+uuid.uuid4().hex+".json"),result)
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":
 try: main()
 except Exception as e:
  print(json.dumps({"ok":False,"error":str(e) if isinstance(e,ValueError) else type(e).__name__},ensure_ascii=False));raise SystemExit(2)
