# ml-contracts

Canonical contracts repository for schemas, policy, and fixtures shared by ML (TF_1) and Trading.

## Table of Contents

- Overview
  - Versioning & Governance
  - Contents
  - Fixtures
  - Consumption (Downstream expectations)
- Data Collection Policy
- Model Input Sequence Definitions
- Validation Quickstart
- Integration with TF_1 and Trading
  - Trading downloads manifests (proposed usage)
- North-Star: Repo Roles & Guardrails

---

## Versioning & Governance

- Schema Versioning:
  - The `schema_version` starts at "v1". Any breaking change to required fields (add/remove/modify) requires incrementing the `schema_version` (e.g., to "v2") and tagging a release (e.g., `v2.0.0`).
  - Consumers (TF_1, Trading) must bump their submodule and update validators to match the new schema version whenever `schema_version` changes.
  - All breaking changes must be accompanied by a release tag (e.g., `v2.0.0`).
- Change Review:
  - All changes require review by @JSunRae (see CODEOWNERS).

## Contents

- `schemas/manifest.schema.json` — model export manifest (v1)
- `schemas/bars_download_manifest.schema.json` — per-line record schema for Trading's append-only bars downloads log (JSONL)
- `schemas/bars_coverage_manifest.schema.json` — schema for Trading's compact coverage index (JSON)
- `rules/promotion.rule.json` — JSON-Logic promotion thresholds
- `fixtures/l2_fixture.csv` / `.parquet` — tiny canonical L2/curated sample
- `tools/validate.py` — helper for CI/tests
- `contracts/policies/data_collection_policy_v1.json` — canonical defaults for data collection
 - `contracts/fixtures/*.sample.*` — example instances for the schemas above

## Fixtures

- CSV and Parquet formats are provided in `fixtures/`.
- Regenerate Parquet via `fixtures/make_parquet.py`.

## Consumption

Downstream repos should:
- Track schema changes via tags and `schema_version`.
- Update submodules and validation logic when schema changes.
- Use the data collection policy defaults and stamp effective values into `export_manifest.data_collection` on model export for reproducibility.

## Data Collection Policy

This repo is the source of truth for cross-boundary data collection defaults. See `contracts/policies/data_collection_policy_v1.json`.

Downstream repos (ML/Trading) should:
- Use this policy for defaults (timezone, L2 session window, calendar, symbol normalization policy, recommended lookbacks).
- Stamp effective values into `export_manifest.data_collection` on model export for reproducibility.
- Optionally compare a manifest to policy: the validator prints non-fatal warnings if a manifest diverges.

Notes and clarifications:
- `calendar_id`: Using "XNYS" (canonical NYSE calendar). Can change via PR.
- `provider` default is intentionally omitted in policy; downstream can specify `export_manifest.data_collection.provider`.
- Symbol normalization examples include `BRK.B→BRK-B` and `BF.B→BF-B`. More examples can be added as examples (no mapping tables here).

Verification notes
- Old manifest sample: PASS (`contracts/fixtures/export_manifest_old.json`)
- New manifest with data_collection: PASS (`contracts/fixtures/export_manifest_with_policy.json`)
- Policy mismatch produces warnings (e.g., changing `l2_window` to `09:30-12:00` emits a WARNING without failing)

## Model Input Sequence Definitions

Standardizing expected input sequence lengths across model types (for TF_1 docs and manifest `input_signature` content):

- Seconds models: Input sequence = 30 minutes of seconds data
- Hour models: Input sequence = 1750 hour bars (≈ 1 year of open hours for most stocks)
- Ticks models: Input sequence = 1000 ticks
- Minutes models: Input sequence = 380 minutes (last 24 hours of open trading hours)

Manifests can encode this inside `input_signature` without changing the schema, for example:

```json
{
  "input_signature": {
    "granularity": "minute",
    "sequence_length": 380,
    "channels": ["price", "volume"],
    "dtype": "float32"
  }
}
```

