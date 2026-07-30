# matraix-persona-dev-sample source

Dev persona pool for docs, smoke tests, Harbor tasks, and Playground UI.

| Field | Value |
|-------|-------|
| Count | 200 (`persona_0001` … `persona_0200`) |
| Schema | v2 YAML (`persona_id`, `version`, `source`, `dimensions`) |
| Persona version | `1.0` |
| Smoke | `persona_0042.yaml` |
| Dimensions | **1290** — full `persona/schema/dimensions.json` catalog |
| Origin | Sampled from [`MatrAIx_Persona_1M_Public_Release`](https://huggingface.co/datasets/MatrAIx2026/MatrAIx_Persona_1M_Public_Release) |
| Sources | Even mix across `wiki`, `stackoverflow`, `amazon`, `gss`, `real_human_survey`, `prism`, `synthetic` |
| UI filters | Full 3-layer 1290 taxonomy (same as production 1M) |

Rebuild from the local 1M release + indexes:

```bash
PYTHONPATH=.:application/playground:src:environment/runtime:packages/playground/src \
  uv run python persona/scripts/rebuild_bench_dev_from_1m.py --count 200 --seed 42
```
