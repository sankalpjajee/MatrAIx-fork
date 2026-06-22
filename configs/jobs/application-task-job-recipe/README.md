# Application task job recipes

Harbor job YAML **recipes** for running **application tasks** across many personas.

Built by [`application/scripts/generate_application_job.py`](../../application/scripts/generate_application_job.py) — output lands here (append; same basename overwrites).

## Generate

```bash
# Default: random sample, sample-size 1
uv run python application/scripts/generate_application_job.py \
  --task application/tasks/example-survey_product-feedback

# Stratify when you need balanced representation
uv run python application/scripts/generate_application_job.py \
  --task application/tasks/example-survey_product-feedback \
  --stratify dimensions.age_bracket

# Multi-field stratify (composite buckets)
uv run python application/scripts/generate_application_job.py \
  --task application/tasks/example-survey_product-feedback \
  --sample-size 20 \
  --stratify dimensions.age_bracket,dimensions.economic_motivation
```

Then:

```bash
uv run harbor run -c configs/jobs/application-task-job-recipe/<name>.yaml
```

## vs other job folders

| Folder | Purpose |
|--------|---------|
| [`../example-job-recipe/`](../example-job-recipe/) | Hand-written smoke (1 persona) |
| [`../persona-task-grounding-job-recipe/`](../persona-task-grounding-job-recipe/) | Persona bench grounding (`--stratify`; first field = probe) |

Application recipes do **not** set `MATRAIX_PROBE_*` verifier env vars.

## Reporting

Batch aggregation: [`application/reporting/`](../../application/reporting/) (placeholder).
