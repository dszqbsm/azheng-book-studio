"""V1 authoring support; no model calls and no benchmark transcript reads."""
import argparse,json,re
from pathlib import Path
from core import read,save,digest,record

def hanzi(s): return len(re.findall(r"[\u4e00-\u9fff]",s))
def check(plan,sources):
 issues=[];chapters=plan.get("chapters",[]);ids=[c.get("chapter_id") for c in chapters]
 if not 3<=len(plan.get("proposals",[]))<=5: issues.append("proposal_count")
 if not chapters or len(set(ids))!=len(ids): issues.append("chapter_ids")
 if plan.get("mode") not in list("ABCDEFGH") or not plan.get("mode_selection_rationale"): issues.append("mode_selection")
 if sum(c.get("target_hanzi",0) for c in chapters)!=plan.get("minutes",30)*300: issues.append("budget_total")
 for i,c in enumerate(chapters):
  cid=c.get("chapter_id","?")
  for key in ["title","question","interpretation","transition_question","emotion_role","fact_notes","target_hanzi"]:
   if not c.get(key): issues.append(f"{cid}:missing_{key}")
  evidence=c.get("evidence",[])
  if not evidence: issues.append(f"{cid}:missing_evidence")
  for sid in evidence:
   if sid not in sources: issues.append(f"{cid}:unknown_evidence:{sid}")
   elif sources[sid].get("status")!="verified": issues.append(f"{cid}:unverified_evidence:{sid}")
  if i+1<len(chapters) and c.get("transition_question")!=chapters[i+1].get("question"): issues.append(f"{cid}:broken_transition")
 return issues

def prepare(p):
 p=Path(p);plan=read(p/"writing-plan.json");sources=read(p/"research/sources.json");issues=check(plan,sources)
 (p/"chapters").mkdir(exist_ok=True);(p/"writing-tasks").mkdir(exist_ok=True)
 proposals="\n\n".join(f"## {x['title']}\n问题：{x['question']}\n观点：{x['answer']}\n理由：{x['reason']}\n素材：{x['evidence']}\n缺口：{x['gaps']}" for x in plan["proposals"])
 (p/"topic-proposals.md").write_text(proposals,encoding="utf-8")
 (p/"outline.md").write_text("# "+plan["core_question"]+"\n主模式："+plan["mode"]+"；"+plan["mode_selection_rationale"]+"\n\n"+"\n\n".join(json.dumps(c,ensure_ascii=False,indent=2) for c in plan["chapters"]),encoding="utf-8")
 for c in plan["chapters"]:
  save(p/"writing-tasks"/(c["chapter_id"]+".json"),dict(rules=["references/writing-dna-v1.md","references/narrative-structures-v1.md"],core_question=plan["core_question"],chapter=c,sources={sid:sources[sid] for sid in c.get("evidence",[]) if sid in sources},instruction="写原创纯口播，明确解释与引文边界；未核验不得引作事实；段尾自然交给下一问。"))
 save(p/"plan-check.json",dict(issues=issues,ready=not issues));return issues

def review(p):
 p=Path(p);plan=read(p/"writing-plan.json");issues=check(plan,read(p/"research/sources.json"));texts=[];counts={};paragraphs={}
 for c in plan["chapters"]:
  f=p/"chapters"/(c["chapter_id"]+".md")
  if not f.exists(): issues.append(c["chapter_id"]+":missing_chapter");continue
  t=f.read_text(encoding="utf-8").strip();texts.append(t);counts[c["chapter_id"]]=hanzi(t)
  if not .8*c["target_hanzi"]<=hanzi(t)<=1.2*c["target_hanzi"]: issues.append(c["chapter_id"]+":length_budget")
  for paragraph in re.split(r"\n\s*\n",t):
   n=re.sub(r"\s+","",paragraph)
   if len(n)>=30:
    if n in paragraphs: issues.append(c["chapter_id"]+":repeated_paragraph:"+paragraphs[n])
    else: paragraphs[n]=c["chapter_id"]
 script="\n\n".join(texts);target=p/"script.md"
 if target.exists() and target.read_text(encoding="utf-8")!=script: save(p/"script-history"/(digest(target)+".json"),dict(text=target.read_text(encoding="utf-8")))
 target.write_text(script,encoding="utf-8")
 report=dict(status="needs_review" if issues else "structural_checks_passed",issues=issues,chapter_hanzi=counts,total_hanzi=hanzi(script),target_hanzi=plan["minutes"]*300,estimated_minutes=hanzi(script)/300,actual_audio_minutes=None,ready_for_voice=False,manual_review_required=["事实与引文逐条核对","正文语义衔接","开头结尾闭环","六维0至5分人工评分"],scope="deterministic structural checks; not semantic or factual certification")
 save(p/"script-review.json",report);(p/"script-review.md").write_text("# 统稿检查\n"+json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
 if (p/"project_state.json").exists(): record(p,"script",target,{"writing-plan.json":digest(p/"writing-plan.json"),**{str(f.relative_to(p)):digest(f) for f in (p/"chapters").glob("*.md")}})
 return report
if __name__=="__main__":
 ap=argparse.ArgumentParser();ap.add_argument("command",choices=["prepare","review"]);ap.add_argument("project",type=Path);args=ap.parse_args();print(json.dumps((prepare if args.command=="prepare" else review)(args.project),ensure_ascii=False,indent=2))
