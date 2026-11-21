"""Prepare writing tasks and review drafts against the current writing rules."""
import argparse,json,re
from pathlib import Path
from core import read,save,digest,record

WRITING_RULES = ["references/writing-dna-v3.md", "references/narrative-structures-v2.md"]

BOOK_STRUCTURES = {
 "story": "文学叙事：围绕人物处境、选择与后果推进。每章交代这次选择怎样改变下一章的处境。",
 "history": "历史与制度：从一个具体疑问切入，按时间关口或不同人物的案例呈现成因、利益冲突与结果。",
 "biography": "人物传记：选取能改变人物命运的节点，交代当时的选项、取舍与代价，用关键场景串起人生。",
 "ideas": "思想与处世：从具体两难切入，按理解顺序引入概念，每个核心概念配原文证据和可理解的案例。",
}
STRUCTURE_REVIEW = [
 "先念一遍开头，确认听众能说出接下来最想知道什么，第一场戏或案例能自然接上，正文能兑现",
 "按本期书型逐章检查：每章推动一个变化，或回答一个独立的子问题",
 "按本期文稿形式决定解读分量，借助现代类比时用具体事例讲清适用条件",
 "结语用正文细节回收开场问题或画面，按本期文稿形式收束",
]

def hanzi(s): return len(re.findall(r"[\u4e00-\u9fff]",s))
def check(plan,sources):
 issues=[];chapters=plan.get("chapters",[]);ids=[c.get("chapter_id") for c in chapters]
 if not 3<=len(plan.get("proposals",[]))<=5: issues.append("proposal_count")
 if not chapters or len(set(ids))!=len(ids): issues.append("chapter_ids")
 if plan.get("mode") not in list("ABCDEFGH") or not plan.get("mode_selection_rationale"): issues.append("mode_selection")
 if "book_type" in plan and (not isinstance(plan["book_type"],str) or plan["book_type"] not in BOOK_STRUCTURES): issues.append("book_type")
 if sum(c.get("target_hanzi",0) for c in chapters)!=plan.get("minutes",30)*300: issues.append("budget_total")
 if plan.get("minutes",30)>30: issues.append("duration_limit")
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
 book_type=plan.get("book_type")
 structure=BOOK_STRUCTURES.get(book_type) if isinstance(book_type,str) else None
 if structure is None: structure="沿用本期主模式，根据本期任务选用 Writing DNA V3.0 对应的文稿形式。"
 (p/"chapters").mkdir(exist_ok=True);(p/"writing-tasks").mkdir(exist_ok=True)
 proposals="\n\n".join(f"## {x['title']}\n问题：{x['question']}\n观点：{x['answer']}\n理由：{x['reason']}\n素材：{x['evidence']}\n缺口：{x['gaps']}" for x in plan["proposals"])
 (p/"topic-proposals.md").write_text(proposals,encoding="utf-8")
 (p/"outline.md").write_text("# "+plan["core_question"]+"\n主模式："+plan["mode"]+"；"+plan["mode_selection_rationale"]+"\n\n"+"\n\n".join(json.dumps(c,ensure_ascii=False,indent=2) for c in plan["chapters"]),encoding="utf-8")
 for c in plan["chapters"]:
  save(p/"writing-tasks"/(c["chapter_id"]+".json"),dict(rules=WRITING_RULES,core_question=plan["core_question"],book_type=book_type,body_structure=structure,structure_review=STRUCTURE_REVIEW,chapter=c,sources={sid:sources[sid] for sid in c.get("evidence",[]) if sid in sources},instruction="写原创纯口播，区分解释与引文，以核实资料为依据，段尾自然交给下一问。"))
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
 if hanzi(script)>9000: issues.append("script_over_30_minute_budget")
 if target.exists() and target.read_text(encoding="utf-8")!=script: save(p/"script-history"/(digest(target)+".json"),dict(text=target.read_text(encoding="utf-8")))
 target.write_text(script,encoding="utf-8")
 report=dict(status="needs_review" if issues else "structural_checks_passed",issues=issues,book_type=plan.get("book_type"),chapter_hanzi=counts,total_hanzi=hanzi(script),target_hanzi=plan["minutes"]*300,estimated_minutes=hanzi(script)/300,actual_audio_minutes=None,ready_for_voice=False,manual_review_required=["事实与引文逐条核对","正文语义衔接",*STRUCTURE_REVIEW,"按 references/script-quality-rubric-v2.md 完成十维1至10分人工评分"],scope="deterministic structural checks; not semantic or factual certification")
 save(p/"script-review.json",report);(p/"script-review.md").write_text("# 统稿检查\n"+json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
 if (p/"project_state.json").exists(): record(p,"script",target,{"writing-plan.json":digest(p/"writing-plan.json"),**{str(f.relative_to(p)):digest(f) for f in (p/"chapters").glob("*.md")}})
 return report
if __name__=="__main__":
 ap=argparse.ArgumentParser();ap.add_argument("command",choices=["prepare","review"]);ap.add_argument("project",type=Path);args=ap.parse_args();print(json.dumps((prepare if args.command=="prepare" else review)(args.project),ensure_ascii=False,indent=2))
