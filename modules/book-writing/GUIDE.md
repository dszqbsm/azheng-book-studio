# 讲书写作

## 第一步是交付 Gemini 写作提示词

选定书目或选篇后，按 [单段提示词规则](../../references/writing-dna-v3.md#给-gemini-的单段提示词) 输出一段可直接复制到 Gemini 新会话的提示词。先定本期一个核心问题，并在提示词中写明开头直接进入与它相关的故事。收到稿件后接着审稿和定稿。已有文稿的期次从审稿或用户指定的阶段接续。

## 审稿

先读开头几句话，确认已经进入具体故事，再沿正文检查人物的行动、选择或例证如何回答提示词里的核心问题。核对引文、事实、叙事和 [V2 十维量表](../../references/script-quality-rubric-v2.md)。缺章或未满预算的样稿标明实际范围。

## Codex 逐章写作

用户指定由 Codex 写稿时，按 [叙事结构](../../references/narrative-structures-v2.md) 和 [计划格式](../../references/writing-workflow-v1.md) 准备 3 至 5 个选题、章节卡和来源表。运行 `writing.py prepare`，写入 `chapters/编号.md`，再运行 `review` 生成纯口播 `script.md` 和报告。重写单章后重新统稿。脚本检查结构、显式衔接、重复段落和预算。
