# V3.0 写作

给 Gemini 生成提示词时，按[单段提示词规则](../../references/writing-dna-v3.md#给-gemini-的单段提示词)交付一段在新会话可直接使用的文字，包含本期内容和原著出处、篇幅、收听目标及完整口播的交付要求。重点写清开头几句话要留住听众，正文要自然延续期待。切入点、结构和解读落点由 Gemini 决定。用户明确要求采用指定 DNA 或模板时，再在本期提示词中引用。

Codex 逐章写作时，按 [叙事结构](../../references/narrative-structures-v2.md) 和 [计划格式](../../references/writing-workflow-v1.md) 准备 3 至 5 个选题、章节卡和来源表。运行 `writing.py prepare`，写入 `chapters/编号.md`，再运行 `review` 生成纯口播 `script.md` 和报告。重写单章后重新统稿。

脚本检查结构、显式衔接、重复段落和预算。人工先念一遍开头，确认听众想追问什么，以及正文从哪里接上，再复核引文、事实、叙事和 [V2 十维量表](../../references/script-quality-rubric-v2.md)。缺章或未满预算的样稿标明实际范围。
