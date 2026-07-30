# validation-subset

Persona adherence validation 用的 persona 子集（第二个 validation / probe 任务）。

- **68 个唯一 persona**，覆盖 **10 个目标 attribute**，每个 attribute **5 正(X) + 5 反(Y)**。
  （68 < 100，因为 22 个 persona 同时满足多个 attribute 的正/反条件——见 manifest 的
  `attribute_hits`。）
- 来源：`HFXM/MatrAIx-Wiki-Personas` + `HFXM/MatrAIx-Amazon-Review-Personas-10K`
  两源提取（各 persona 完整 1290-attribute 提取，转成本仓库标准 yaml 时只保留非空维度）。
- 格式与 `matraix-persona-dev-sample` 一致：`persona_XXXX.yaml`（`dimensions:` = id→value）+ `manifest.json`。
  `source` 字段记录原始来源 `wiki:<qid>` / `amazon:<user_id>`。

## 10 个目标 attribute（X 正 / Y 反）

| attribute | X (positive) | Y (negative) |
|---|---|---|
| tech_savviness | Digital native | Reluctant |
| expertise_gap | Expert testing the system | Novice asking expert |
| decision_style | Analytical | Intuitive |
| risk_tolerance | Risk-seeking | Cautious |
| trust_level | Trusting | Skeptical |
| register | Formal / standard | Colloquial |
| economic_motivation | Premium-seeking | Indifferent |
| trait_empathy | Strong | Absent |
| trait_curiosity | Strong | Absent |
| cog_feedback_receptiveness | High | Low |

## 用法

在 probe 任务的 `persona_strategy.json` 里，把 `dimensionFilters` 锁到某个目标
attribute 的两端（X/Y），`stratifyFields` 放该 attribute，`sampleSize: 10` → 自动
取该 attribute 的 5 正 + 5 反。`manifest.json` 的 `attribute_hits` 列出每个 persona
被选中的 attribute 与 polarity，便于核对。

## 待补

StackOverflow + synthetic 两源在 gated repo `MatrAIx2026/Existing_Data`，拿到访问权
后按同逻辑补进来（attribute 名单与 5+5 结构不变）。
