# matraix-persona-1m

Production persona source for Playground: the published
[`MatrAIx_Persona_1M_Public_Release`](https://huggingface.co/datasets/MatrAIx2026/MatrAIx_Persona_1M_Public_Release)
coreset (1,000,000 rows).

This is **not** a synthetic `_generated` pool.

- **`release/`** — the Parquet source (download / HF cache). Shown in Dataset as `matraix-persona-1m`.
- **`indexes/`** — inverted `dim|source → value → row_id[]` postings for fast filtered / stratified
  sampling (shipped on HF next to the release).
- **`cohorts/`** — local launch cache only. Sampling writes YAML here so Harbor can run the subset.
  These dirs are **not** listed in the Dataset dropdown (that was confusing next to the 1M root).
  Use **Save as dataset…** in Playground to promote a cohort to `persona/datasets/<name>/`
  so it appears in the Dataset list across tasks.

## Setup

Either:

```bash
export MATRIX_PERSONA_1M_DIR=/path/to/MatrAIx_Persona_1M_Public_Release
```

where that directory contains `data/persona-1m-*.parquet` and `persona_codes.schema.json`,
or download the HF dataset into the local Hugging Face cache (Playground will discover it).

Optional offline mirror:

```bash
huggingface-cli download MatrAIx2026/MatrAIx_Persona_1M_Public_Release \
  --repo-type dataset \
  --local-dir persona/datasets/matraix-persona-1m/release
```

### Sampling indexes (HF)

The public release includes ``indexes/`` (``manifest.json`` + ``postings.sqlite``, ~2.5GB):

https://huggingface.co/datasets/MatrAIx2026/MatrAIx_Persona_1M_Public_Release/tree/main/indexes

Downloading the dataset with ``hf download … --local-dir …/release`` pulls indexes if you
also fetch that folder, or copy ``indexes/`` next to ``release/`` / under
``persona/datasets/matraix-persona-1m/indexes``.

Rebuild locally only if you change the Parquet shards:

```bash
PYTHONPATH=.:application/playground:src:environment/runtime:packages/playground/src \
  .venv/bin/python -m backend.service.build_persona_1m_indexes
```

To add/refresh only the ``source`` postings on an existing index (no full rebuild):

```bash
PYTHONPATH=.:application/playground:src:environment/runtime:packages/playground/src \
  .venv/bin/python -m backend.service.build_persona_1m_indexes --enrich-source
```

Playground sampling uses the index automatically when present; otherwise falls back to Parquet scan.

## Usage in Playground

1. Dataset → `matraix-persona-1m`
2. Turn off task default persona strategy if needed
3. Random / Stratified → sample up to 10,000
4. Optional: **Save as dataset…** → appears under Dataset for reuse across tasks
5. Launch against the materialized cohort (or the saved dataset)

`All` is disabled on the full 1M root — sample a cohort instead.
