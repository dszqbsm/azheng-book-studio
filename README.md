# azheng-book-studio

项目写作与审稿参考 [Writing DNA V3.0](references/writing-dna-v3.md)。发给 Gemini 的[单段提示词](references/writing-dna-v3.md#给-gemini-的单段提示词)可以直接在新会话使用，重点写清开头钩子和整篇的收听目标。发布封面使用 [系列听书封面 V2](references/cover-style-v2.md)。研究证据见 [68 条视频研究](references/competitor-research-68/README.md)。

## 发布前一次性交付

准备发布时按 [竞品研究发布规则](modules/publishing/GUIDE.md#按竞品研究制作发布内容) 组织整套交付，并在交付前对照定稿和最终时长检查四平台标题与两张封面。

发布阶段统一交付：小红书≤20字、抖音≤30字、视频号≤16字、快手不限字数的四平台标题，简介、推荐标签、≤12字章名及真实时间、合集建议，以及系列听书风格的两张封面（3:4为1080×1440，4:3为1440×1080）。不默认生成其他比例，不自动发布。完整规范见 modules/publishing/GUIDE.md，封面规范见 references/cover-style-v2.md。

Agent准备完整发布内容与成图后，用已配置Python执行 `PY /技能绝对路径/scripts/publishing.py /项目绝对路径/publishing/package_v01.json --package --output /项目绝对路径/publishing/发布包_v01.md`。校验通过后一次性提供发布包与两张封面。脚本负责校验和组装，不代写文案、不调用生图服务；输入及模板字段见发布指南。
独立源码，不依赖已安装 Story Studio。明确指定读取本目录 SKILL.md 即可在当前聊天使用；本次未安装到全局技能目录，因此不保证自动发现。

执行：使用现有媒体Python运行 `scripts/studio.py --help`。init PROJECT --title 增广贤文；script PROJECT --input script.md；doctor PROJECT；其余见SKILL.md。PROJECT使用独立创作目录，不能放在技能源码中。

核心仅Python标准库；媒体需要FFmpeg/ffprobe，图片需要Pillow，草稿需要pyJianYingDraft==0.3.1及MediaInfo，配音需要websockets，ASR需要Coli及sensevoice模型。利用已有环境，通过PATH提供工具，不重复安装。配音默认使用悠悠君子 2.0 和 seed-tts-2.0。优先读取 AZHENG_DOUBAO_API_KEY，在历史人物视频工作区也可复用 Story Studio 已保存的本地凭据。
测试：`PY -m unittest discover -s tests -v`（在本目录执行）。测试产物置系统临时目录，明确为模拟。
当前限制：自动精确音文对齐、SRT、章节拼接命令、配置全量贯通和智能场景分类尚未完整实现。详见交付报告。

## 生图

开始实际生图前选择 Codex 内置生图或 DevPoolAi · gpt-image-2.6。选择后可接续已有队列，按镜生成并登记。DevPoolAi 调用支持上传角色参考图。只生成分镜或提示词时直接运行队列流程。[生图指南](modules/image-generation/GUIDE.md)


## V3.0 写作

现有写作计划及 A–H 编码继续适用。运行 `scripts/writing.py prepare PROJECT` 生成校验后的方案、大纲与写作任务，逐章写稿后运行 `review PROJECT` 统稿。数据格式见 [写作工作流](references/writing-workflow-v1.md)，示例见 `examples/caigentan-v1` 的前两章。人工审稿先过 V3 的开头钩子，再核对语义、事实与 V2 十维评分。
