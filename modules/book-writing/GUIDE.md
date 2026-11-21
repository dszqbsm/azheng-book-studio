# V3.0 写作

Gemini 写稿使用 [Writing DNA V3.0](../../references/writing-dna-v3.md) 中的单段提示词，给出当期原著资料，要求直接输出完整口播。开头类型和正文结构由写作者按本期内容选择。

Codex 逐章写作时，按 [叙事结构](../../references/narrative-structures-v2.md) 和 [计划格式](../../references/writing-workflow-v1.md) 准备 3 至 5 个选题、章节卡和来源表。运行 `writing.py prepare`，写入 `chapters/编号.md`，再运行 `review` 生成纯口播 `script.md` 和报告。重写单章后重新统稿。

脚本检查结构、显式衔接、重复段落和预算。人工先念一遍开头，确认听众想追问什么，以及正文从哪里接上，再复核引文、事实、叙事和 [V2 十维量表](../../references/script-quality-rubric-v2.md)。缺章或未满预算的样稿标明实际范围。
