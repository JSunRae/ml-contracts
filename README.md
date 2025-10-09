# ml-contracts

Canonical contracts repository for schemas, policy, and fixtures shared by ML (TF_1) and Trading.

## Table of Contents

- Overview
  - Schemas
  - Fixtures
  - Promotion governance at a glance
  - Downstream consumption
- Getting Started
  - Environment setup
  - Run DocSync
  - Validate manifests & policies
  - Regenerate fixtures
- Contributing
  - Workflow checklist
  - Promotion rule and schema changes
  - Downstream coordination
- Data Collection Policy
- Model Input Sequence Definitions
- Validation Quickstart
- Integration with TF_1 and Trading
  - Trading downloads manifests (proposed usage)
- North-Star: Repo Roles & Guardrails

---

## Overview

The contracts repo hosts the canonical JSON Schemas, JSON-Logic promotion rules, and curated fixtures that TF_1 and Trading rely on to keep export/promotion pipelines aligned. Everything in this repo is versioned, reviewed, and consumed downstream via git submodules.

### Schemas

- `schemas/manifest.schema.json` — authoritative model export manifest (`schema_version="v2"`). Historical snapshots (`schemas/manifest.schema.v1.json`, `schemas/manifest.schema.v2.json`) remain for validation of legacy artifacts.
- `schemas/bars_download_manifest.schema.json` (`*.v1.json`) — append-only bars download manifest used to audit historical bars drops line-by-line (JSONL).
- `schemas/bars_coverage_manifest.schema.json` (`*.v1.json`) — coverage index summarizing per-symbol/bar-size availability (JSON).
- Schema checksum files live in `checksums/` and are regenerated via `python3 tools/generate_checksums.py` before cutting a release.

### Fixtures

- `fixtures/l2_fixture.csv` / `fixtures/l2_fixture.parquet` — canonical Level-2 sample; keep CSV→Parquet synchronized via `python3 fixtures/make_parquet.py`.
- `contracts/fixtures/*.json` — contract-aligned export manifests, including legacy snapshots and policy aware examples.
- `validation/*.json` — DocSync-compatible audit outputs for schemas, promotion rules, and fixtures.

### Promotion governance at a glance

- Promotion gating logic resides in `rules/promotion.rule.json` and is audited in `validation/promotion_rule_audit.json`.
- Schema changes require a `schema_version` bump inside the JSON payload and an annotated git tag (`v1.x.y` for additive, `v2.0.0` for breaking).
- Any governance change (schema, rule, fixture) must update `CHANGELOG.md` and the Verification notes table in this README.

### Downstream consumption

Downstream repos should:
- Track schema changes via tags and `schema_version`.
- Update submodules and validation logic when schema changes.
- Use the data collection policy defaults and stamp effective values into `export_manifest.data_collection` on model export for reproducibility.
- Populate the v2-only required identity fields before promotion:
  - `dataset_version` – semantic identifier for the parquet bundle TF_1 trained on.
  - `data_hash` – canonical sha256 over the curated dataset contents (see `docs/NORTH_STAR.md`).
  - `feature_hash` – sha256 of the exported feature set definition.
- Provide the expanded evaluation diagnostics (`metrics`, `latency_metrics`, `stability`, `regime_metrics`, `calibration.metrics`) so the shared promotion rule can gate on them.

## Getting Started

### Environment setup

