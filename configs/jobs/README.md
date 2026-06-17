# MatrAIx job configs

Harbor Job YAML templates for `harbor run -c configs/jobs/<file>.yaml`.

## How this differs from code paths

| Path | Contents |
|------|----------|
| **`configs/jobs/`** (this directory) | Orchestration: agents, personas, tasks, concurrency, docker/daytona |
| `src/harbor/environments/` | Python environment provider implementations |
| `tasks/*/environment/` | Per-task container definitions |

## Files

| File | Purpose |
|------|---------|
| `persona-debug-local.yaml` | Quick local run: survey + chat with `persona-claude-code` |
| `persona-survey-local.yaml` | Survey task smoke |
| `persona-chat-local.yaml` | Chat task smoke |
| `persona-web-playwright-local.yaml` | Live web via `persona-openhands-sdk` (Playwright) |
| `persona-web-browser-use-local.yaml` | Live web via `persona-browser-use` |
| `persona-web-cocoa-local.yaml` | Live web via `persona-cocoa` (AIO Sandbox image) |
| `persona-web-linux-cua-local.yaml` | Docker Linux **web** CUA (books.toscrape.com); uses `cua_submission_profile: book_interest` |
| `persona-computer-use-linux-local.yaml` | Linux desktop notifications (Docker Xvfb) via `persona-computer-1` |
| `persona-computer-use-macos-local.yaml` | macOS desktop via `persona-computer-1` + `use-computer` |
| `persona-computer-use-ios-local.yaml` | iOS Simulator via `persona-computer-1` + `use-computer` (`platform: ios`) |

Planned (Phase 3): `persona-sweep-daytona.yaml`

## Environment variables

- `ANTHROPIC_API_KEY` — Claude-family persona agents
- `LLM_API_KEY` — `persona-openhands-sdk` (Playwright web)
- `USE_COMPUTER_API_KEY` — `persona-computer-1` with `-e use-computer` (macOS / iOS)
- Docker Linux CUA (`persona-web-linux-cua-local.yaml`) needs only `ANTHROPIC_API_KEY` + `uv sync --extra computer-1`
- `DAYTONA_API_KEY` — when `environment.type: daytona`

Set these in your shell (see [`.env.example`](../../.env.example) and [choosing-an-agent.md](../../docs/environments/choosing-an-agent.md)).

## Run

```bash
uv run harbor run -c configs/jobs/persona-debug-local.yaml
```

Computer-use: `persona-computer-1` auto-routes by environment — see [tasks/computer-use/README.md](../../tasks/computer-use/README.md) and job YAMLs `persona-computer-use-macos-local`, `persona-computer-use-ios-local`, `persona-computer-use-linux-local`. Web CUA: `persona-web-linux-cua-local`.
