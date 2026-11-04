# 实施报告 — V0.1（部分实现，未完成全部验收）

实际保存位置为当前项目根目录 azheng-book-studio。全部新源码、配置、文档及测试在此目录；没有修改原 Story Studio 或既有人物工程。测试输出使用系统临时目录。

已创建 SKILL.md、README.md、scripts/{core,studio,draft,doubao_protocol}.py、configs/{defaults,voice}.json、九个 modules/*/GUIDE.md、五份 references、examples/script.md、tests/test_core.py 和许可声明。

已实现：项目初始化；书籍商业信息记录；文稿分章、汉字统计、重复句提示；产物哈希与直接输入版本检查；JSON历史备份；音频导入完整解码检查接口；真实cue驱动长镜头聚合与时间连续性检查；生图队列输出；图片完整性检查；独立豆包V3协议与显式收费开关；Coli原始识别调用；图片/音频轨道与缩放关键帧草稿接口。写作采用独立Agent指令及Writing DNA V0.1，不是Python自动写作器。

未完成：上游Git提交溯源（网络克隆未完成）；精确音文匹配、SRT生成、自动局部对齐重试；章节合并及章节增量缓存自动编排；配置文件全部贯通（当前分镜时长和导出尺寸为接口默认参数）；自动场景分类与人物一致性算法；生图服务适配；实际剪映草稿运行验证；封面自动生成。状态仅校验已登记产物及其直接输入，不是完整依赖图调度器。分镜提示词需要Agent补全年代人物信息后才能正式生图。当前不能声称已完成用户全部验收。

参考源码审查：本地安装副本 README.md、SKILL.md、LICENSE、agents/openai.yaml、history-image/GUIDE.md、render-history-video/scripts/export_jianying.py、align_with_coli.py、scripts/doubao_tts.py。历史及人物Writing DNA未复制。上游安装副本没有Git HEAD，不能将其称为某个确定SHA。临时克隆目标为系统TEMP下azheng-story-reference，初次网络连接失败，提权尝试仍未取得HEAD；未修改全局Git信任设置。

直接提取：scripts/doubao_tts.py 截至main之前的二进制协议、流式会话、synthesize和validate_audio函数，保存在scripts/doubao_protocol.py，删除studio_runtime及voice_settings依赖。依赖Python标准库、websockets和FFmpeg工具。保留MIT Copyright (c) 2026 konlu，见LICENSES-story-studio.txt。由于来源为本地适配副本，无法保证与远端当前提交一致。草稿模块独立重写，参考pyJianYingDraft轨道、Timerange和uniform_scale关键帧用法；没有复制整个渲染模块。Coli保留本地CLI调用方式，不复制字数估算时间。

实际测试：使用现有媒体Python执行 `-m unittest discover -s azheng-book-studio/tests -v`，5项全部通过：项目创建与版本变化、时间缺口交叉及NaN、依赖缺失、模拟cue分镜及图片映射和版本不符、协议帧构造。模拟音频是显式标注的字节fixture，不是真实可播放音频；未宣称通过真实配音测试。未测试真实收费接口、真实ASR、完整音频导入和真实剪映导出。

依赖诊断：媒体Python中Pillow、pyJianYingDraft、websockets可导入；当前PATH中FFmpeg、ffprobe、Coli不可发现。项目既有runtime.json记录这些工具的位置，可以在运行前配置PATH复用；本技能不把原Skill作为运行时依赖。skill-creator quick_validate因缺PyYAML未能运行，未安装新依赖。

已有语音配置check返回profile_ready=true/api_key_present=true，未输出密钥，未联网鉴权，未发送收费请求。新技能为独立配置，真实调用需要AZHENG_DOUBAO_API_KEY环境变量；尚未接入既有DPAPI凭据存储，勿要求用户在聊天中粘贴密钥。

当前调用：在Codex中说“读取 azheng-book-studio/SKILL.md，使用阿正讲书工坊，为《增广贤文》创建30分钟项目，先研究和写稿，不配音”。本次按要求只保存在指定目录，没有安装到已装技能目录，因此不保证$名称自动发现。CLI使用配置媒体Python调用scripts/studio.py --help，项目参数给源码外的新目录。

后续Writing DNA：将合法对标原稿放创作目录benchmarks，按references/benchmark-methodology.md逐篇标注与交叉统计，再版本化更新规则。本次未声称读取用户其他聊天的十篇逐字稿。


# 第二轮：Writing DNA V1.0 接入（2026-11-04）

本节为最新写作能力状态，前文V0.1记录保留用于追溯。

修改文件：SKILL.md、modules/book-research/GUIDE.md、modules/book-writing/GUIDE.md、README.md；新增scripts/writing.py、references/writing-workflow-v1.md、tests/test_writing.py、examples/caigentan-v1/。用户提供的V1知识库和十篇原件未改写，旧V0.1 writing-dna.md及原脚本测试保留。

实际读取：现有Skill、V0.1 DNA、core.py、原测试及研究/写作指南；两份V1规则、benchmark INDEX、metadata与分析摘要。日常流程改为优先两份V1规则，本轮未读取原始对标逐字稿。metrics.csv不参与日常写作生成。

真实实现：Agent原创提案→结构章节卡→prepare校验并输出topic-proposals.md、outline.md、writing-tasks/*.json→Agent逐章写chapters/*.md→review合并纯口播script.md并输出script-review.json/md。章卡包含question/evidence/transition_question/target_hanzi等字段，evidence对应V1的story_or_evidence。支持单章修改后重跑统稿。此能力由Codex创作与本地确定性工具共同完成，无外部文本模型调用器；prepare本身不自动创造书籍内容。

自动检查范围：3至5方案、模式、总字数预算、章节必要字段、来源ID及核验状态、相邻问题接力字段一致、缺章、字数预算和完全重复段落。字段一致不保证正文语义连贯；近义改写重复、事实真假、伪引文、情绪弧线仍需Agent逐条审阅。报告明确保留manual_review_required和ready_for_voice=false，不用结构测试替代六维人工评分。

示例：examples/caigentan-v1中实际保存3个选题、A主模式选择理由、6章9000汉字/30分钟完整预算大纲、前两章纯口播样稿及合稿。两章625和655汉字，共1280字，按300字/分钟仅估算4.27分钟，未生成音频。其余四章未写，报告正确标记缺章与预算不足。这里的30分钟指大纲目标，不能称30分钟定稿或成片。

独立资料：核对Chinese Text Project及维基文库公开搜索结果中的菜根谭条文线索，URL和定位见research/sources.json；仅确认相关条文存在，纸本底本、条次、异文仍待复核。未虚构作者传记或历史案例。样稿中办公室协作明确是假设，现代使用方法明确归于讲述者阐释。原文线索不等于其现代解释被学术验证。

测试命令：现有媒体Python -m unittest discover -s azheng-book-studio/tests -v。实际结果8项通过（原5项+新增3项）。新增A：禁止打开transcripts路径仍可由已准备的原创计划输出创作方案和任务；此为本地编排验证，不是模型写作质量评测。新增B：故意断线和缺证据可检出；重复段落和缺章可检出。测试不调用收费接口。

调用示例：读取本Skill后，让Codex按两份V1规则创建独立一期sources和writing-plan；运行scripts/writing.py prepare PROJECT；逐章写稿后review PROJECT。示例因属于测试交付物，按本轮要求放在源码examples内，真实节目仍使用源码外的独立工作目录。

下一步：核对采用的菜根谭纸本版本，扩展独立证据材料，完成其余章节并人工六维审稿后才进入配音。前轮精确音文对齐、SRT及真实剪映验收限制仍未在本轮解决。本轮没有配音、生图、转录或剪映成片执行。
