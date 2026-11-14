---
name: azheng-book-studio
description: 围绕一本书制作20至40分钟中文深度解说，支持独立研究写稿、章节配音、真实时间分镜、生图任务及剪映草稿。
---

# 阿正讲书工坊
用户要求“按 azheng 准备发布”或“给我发布前需要的东西”时，默认执行 [发布指南的竞品研究规则](modules/publishing/GUIDE.md#按竞品研究制作发布内容)。先从本期定稿提炼一个可兑现的问题，再联动四平台标题、简介、标签、章节、合集和两张封面。交付前目视复核标题与成图的分工、书名可读性、正文承诺和实际片长。
完整发布包为固定收尾阶段：用户要求准备发布时，一次性交付四平台标题及字数、简介、标签、≤12字章节名及真实起始时间、合集归属或新建建议，以及两张完整封面。封面固定3:4（1080×1440）、4:3（1440×1080），复用 references/cover-style-v1.md 的历史写实墨青金色电影海报风格，不再默认制作其他比例。执行 modules/publishing/GUIDE.md，一次交齐后再回复，不拆成多轮索要；仅缺必要真实信息时明确缺口。不自动发布。
所有平台发布章节名统一不超过12字，尽量简短；章序、标点、空格若写入名称也计数，时间戳不计入名称。每次交付前校验，保留完整口播标题与真实时间。发布前还需给出合集归属建议：有合适已有合集则优先使用，否则建议新建并提供名称、简介；未知已有合集时不假定其存在，不自动创建或发布。
章节时间必须来自最终音频/视频的真实时间轴，涵盖开场、正文各章和结语；不得按字数估时或沿用修补前的时间。
发布标题生成规则：每次生成或修改发布标题，必须同时输出小红书、抖音、视频号、快手四个平台适配版本，不能只交付通用标题。小红书≤20字、抖音≤30字、视频号≤16字，快手不设字数上限；标点、数字、字母、空格均计入字数。交付前校验并标注字数，超限应重写，不机械截断。规则配置见 configs/publishing.json，发布流程见 modules/publishing/GUIDE.md。
新一期配音顺序：先完成除开场外的章节与结语，测量真实音频总时长，再按已确认音色语速估计开场时长，确定全片约数分钟。开场第一句固定为“XX分钟听完一本书，今天我们听《XXX》。”，其中XX为预计完整音频四舍五入到整数分钟的值，不使用初稿目标时长。开场内其他时长描述必须一致。最后生成开场、合并、重新测时；若最终四舍五入分钟数改变，只重做开场，保留正文。记录正文时长、开场时长、合并时长和版本哈希。试听可先试正文一小段。只有用户明确要求才提前合成开场。
章节标题属于正式口播内容：默认朗读每章的章序与完整标题，以及结语标题；仅移除 Markdown 的 # 等格式标记，不得删除标题所在首行。只有用户明确要求时才省略标题。配音前核对标题与正文均在合成文本中，详见 modules/voice/GUIDE.md。
配音默认使用豆包语音合成大模型 2.0 的悠悠君子音色 `zh_male_youyoujunzi_uranus_bigtts`，资源 `seed-tts-2.0`，请求省略 model。读取 configs/voice.json，凭据来源见 modules/voice/GUIDE.md。
所有命令使用本技能 scripts/studio.py 的绝对路径；工作目录参数 PROJECT 必须在源码目录外。使用已配置媒体 Python。首次读 README.md 了解接口与限制。

只执行用户请求阶段；定稿后才可配音，付费前核对章节文本和配置，本次开发不得付费。真实完成情况用 status 检查；缺服务只输出任务队列，不声称已生成。

新讲书创作必须先读 references/writing-dna-v2.md 和 references/narrative-structures-v2.md。V1 结构库保留 A–H 编码，选定一个主模式，并可使用 V2 组合。日常不读取 benchmark/transcripts。方法研究先读 benchmark/INDEX.md 和 analysis/ten-sample-analysis-v1.md；只有验证具体争议时按metadata定位单篇原稿；数据比较才读metrics.csv。对标不作为新书事实来源。整理 research/sources.json：来源URL、版本页码、摘录、观点、核验状态；每个核心论点关联来源。生成3至5角度，选择一个贯穿问题，选择A至H结构，写 outline.md，分章写 chapters，整合纯口播 script.md。引用原著与现代阐释分开，不编造原句。

命令：`PY scripts/studio.py COMMAND PROJECT [OPTIONS]`
- init --title 书名 --minutes 30：创建独立一期。
- script --input 文稿：检查字数、重复并生成章节记录。修改单章后重新整合并执行；不调用配音。
- voice --input 章节文本：默认拒绝付费；确认后 --paid-authorized。单章重试选该文件，保存新音频版本。记录参数哈希；不自动重试收费请求。
- audio --input 最终MP3：导入并完整解码检查。章节音频用FFmpeg concat后导入；不要用旧章节拼接记录冒充最终版本。
- merge-audio --input 合并清单.json：按清单顺序合并章节，章间额外停顿默认0.5秒（configs/defaults.json 的 chapter_pause_seconds），不在首尾添加；记录真实时长与输入哈希，不为凑分钟数延长停顿，不调用付费合成。
- asr：用户确认最终音频无误后，本地 Coli 保存原始JSON；Agent对照同版本定稿校字，使用 `scripts/subtitles.py` 的 `caption_boundaries` 按句末、逗号和分号拆分，用真实词元时间落点。单卡引用保留成对引号，跨卡引用在显示层移除外引号。详见 modules/audio-alignment/GUIDE.md。不得用字数估算时间。
- storyboard --input cues.json --style 画风：按真实cue边界动态聚合；人工复核场景类型、切点与人物连续性。
- queue：生成生图任务。新分镜配图默认 16:9 横图，生图参数和逐镜提示词均使用分镜记录的比例。画面连续满幅，底部沿场景自然衔接，字幕在剪映独立叠加。用户要求继续配图时默认连续完成全部缺失镜头，不自行停在首张预览。逐张调用当前宿主生图工具或外部服务后保存到项目，填入每镜image相对路径并检查登记；已有有效图复用，单镜重做保留旧文件。详见modules/image-generation/GUIDE.md。
- draft：默认交付 16:9 横屏剪映草稿（1920×1080、30 fps），含白色粗体黑描边字幕。标准顺序为配音确认→本地转录→Agent按定稿校正→生成真实时间短句字幕→分镜与配图→含字幕剪映草稿。字幕制作是正式阶段，不必等用户再次要求；明确要求无字幕时才跳过。详见modules/video-editing/GUIDE.md。不自动导出MP4，不声称剪映播放验收。
- 动态章节条：使用最终配音的真实章节时间表，剪映草稿在画面顶部展示分段、当前章高亮及播放进度。接续时读取本期 chapter_timeline，缺失时从最终配音的 ASR 核对并保存 subtitles/chapter_timeline.json。草稿左上角默认全程叠加「阿正」竖印，有章节条时置于其下方。详见 modules/video-editing/GUIDE.md。
- status / doctor：检查版本或依赖。失效阶段从上游重新生成，已有效产物复用。

人物年龄服装、年代地点、参考图与场景ID需在 research/visual-bible.json 记录并补全每镜独立提示词。未指定画风先询问。商业资料只记录 book.json，不擅加荐书话术。

## V2.0 写作可执行路径
默认使用 [Writing DNA V2.0](references/writing-dna-v2.md)。第二轮方法依据见 [68 条视频研究](references/competitor-research-68/README.md) 和 [V1/V2 对照](references/writing-dna-v1-v2-comparison.md)。用户用 Gemini 写稿时，提示词指定 V2 文件和本期原著证据，要求输出完整口播。

读取 modules/book-writing/GUIDE.md。Codex负责原创提案和逐章创作，脚本负责校验、任务生成、统稿与报告，不使用假定的模型API。
1. 整理 research/sources.json，创建 writing-plan.json（格式见references/writing-workflow-v1.md），先交付3至5选题及理由。
2. `PY scripts/writing.py prepare PROJECT` 校验计划并输出选题、大纲和逐章任务。缺资料列gap，不编造引文。
3. 依任务逐章写 chapters/编号.md，修改章节可只重新写该文件。
4. `PY scripts/writing.py review PROJECT` 合并现有章节到script.md并生成script-review.json/md。未齐章、预算不足或证据未核验时标记未就绪，不自动进入配音。
完整30分钟大纲不等于30分钟成稿。脚本的衔接检查是显式字段一致性检查，语义、事实及 V2 十维评分由 Codex 另行审稿，不伪装算法已理解全文。

- 生图前逐段复核相邻分镜。若两镜表达的是同一个画面，后一镜没有新增可见的动作、表情、人物关系、关键物件或场景变化，就合并为一镜，使用一张图覆盖原两镜的真实时间范围，保留对应口播和字幕时间。仅改变机位、景别或轻微构图时，也按是否增加叙事信息判断。若中间有必要的叙事切点，保留切点，回到同一画面时复用已有图。并排检查已生成的近似画面，确认后同步更新分镜表和生图队列。
