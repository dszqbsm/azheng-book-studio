# azheng-book-studio V0.1
独立源码，不依赖已安装 Story Studio。明确指定读取本目录 SKILL.md 即可在当前聊天使用；本次未安装到全局技能目录，因此不保证自动发现。

执行：使用现有媒体Python运行 `scripts/studio.py --help`。init PROJECT --title 增广贤文；script PROJECT --input script.md；doctor PROJECT；其余见SKILL.md。PROJECT使用独立创作目录，不能放在技能源码中。

核心仅Python标准库；媒体需要FFmpeg/ffprobe，图片需要Pillow，草稿需要pyJianYingDraft==0.3.1及MediaInfo，配音需要websockets，ASR需要Coli及sensevoice模型。利用已有环境，通过PATH提供工具，不重复安装。配音密钥独立读取AZHENG_DOUBAO_API_KEY，不读取原技能私有安全配置。
测试：`PY -m unittest discover -s tests -v`（在本目录执行）。测试产物置系统临时目录，明确为模拟。
当前限制：自动精确音文对齐、SRT、章节拼接命令、配置全量贯通、智能场景分类和生图服务适配尚未完整实现；详见交付报告。不能据此宣称生产全链路验收。


## V1 写作升级
新创作以references/writing-dna-v1.md和narrative-structures-v1.md为主。运行scripts/writing.py prepare PROJECT生成校验后方案、大纲与写作任务；Codex写各章后运行review PROJECT统稿。数据格式见references/writing-workflow-v1.md。实际示例见examples/caigentan-v1，只有前两章样稿，非完整30分钟文稿。8项离线测试通过；语义与事实审稿仍由Agent负责。
