# 故纸观今 · 第二轮 68 条视频研究

当前已入库 68 条元数据、68 张主页卡片截图和 V001 的评论文件。第一轮 10 份逐字稿按用户确认直接复用，原件见 [V1 对标索引](../benchmark/INDEX.md)。另有 40 份本地转录初稿通过结构核验，18 条缺完整正文来源。详见 [转录核验记录](reports/asr-verification.md)。

研究转录使用 `PY scripts/competitor_asr.py INVENTORY --workers 1`，其中 `INVENTORY` 为豆包交付的 `transcript_source_inventory.csv` 绝对路径。分段结果保存在 `raw/asr/Vxxx/`，重跑按媒体哈希和分段时间复用。机器稿单独标记待听校，校对后再登记到逐字稿目录。

## 导入与校验

1. 按 [入库说明](raw/README.md) 放入真实材料并填写 `raw/metadata.csv`。若该文件缺失，从 `raw/metadata.template.csv` 复制一份。
2. 在技能仓库根目录，用项目配置的 Python 执行 `PY scripts/competitor_intake.py`。命令输出逐项已收、缺失、错误和告警。用 `--output datasets/inventory.local.json` 可保存新快照，已有同名文件时换新文件名或用 PowerShell 重定向更新。退出码 1 表示格式或引用错误，缺素材单独列出。
3. 每批取 5–8 条，在 `analysis/individual/Vxxx.md` 保存带定位的报告，并同步填写 `datasets/video-matrix.csv`。每批记录 ID、素材版本、已完成与缺口。样本不完整时按真实覆盖数出阶段结论。
4. 完成逐条编码后，按同题材、相近时长与发布后观察窗口做横向比较。先更新专题与汇总表，再出总报告。最后形成独立 V2 候选与 V1 对照，用户审核后才考虑接入生产。

## 证据与数据口径

- 逐条记录原始文件、行号或真实时间区间。封面必须打开实际图片，并记录构图与文字依据。文稿无时间轴时可按段落分析开头与结尾，秒级字段留空。
- 区分直接观察、跨样本规律、解释性推测和自有账号实验假设。规律注明样本 ID、分子、分母、反例和缺失数。评论注明采集时间、抽样方式和可见范围。
- 时间窗口按采集时刻减发布时间计算。会员、置顶、新发和未知状态分别标记。按可比组预先选分组窗口与高低表现阈值，报告样本量。播放量大于 0 且分子已知时才计算互动率。近似计数注明精度，未知留空。绝对互动与内容质量分别记录。
- 粉丝数按账号与采集时刻去重。缺历史快照时仅报告可见发布节奏。商业功能、购买意愿和实际销售分别取证。
- 先用少量样本统一标注口径，再逐批标注。分类允许多标签与新类型，新增类写清边界和反例。统一以 `|` 分隔多标签；空值代表未知，明确观察为无时写 `false` 或 0。

[仓库审查与初始清点](reports/intake-audit.md) · [首轮入库记录](reports/doubao-import.md) · [逐条报告模板](analysis/individual/TEMPLATE.md) · [升级路线图](reports/improvement-roadmap.md)

68 条逐条报告已写入 `analysis/individual/`。横向结果见 [研究总报告](reports/competitor-research-final.md) 和 [视频矩阵](datasets/video-matrix.csv)。正文覆盖 50 条，18 条只编码可见包装和数据。V2 规则均为独立候选，见 [V1/V2 对照](../writing-dna-v1-v2-comparison.md)。
