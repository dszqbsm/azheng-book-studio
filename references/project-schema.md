项目schema=1。book.json记录书名作者出版社版本ISBN商品链接推荐理由主题时长模式。project_state.json各artifact记录file、sha256及inputs路径哈希；status动态校验直接输入。

用户试听确认最终音频后，由Agent对照同版本定稿校正转录文字，不再要求用户逐条人工核对。原始ASR、校正文字与修改记录分开保留；真实时间映射和异常处理遵循modules/audio-alignment/GUIDE.md。文字校正不得冒充音频修复或逐字试听。
cues.json结构：{"audio_sha256":"最终音频哈希","script_sha256":"全文哈希","cues":[{"start":0,"end":16,"text":"真实识别且核对文字","type":"knowledge","chapter":"001"}]}。cue必须来自真实ASR，人工核对全文及时间后才进入分镜；当前不自动强制对齐。storyboard每镜id/start/end/narration/type/prompt/image/status；时间单位秒。所有素材相对项目根目录。项目JSON覆盖前保留.history；音频、草稿使用唯一名称。
