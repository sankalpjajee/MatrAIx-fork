# application/validation

Persona **adherence validation**（第二个 validation / AgentPersonaBench 前身）的工作区。

目标：验证 persona 的 attribute 是否真的驱动 agent 行为——例如「persona 说写代码不留注释 →
让它写代码 → 产物真的没注释」。设计上是 **10 个 attribute × 4 个 env（Survey / Chat / Web /
OS-App）= 40 个 probe task**，每个 task 用 A/B（attribute 正向 vs 反向 persona）对照。

## 目录

| 子目录 | 内容 |
|---|---|
| `tasks/` | probe task（标准 harbor task：task.toml/instruction/questionnaire/persona_strategy/tests） |
| `recipes/` | harbor job recipe（指定 task + persona + 模型） |
| `scripts/` | 抽 persona / 解码 / 跑 probe 的脚本 |
| `results/` | 跑出来的产物 + 报告 |
| `docs/` | 说明文档 |

## 数据

- persona 子集：`persona/datasets/validation-subset/`（10 attribute × 5 正 + 5 反，
  从 1M 四源 coreset `MatrAIx2026/MatrAIx_Persona_1M_Public_Release` 抽取）。
- 抽取脚本：`scripts/extract_subset.py`（+ `decode_persona_1m.py` 解 persona_codes 编码）。

## 怎么跑一个 probe（已固化，一条命令）

```bash
# 模型走 CAPI（Copilot 网关）的 Opus 4.8，不需要 ANTHROPIC_API_KEY
application/validation/scripts/run_probe.sh <recipe.yaml> [survey_task_path]

# 例：跑 code_comment_style 的正向 survey probe
application/validation/scripts/run_probe.sh \
  application/validation/recipes/survey-pos.yaml \
  application/validation/tasks/probe-survey_code-comment
```

`run_probe.sh` 封装了所有踩过的坑：CAPI token 加载、`PYTHONPATH`（host-native persona agent
要 import `backend`）、`MATRIX_SURVEY_TASK_PATH`（survey host 路径）。产物写到 `jobs/<job_name>/`。

## 判读（写没写注释怎么自动判）

`probe-survey_code-comment/tests/test_state.py` 是 **rule-based verifier**：解析产物代码，
数注释行，输出 `comment_ratio` 和 `wrote_comments`(yes/no)，grouped by `code_comment_style`。
- **rule-based 够用**的场景：coding comment 这类信号硬、可数的 attribute。
- **需要 LLM-judge** 的场景：文体/语气/共情这类软性 attribute（rule 数不出来）——TODO。

## 当前进度

| env | agent | CAPI 状态 | code_comment_style probe |
|---|---|---|---|
| Survey | `persona-json-survey`（host-native） | ✅ 已通 | ✅ **跑通**：正 ratio>0 / 反 ratio=0 |
| Chat | `persona-claude-code`（容器 CLI） | CAPI `/v1/messages` 已验证可达；待接线 | 建了 task，未跑通 |
| Web | `persona-openhands-sdk` | 待验证 | 未建 |
| OS-App | `persona-computer-1` | memory 标 TODO | 有 verbosity 版，未接 CAPI |

> 关键发现：CAPI 网关 `api.githubcopilot.com` **同时支持** OpenAI 兼容 `/chat/completions`
> 和 Anthropic 原生 `/v1/messages`（后者可喂给容器里的 Claude Code CLI，用
> `ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN`）。这是把 chat/osapp 容器 agent 接上 CAPI 的路子。

## 扩到 40 个

四个 env 的 agent 路径各不同，且不是每个 (attribute, env) 都天然成立（如 code_comment_style
只在写代码的任务里体现）。所以先各 env 跑通一个最小 coding probe（证明 agent×CAPI 可用），
再按 attribute 批量复制 + 换 `persona_strategy.json` 的 `dimensionFilters`。
