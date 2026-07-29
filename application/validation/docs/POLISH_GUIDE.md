# Attribute Probe 打磨手册（给打磨者）

目标：把一个 attribute 的**四个 env**（survey / chat / web / osapp-linux）probe task
打磨到「正向 persona 和反向 persona 跑出来，LLM-judge 能明显分开」。

**判据（唯一）**：跑 1 正 + 1 反 persona → 各出 trajectory → 用 `judge_adherence.py`
判读 → **正向 expressed=true 且反向明显更弱/false**。不看 reward（reward 是任务完成度，与我们无关）。

## 金标准参考
`code_comment_style` 四个 env 已打磨达标，照它的 instruction 风格做：
- `application/validation/tasks/probe-{survey,chat,web,osapp-linux}_code-comment-style/`

## 五条经验
1. 任务要让 persona **实际产出**能体现该 attribute 的东西（写代码 / 写一段文字 / 多轮对话）。
2. instruction **强锚定**：明确说「按你自己的习惯/风格写，让你的风格显出来，不要精简/中性版」。
   但**绝不能**直接说出 attribute 的方向（不能说“请多写注释”/“请简洁”）——那是作弊。
3. **osapp-linux**（computer-1 桌面）：instruction 要降低操作负担——告诉它终端怎么开
   （`Ctrl+Alt+T`），并给 heredoc 写文件示例，否则 agent 忙于找终端、风格被稀释。
4. **web**（openhands）：instruction 明确「用 terminal 工具写文件」+ heredoc 示例；recipe 里
   `max_iterations: 20`。
5. **chat**（persona-claude-code + acme sidecar）：让 persona 在**第一条消息**里就产出内容
   （如贴一段自己写的代码、或写一段话），再 continue 一轮。judge 只看 persona 发的内容。

## 每个 env 的 recipe 模板 + 环境变量

**通用环境变量**（跑前 export，token 从 fastedit .env 取）：
```bash
T=$(grep '^GITHUB_COPILOT_TOKEN=' /mnt/nvme/jintao/project/fastedit/fastedit/.env | sed -E "s/^[^=]*=//; s/['\"]//g" | tr -d ' ')
export CAPI_API_KEY="$T" CAPI_BASE_URL="https://api.githubcopilot.com"
REPO_ROOT=<repo>
export PYTHONPATH="$REPO_ROOT:$REPO_ROOT/environment/runtime:$REPO_ROOT/packages/playground/src:$REPO_ROOT/application/playground"
```

- **survey**: agent `persona-json-survey`, model `anthropic/claude-opus-4-8`;
  额外 `export MATRIX_SURVEY_TASK_PATH=$REPO_ROOT/application/validation/tasks/<task>`
- **web**: agent `persona-openhands-sdk`, model `openai/claude-opus-4.8`, kwargs `max_iterations: 20`;
  额外 `export OPENAI_API_KEY=$T OPENAI_BASE_URL=... LLM_API_KEY=$T LLM_BASE_URL=...`
- **osapp-linux**: agent `persona-computer-1`, model `openai/claude-opus-4.8`, kwargs `api_base: https://api.githubcopilot.com`;
  额外 `export OPENAI_API_KEY=$T OPENAI_BASE_URL=...`
- **chat**: agent `persona-claude-code`, model `claude-opus-4.8`;
  额外 `unset ANTHROPIC_API_KEY; export ANTHROPIC_AUTH_TOKEN=$T ANTHROPIC_BASE_URL=https://api.githubcopilot.com`
  （关键：chat 必须用 AUTH_TOKEN→Bearer，不能用 API_KEY→x-api-key）

跑：`uv run harbor run -c <recipe.yaml>`（先 `rm -rf jobs/<job_name>`）

## judge
```bash
python3 application/validation/scripts/judge_adherence.py jobs/<job> \
  --attribute <attr> --value "<X or Y value>"
```

## 找某 attribute 的正/反 persona
```bash
python3 -c "import json;m=json.load(open('persona/datasets/validation-subset/manifest.json'))
for pol in ['positive','negative']:
  print(pol,[p['persona_id'] for p in m['personas'] for h in p['attribute_hits'] if h['attribute']=='<attr>' and h['polarity']==pol])"
```

## 完成标准
四个 env 各跑通 1 正 1 反、judge 正反分开，把 instruction 打磨到位。产出：改好的
四个 task 的 instruction.md（必要时 questionnaire/context），以及一句话结论：每个 env
正/反 judge 结果。
