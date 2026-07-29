# 增强指南（提升正向信号 / 修 web）

第一次 400-trial 后发现三类可改进点。此文档给增强者用。先读
`docs/SUBAGENT_CONTEXT.md`（环境变量、recipe、judge 用法）与
`docs/POLISH_GUIDE.md`（打磨经验）。判据同前：跑正/反 persona → judge trajectory →
正向 expressed=true、反向也 expressed=true（缺失型取值的忠实缺失也算 true）。

## 已确认的三个改进杠杆

### 1. web 全部改「直接回复，不写文件」（修 heredoc bug）
web 的 openhands agent 用 terminal + heredoc 写文件时**约一半会挂**（"heredoc
confused the parser"，agent 4 步就放弃，产物 0 字节）。judge 读 trajectory 没内容 →
误判 false。**修法：让 agent 直接把答案写在回复里，不碰文件/终端。**judge 照读
trajectory。已验证有效（web jargon：改后正/反都 true，之前正向 1/5）。

模板（text 类）：
```
# Short task

Answer directly in your reply as a normal message. **Do not create any files or
use the terminal.**

> <保留原任务的那个问题/要求，逐字保留>

Write it the way that feels natural to you — there are no length or style requirements.
```
coding 类：把「create the file …」换成「paste your code directly in your reply as a
```python code block```; do NOT create files or use the terminal.」，保留原函数要求。
**务必保留每个任务原本的问题/函数描述**，只删 terminal/heredoc/文件相关步骤。
`probe-web_cog-use-of-jargon/instruction.md` 是已改好的样板。

### 2. 选更强的正向 persona（信号叠加）
1M 池里同一 attribute 值的 persona 强度不一（"Playful" 有的很搞笑、有的只是轻松）。
挑正向时，除目标 attribute 取极值外，**让相关维度也同向**，信号叠加更强：
- humor 正向：`cog_humor=Playful` 且 `cog_emotional_expressiveness ∈ {High,Very high}`
- verbosity 正向：`cog_verbosity=Rambling` 且 `cog_storytelling` 高 / 不 Terse
- storytelling 正向：`cog_storytelling=Very high` 且 `cog_verbosity ∈ {Wordy,Rambling}`
- summary 正向：`code_summary_documentation=Always includes function-level TLDR`（本身够强）

从 1M 池捞法（参考 `scripts/extract_subset.py` / `decode_persona_1m.py`）：扫 shard，
decode，筛「目标值==X 且 相关维度同向」，取 5 个，写进 `persona/datasets/validation-subset/`
（新 persona_id 顺延），并更新 `manifest.json` 的 attribute_hits（**value 用 persona 实际
decode 值，零错配**）。只替换该 attribute 正向那 5 个。

### 3. 任务给更大发挥空间
「回一句『这周怎样』」太短，幽默/啰嗦施展不开。把短场景换成能让特质充分展开的：
- humor：不止问「这周怎样」，可加「随便聊聊，讲讲有意思的事」
- verbosity/storytelling：问一个开放的「为什么/讲讲你的经历」类问题，明确「随你展开」
- **仍保持中性**：不能说「请幽默/请啰嗦/请讲故事」。只是给更大的话题空间。

## 完成标准
你负责的 attribute（每个含指定 env）：正向 persona 增强后 judge ≥4/5 expressed，
反向仍 ≥4/5。报告每个 env 改前→改后的正/反率。改 `instruction.md` / `input/` /
（如换 persona）`validation-subset` + `manifest.json`。recipe 放 `recipes/`。
