# Acme support chat (REST API)

MatrAIx chat task with a **mock Acme support bot** exposed as a REST API compose sidecar. The persona agent must call HTTP endpoints (`POST /v1/messages`, `GET /v1/conversation`) for a multi-turn conversation, then save the transcript to `/app/output/transcript.json`.

Requires **Docker Compose** (local `docker` environment). Not supported on cloud providers yet.

For the MCP variant, see [`../acme-support-mcp/`](../acme-support-mcp/).

## Suggested setup (non-binding)

| Field | Value |
|-------|-------|
| Agent | `persona-claude-code` |
| Environment | `docker` (default) |
| Persona | `persona/examples/persona_0042.yaml` |

```bash
uv run harbor run \
  -a persona-claude-code \
  -m anthropic/claude-sonnet-4-6 \
  --ak persona_path=persona/examples/persona_0042.yaml \
  -p tasks/chat/acme-support-api
```

Oracle check (no API key):

```bash
uv run harbor run -p tasks/chat/acme-support-api -a oracle
```

## Layout

```
environment/
├── Dockerfile
├── docker-compose.yaml      # support-api sidecar
├── order_context.md         # → /app/input/
└── support-api/
    ├── Dockerfile
    └── server.py            # Flask REST endpoints
```
