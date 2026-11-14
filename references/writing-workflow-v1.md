# V1 数据约定
writing-plan.json包含minutes、core_question、core_answer、mode（A—H）、mode_selection_rationale、proposals、chapters。
新计划填写 book_type，根据本期切入角度选 story（文学叙事）、history（历史与制度）、biography（人物传记）或 ideas（思想与处世）。旧计划缺少该字段时继续沿用原主模式。
proposals每项title/question/answer/reason/evidence/gaps；章节每项chapter_id/title/question/evidence（来源ID数组）/interpretation/transition_question/emotion_role/target_hanzi/target_minutes/fact_notes。evidence是V1 story_or_evidence的机器字段。问题接力约定：transition_question与下一章question相同；正文允许自然改写，另作人工语义审稿。
research/sources.json为来源ID到{title,url,locator,status,notes}映射。verified表示本次实际核对；pending表示待核对。现代假设案例须在notes明确，不作为原书事实。
prepare不会自动写正文；Codex读取任务逐章写入chapters/ID.md。review只合并存在章节，报告缺章并保留旧稿；不会把部分稿件标成定稿。原V0.1 studio.py接口不变。
