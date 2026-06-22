# MatrAIx application tasks

Executable Harbor tasks for **application product research** (survey, chat, web, computer-use). Owned by the Application team.

## Layout

```
application/
├── tasks/       # Flat task dirs (example-* = reference scenarios)
│   └── _docker/ # Shared Docker build scripts (copy into task environment/)
└── reporting/   # Application-team batch reports (placeholder)
```

Each task is a standard Harbor directory (`task.toml`, `instruction.md`, `environment/`, `tests/`). Docker tasks use `/app/input/` and `/app/output/`.

## Example scenarios

| Form | Path | Suggested agent |
|------|------|-----------------|
| survey | `application/tasks/example-survey_product-feedback/` | `persona-claude-code` |
| chat (API) | `application/tasks/example-chat-api_support_chatbot/` | `persona-claude-code` |
| chat (MCP) | `application/tasks/example-chat-mcp_support_chatbot/` | `persona-claude-code` |
| web (Playwright) | `application/tasks/example-web-playwright_books-interest/` | `persona-openhands-sdk` |
| web (browser-use) | `application/tasks/example-web-browser-use_books-interest/` | `persona-browser-use` |
| web (Cocoa) | `application/tasks/example-web-cocoa_books-interest/` | `persona-cocoa` |
| web (CUA) | `application/tasks/example-web-cua_books-interest/` | `persona-computer-1` |
| computer-use (macOS) | `application/tasks/example-computer-use-macos_notification-preferences/` | `persona-computer-1` |
| computer-use (iOS) | `application/tasks/example-computer-use-ios_notification-preferences/` | `persona-computer-1` |
| computer-use (Linux) | `application/tasks/example-computer-use-linux_notification-preferences/` | `persona-computer-1` |

## Job recipes

| Config path | Use |
|-------------|-----|
| `configs/jobs/example-job-recipe/` | Hand-written smoke jobs (1 persona) |
| `configs/jobs/application-task-job-recipe/` | Generated multi-persona application runs |

```bash
# Default: random sample, sample-size 1
uv run python application/scripts/generate_application_job.py \
  --task application/tasks/example-survey_product-feedback

# Explicit stratify when you need balanced buckets
uv run python application/scripts/generate_application_job.py \
  --task application/tasks/example-survey_product-feedback \
  --stratify dimensions.age_bracket

uv run harbor run -c configs/jobs/application-task-job-recipe/<name>.yaml
```

Smoke: `uv run harbor run -c configs/jobs/example-job-recipe/appSim-example-survey-local.yaml`

## Persona bench (separate track)

Persona matrix / profile validation lives under [`persona/tasks/`](../persona/tasks/). Some **example** folder names match Application for easy comparison; each team owns and extends its own tasks — no sync between trees.

## Docs

- **First run:** [`docs/applications/getting-started.md`](../docs/applications/getting-started.md)
- Authoring tasks: [`docs/applications/`](../docs/applications/README.md)

Harbor upstream examples: `examples/tasks/`