## Validation Quickstart

Validate a manifest against the schema and optionally compare to policy:

```bash
python3 tools/validate.py contracts/fixtures/export_manifest_with_policy.json schema=schemas/manifest.schema.json

python3 tools/validate.py contracts/fixtures/export_manifest_with_policy.json contracts/fixtures/policy_v1.json \
  schema=schemas/manifest.schema.json
```

Tests live under `contracts/tests/`. To run all tests:

```bash
python3 -m pytest -q
```

## Integration with TF_1 and Trading

- TF_1 produces model artifacts and an export manifest conforming to `schemas/manifest.schema.json`.
- Trading consumes the manifest, enforces promotion rules, and orchestrates execution.

### Trading bars manifests (append-only + coverage)

Trading maintains two ML-consumable artifacts for bars data discovery and planning. They live under your data root (get_config().data_paths.base_path) with stable filenames:

- Append-only audit log: `bars_download_manifest.jsonl`
  - One JSON object per line; never deduped/overwritten
  - Key fields: `schema_version="bars_manifest.v1"`, `written_at`, `vendor`, `file_format`, `symbol`, `bar_size`, `path`, `filename`, `rows`, `columns`, `time_start`, `time_end`
  - Schema: `schemas/bars_download_manifest.schema.json`
  - Sample: `contracts/fixtures/bars_download_manifest.sample.jsonl`
  - Typical uses: ingestion discovery, validation (non-zero rows/expected columns), and lineage

- Coverage index: `bars_coverage_manifest.json`
  - Single JSON object with `entries[]` per (symbol, bar_size) and `days[]` best-per-day records
  - Key fields: `schema_version="bars_coverage.v1"`, `generated_at`, `entries[].{symbol,bar_size,total:{date_start,date_end},days[]}`
  - Schema: `schemas/bars_coverage_manifest.schema.json`
  - Sample: `contracts/fixtures/bars_coverage_manifest.sample.json`
  - Typical uses: planning/resume (gap analysis vs policy windows), incremental export, UI summaries

Notes
- Timestamps are ISO strings and may be naive; treat as wall-clock ET unless your pipeline normalizes TZ.
- Keep bar sizes separate for planning and partitioning.
- Partial days are expected; coverage `time_start/time_end` reflect actual file coverage.
- These schemas are new and do not change the TF_1 export manifest; no `schema_version` bump is required for `schemas/manifest.schema.json`.

## North-Star: Repo Roles & Guardrails

This ecosystem is designed around clear separation of concerns with a single shared source of truth for contracts.

Repositories & Roles

- ml-contracts
  - Scope: Canonical schemas, promotion rules, and L2 fixtures.
  - Governance: Versioned, tagged, CODEOWNERS enforced.
  - Responsibility: Defines what “valid” looks like. No model code, no trading logic.

- TF_1 (Machine Learning)
  - Scope: Data preparation, deep learning models (CNN/LSTM/Transformers), evaluation, export.
  - Responsibility: Train → evaluate → export → promote ML models.
  - Boundary: Consumes `contracts/` as a submodule. Produces manifests + models.
  - Explicit Non-Goals: No execution, no broker logic, no order routing.

- Trading Platform
  - Scope: Market data ingestion, backfill, execution orchestration, observability.
  - Responsibility: Use validated contracts + manifests from TF_1.
  - Boundary: No ML training or experiment management.

Flow of Responsibility
- Contracts: Define schemas + promotion thresholds (ml-contracts).
- Modeling: Train, evaluate, and export models (TF_1) → validated against contracts.
- Execution: Consume model manifests + signals (Trading) → enforce risk, P&L, compliance.

Guardrails
- Contracts-first: All schema/rule/fixture evolution starts in ml-contracts.
- Cross-repo smoke CI: Each repo validates artifacts against contracts.
- Branch protection: Only reviewed, green builds hit main.

—

For Copilot usage guidelines in this repository, see `.github/copilot-instructions.md`.