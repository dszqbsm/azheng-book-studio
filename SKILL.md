---
name: azheng-book-studio
description: 围绕一本书制作20至40分钟中文深度解说，支持独立研究写稿、章节配音、真实时间分镜、生图任务及剪映草稿。
---

# 阿正讲书工坊
新一期配音顺序：先完成除开场外的章节与结语，测量真实音频总时长，再按已确认音色语速估计开场时长，确定全片约数分钟。开场第一句固定为“XX分钟听完一本书，今天我们听《XXX》。”，其中XX为预计完整音频四舍五入到整数分钟的值，不使用初稿目标时长。开场内其他时长描述必须一致。最后生成开场、合并、重新测时；若最终四舍五入分钟数改变，只重做开场，保留正文。记录正文时长、开场时长、合并时长和版本哈希。试听可先试正文一小段。只有用户明确要求才提前合成开场。
所有命令使用本技能 scripts/studio.py 的绝对路径；工作目录参数 PROJECT 必须在源码目录外。使用已配置媒体 Python，不安装或调用 Story Studio。首次读 README.md 了解接口与限制。

只执行用户请求阶段；定稿后才可配音，付费前核对章节文本和配置，本次开发不得付费。真实完成情况用 status 检查；缺服务只输出任务队列，不声称已生成。

新讲书创作必须先读 references/writing-dna-v1.md 和 references/narrative-structures-v1.md，作为主要规则。旧 writing-dna.md 仅供V0.1追溯，不覆盖V1。日常不读取 benchmark/transcripts。方法研究先读 benchmark/INDEX.md 和 analysis/ten-sample-analysis-v1.md；只有验证具体争议时按metadata定位单篇原稿；数据比较才读metrics.csv。对标不作为新书事实来源。整理 research/sources.json：来源URL、版本页码、摘录、观点、核验状态；每个核心论点关联来源。生成3至5角度，选择一个贯穿问题，选择A至E结构，写 outline.md，分章写 chapters，整合纯口播 script.md。引用原著与现代阐释分开，不编造原句。

命令：`PY scripts/studio.py COMMAND PROJECT [OPTIONS]`
- init --title 书名 --minutes 30：创建独立一期。
- script --input 文稿：检查字数、重复并生成章节记录。修改单章后重新整合并执行；不调用配音。
- voice --input 章节文本：默认拒绝付费；确认后 --paid-authorized。单章重试选该文件，保存新音频版本。记录参数哈希；不自动重试收费请求。
- audio --input 最终MP3：导入并完整解码检查。章节音频用FFmpeg concat后导入；不要用旧章节拼接记录冒充最终版本。
- asr：用户确认最终音频无误后，本地 Coli 保存原始JSON；Agent自动对照对应版本定稿、校正转录文字并转换真实cue，详见modules/audio-alignment/GUIDE.md。不要求用户逐条核对识别错字。不得用字数估算时间。
- storyboard --input cues.json --style 画风：按真实cue边界动态聚合；人工复核场景类型、切点与人物连续性。
- queue：生成生图任务；调用当前宿主生图工具或外部服务后填入每镜image相对路径，真实检查 images；单镜重做保留旧文件。
- draft：创建唯一新版本剪映草稿，无字幕；不自动导出MP4，不声称剪映播放验收。
- status / doctor：检查版本或依赖。失效阶段从上游重新生成，已有效产物复用。

人物年龄服装、年代地点、参考图与场景ID需在 research/visual-bible.json 记录并补全每镜独立提示词。未指定画风先询问。商业资料只记录 book.json，不擅加荐书话术。

## V1 写作可执行路径
读取 modules/book-writing/GUIDE.md。Codex负责原创提案和逐章创作，脚本负责校验、任务生成、统稿与报告，不使用假定的模型API。
1. 整理 research/sources.json，创建 writing-plan.json（格式见references/writing-workflow-v1.md），先交付3至5选题及理由。
2. `PY scripts/writing.py prepare PROJECT` 校验计划并输出选题、大纲和逐章任务。缺资料列gap，不编造引文。
3. 依任务逐章写 chapters/编号.md，修改章节可只重新写该文件。
4. `PY scripts/writing.py review PROJECT` 合并现有章节到script.md并生成script-review.json/md。未齐章、预算不足或证据未核验时标记未就绪，不自动进入配音。
完整30分钟大纲不等于30分钟成稿。脚本的衔接检查是显式字段一致性检查，语义、事实、六维评分由Codex另行审稿，不伪装算法已理解全文。