1. Use Python 3.10+ and create an isolated virtualenv:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -U pip jsonschema pandas pyarrow docsync
   ```
2. Install any additional validator dependencies your downstream tooling requires (pytest is only needed for local test runs).

### Run DocSync

Run DocSync from the repo root to compare docs against the audited artifacts:

```bash
docsync scan --root "$(pwd)"
docsync validate --root "$(pwd)"
```

Attach any WARN/ERROR reports to PRs so reviewers can verify deltas.

### Validate manifests & policies

Use `tools/validate.py` for schema and policy checks:

```bash
python3 tools/validate.py --manifest fixtures/model_manifest_valid.json schema=schemas/manifest.schema.json
python3 tools/validate.py --manifest contracts/fixtures/export_manifest_with_policy.json --policy contracts/fixtures/policy_v1.json schema=schemas/manifest.schema.json
```

For bars manifests:

```bash
python3 tools/validate.py bars-jsonl contracts/fixtures/bars_download_manifest.sample.jsonl
python3 tools/validate.py bars-coverage contracts/fixtures/bars_coverage_manifest.sample.json
```

### Regenerate fixtures

- Refresh the parquet fixture whenever `fixtures/l2_fixture.csv` changes:
  ```bash
  python3 fixtures/make_parquet.py
  ```
- If you update schema-carrying fixtures, re-run `python3 tools/generate_checksums.py` to refresh `checksums/*.sha256` before committing.

## Contributing

### Workflow checklist

1. Update or add schemas/rules/fixtures in place—no duplication in new folders.
2. Regenerate dependent artifacts (`fixtures/make_parquet.py`, `tools/generate_checksums.py`).
3. Run DocSync (`docsync scan` + `docsync validate`) and collect WARN/ERROR output for reviewers.
4. Validate affected manifests or policies with `tools/validate.py` and execute tests via `python3 -m pytest -q` when schema logic changes.
5. Update `CHANGELOG.md` and the Verification notes table in this README when behavior shifts.

### Promotion rule and schema changes

- The `schema_version` starts at "v1". Any breaking change to required fields (add/remove/modify) requires incrementing the `schema_version` (e.g., to "v2") and tagging a release (e.g., `v2.0.0`).
- Consumers (TF_1, Trading) must bump their submodule and update validators to match the new schema version whenever `schema_version` changes.
- Use semantic version tags: `v1.x.y` for additive/non-breaking, `v2.0.0` for the next breaking release.
- Every change must be reviewed by @JSunRae (see `CODEOWNERS`). Include DocSync artifacts and validator output in the PR description.
- When promotion thresholds change, update `rules/promotion.rule.json`, refresh `validation/promotion_rule_audit.json`, and document the new predicate expectations in both `CHANGELOG.md` and the README.

### Downstream coordination

- After merging, cut a release tag and notify TF_1 and Trading so they can re-pin their submodules and rerun CI.
- Share DocSync validation bundles (scan + validate reports) and attach them to the release announcement for traceability.
- Confirm downstream promotion services have reloaded updated schemas/rules before toggling enforcement.

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
- Model manifest v2 fixture: PASS (`fixtures/model_manifest_valid.json`)
- Promotion rule evaluation covers thresholds for sharpe, F1 macro, minority recall, drawdown, latency (p95/max), and stability (variance/max_regime_delta).
- Manifest schema hash CLI: `python tools/export_manifest_hash.py [--write-artifact]` prints the canonical sha256 consumed by Trading/Win promotion gates.

### Manifest v2 contract

`schemas/manifest.schema.json` now targets `schema_version="v2"` and requires:

- Identity: `dataset_version`, `data_hash`, `feature_hash` (min length 8), `train_window` bounds.
- Model inputs: `input_signature`, `label_space`, `scaler_refs`.
- Evaluation KPIs: aggregate `metrics` block with `sharpe_sim`, `max_drawdown_sim`, `f1_macro`, `minority_recall` plus optional macro precision/recall/AUC.
- Diagnostics:
  - `latency_metrics` (`p50_ms`, `p95_ms`, `p99_ms`, `max_ms`, optional `window`).
  - `stability` (`variance`, `max_regime_delta`, optional `rolling_sharpe_std`, `notes`).
  - `regime_metrics[]` per regime with Gini KPIs and sample_size.
  - `calibration` with `method`, `evaluated_at`, and `metrics.{ece,brier}`.

Legacy v1 manifests still validate because `tools/validate.py` resolves the corresponding snapshot (`manifest.schema.v1.json`) automatically. Consumers should migrate exporters to emit all v2 blocks before the shared promotion gate flips to “fail on missing fields”.

### Promotion rule predicates

`rules/promotion.rule.json` codifies the production gate used by Trading and TF_1. The JSON-Logic rule enforces:

- Sharpe ratio floor: `metrics.sharpe_sim.value >= 1.5`.
- Drawdown cap: `metrics.max_drawdown_sim.value >= -0.15`.
- Classification quality: `metrics.f1_macro.value >= 0.40`, `metrics.minority_recall.value >= 0.45`.
- Latency guardrails: `latency_metrics.p95_ms.value <= 25`, `latency_metrics.max_ms.value <= 45`.
- Stability bounds: `stability.variance.value <= 0.05`, `stability.max_regime_delta.value <= 0.20`.

Downstream promotion checks should load the rule from this repo (or copy verbatim) so both sides fail the same manifest preconditions.

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
python3 tools/validate.py --manifest contracts/fixtures/export_manifest_with_policy.json schema=schemas/manifest.schema.json

python3 tools/validate.py --manifest contracts/fixtures/export_manifest_with_policy.json --policy contracts/fixtures/policy_v1.json \
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

### Migration & release plan

Follow this sequence when cutting over to manifest v2 + tightened promotion rules:

1. **Trading / Data Platform**
  - Publish dataset manifests (version + hash) alongside parquet drops.
  - Update promotion service to load `rules/promotion.rule.json` and require v2 manifests.
  - Add CI to run `python3 tools/validate.py <manifest> schema=schemas/manifest.schema.json` against promoted models.
2. **TF_1**
  - Emit `schema_version="v2"` manifests with the required diagnostics listed above.
  - Validate locally via `python3 tools/validate.py manifest.json` before export.
  - Ensure export bundles include the upstream dataset manifest for provenance.
3. **Contracts repo**
  - Land schema/rule/doc updates on main.
  - Run `pytest -q` and `python3 tools/validate.py` on legacy + v2 fixtures (see Verification notes).
  - Tag the release `v2.0.0` and notify #ml-platform + #trading-platform.
4. **Downstream re-pin**
  - TF_1 and Trading bump the git submodule/tag, rerun their CI, and roll out promotion rule enforcement in staging before production.

Document any future predicate tweaks in both `CHANGELOG.md` and this section.

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