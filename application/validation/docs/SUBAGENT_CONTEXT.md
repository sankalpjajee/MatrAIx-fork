# Subagent 打磨任务 — 完整背景

你在为 **MatrAIx persona-adherence validation** 打磨 probe task。背景：验证 persona
的某个 attribute 是否真的驱动 agent 行为（例：persona 说"写代码不留注释" → 让它写代码
→ 产物真没注释）。设计是 **10 attribute × 4 env（survey/chat/web/osapp-linux）**，每个用
A/B（attribute 正向 vs 反向 persona）对照。

**你负责一个 attribute 的四个 env。** 目标：把四个 env 的 task 打磨到「正向 persona 和
反向 persona 跑出来，LLM-judge 能明显、干净地分开」。

## 仓库
`/mnt/nvme/jintao/project/matraix/matraix-community-fork`（下面路径都相对它）

## 判据（唯一）
跑 1 正 + 1 反 persona → 各出 trajectory → 用 judge → **正向 expressed=true 且反向也
干净体现反向值**（如 No-comments 反向要真的零注释）。**不看 reward**（reward 是任务完成
度，与判读无关；只要 agent 产出了 trajectory 就能 judge）。

## 金标准（照它做，已四 env 达标）
`application/validation/tasks/probe-{survey,chat,web,osapp-linux}_code-comment-style/`
读它们的 `instruction.md` / `input/` 学风格。

## 五条打磨经验（血泪教训）
1. 任务要让 persona **实际产出**能体现该 attribute 的东西。**每个 attribute 用它专属的
   任务**——不要套 fizzbuzz！politeness→写请求；humor→回消息；register→写给朋友/正式邮件；
   verbosity→答开放题；storytelling→解释"为什么"；jargon→解释技术概念；emoji→写评价/消息；
   code_naming→写函数看变量名；code_summary→写函数看有无 docstring/TLDR。
2. instruction **中性**：绝不能说出 attribute 方向（不能说"请多写注释/请简洁/请礼貌"）——
   那是作弊。只描述任务，让 persona 的属性自发显现。
3. **反向也要干净**：不要用"展示你的风格/让风格显出来"这种措辞——它会诱导 agent 往正向
   加料，污染反向。用中性的"按你平时的方式做"。
4. **任务不要有无关场景污染**：chat 的 `input/context.md`、`input/protocol.md` 默认是 acme
   客服快递场景，必须改成与你任务一致的中性场景，否则 persona 被带偏（血泪教训：反向
   No-comments 被客服场景+展示措辞诱导加了注释）。
5. **env 特有坑**：
   - osapp-linux（computer-1 桌面）：instruction 告诉终端怎么开（Ctrl+Alt+T）+ heredoc 写
     文件示例，降低操作负担；否则 agent 忙于操作、属性被稀释。
   - web（openhands）：instruction 明确"用 terminal 工具写文件"+ heredoc；recipe 里
     `max_iterations: 20`。
   - chat（persona-claude-code + acme sidecar）：让 persona 在**第一条消息**就产出内容，
     再 continue 一轮。

## 环境变量（跑前 export）
```bash
cd /mnt/nvme/jintao/project/matraix/matraix-community-fork
T=$(grep '^GITHUB_COPILOT_TOKEN=' /mnt/nvme/jintao/project/fastedit/fastedit/.env | sed -E "s/^[^=]*=//; s/['\"]//g" | tr -d ' ')
export CAPI_API_KEY="$T" CAPI_BASE_URL="https://api.githubcopilot.com"
REPO_ROOT=$(pwd)
export PYTHONPATH="$REPO_ROOT:$REPO_ROOT/environment/runtime:$REPO_ROOT/packages/playground/src:$REPO_ROOT/application/playground"
```
- survey 额外：`export MATRIX_SURVEY_TASK_PATH=$REPO_ROOT/application/validation/tasks/<task>`
- web 额外：`export OPENAI_API_KEY=$T OPENAI_BASE_URL=$CAPI_BASE_URL LLM_API_KEY=$T LLM_BASE_URL=$CAPI_BASE_URL`
- osapp 额外：`export OPENAI_API_KEY=$T OPENAI_BASE_URL=$CAPI_BASE_URL`
- chat 额外：`unset ANTHROPIC_API_KEY; export ANTHROPIC_AUTH_TOKEN=$T ANTHROPIC_BASE_URL=$CAPI_BASE_URL`
  （**关键**：chat 必须 AUTH_TOKEN→Bearer，不能 API_KEY→x-api-key，否则 400）

## recipe 模板（每 env agent/model 不同）
```yaml
job_name: <job>
jobs_dir: jobs
n_attempts: 1
n_concurrent_trials: 1
environment: { type: docker, delete: true }
agents: [{ name: <AGENT>, model_name: <MODEL>, kwargs: { persona_path: persona/datasets/validation-subset/persona_<ID>.yaml <, EXTRA> } }]
tasks: [{ path: application/validation/tasks/<task> }]
```
- survey: AGENT=`persona-json-survey`  MODEL=`anthropic/claude-opus-4-8`  EXTRA=(无)
- web:    AGENT=`persona-openhands-sdk` MODEL=`openai/claude-opus-4.8`   EXTRA=`, max_iterations: 20`
- osapp:  AGENT=`persona-computer-1`    MODEL=`openai/claude-opus-4.8`   EXTRA=`, api_base: https://api.githubcopilot.com`
- chat:   AGENT=`persona-claude-code`   MODEL=`claude-opus-4.8`          EXTRA=(无)

跑：`rm -rf jobs/<job> && uv run harbor run -c <recipe>`（osapp/web 慢，2–5min）

## 找你的 attribute 的正/反 persona
```bash
python3 -c "import json;m=json.load(open('persona/datasets/validation-subset/manifest.json'))
for pol in ['positive','negative']:
  print(pol,[p['persona_id'] for p in m['personas'] for h in p['attribute_hits'] if h['attribute']=='<ATTR>' and h['polarity']==pol])"
```

## judge
```bash
python3 application/validation/scripts/judge_adherence.py jobs/<job> --attribute <ATTR> --value "<X 或 Y 的取值>"
```

## 交付
四个 env 的 task instruction/input 打磨到位（正反 judge 干净分开），并报告：每个 env 的
正/反 judge 结果（expressed + 证据一句话）。task 目录已存在（`probe-<env>_<attr-dashes>`），
你**改它们的 instruction.md / input/**，不要新建。
