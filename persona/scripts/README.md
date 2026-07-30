# Persona scripts

| Script | Purpose |
|--------|---------|
| [`generate_dev_personas.py`](generate_dev_personas.py) | Generate consistent offline/dev YAML from `persona/schema/dimensions.json` |
| [`generate_persona_job.py`](generate_persona_job.py) | Sample personas → Harbor grounding job YAML |

**Production sampling** uses `persona/datasets/matraix-persona-1m`. Playground /
job launch never auto-synthesize pools for thin coverage — widen filters, use
1M, or a saved cohort instead.

**Offline / experimental pools** (gitignored under `persona/datasets/_generated/`):

```bash
uv run python persona/scripts/generate_dev_personas.py
# → persona/datasets/_generated/bench-dev-2000/
```

Optional: `--task` + `--stratum-min` for Harbor grounding cell top-up;
`--strategy` expands a task `persona_strategy.json` into a local strategy pool
for experiments only (point `"pool"` at the printed path yourself).

**Grounding jobs** read confounders from the task catalog when present (filter pool → stratify on probe only). Default for catalog tasks with confounders. Use `--controlled-probe` for anchor-based cohorts; `--no-controlled-probe` disables anchor mode explicitly.
