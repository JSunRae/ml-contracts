# ml-contracts

## Versioning & Governance

- **Schema Versioning:**
  - The `schema_version` starts at "v1". **Any breaking change to required fields (add/remove/modify) requires incrementing the `schema_version` (e.g., to "v2") and tagging a release (e.g., `v2.0.0`).**
  - Consumers (e.g., TF_1, Trading) **must bump their submodule and update validators to match the new schema version whenever `schema_version` changes.**
  - All breaking changes should be accompanied by a release tag (e.g., `v2.0.0`) in the repository.
- **Change Review:**
  - All changes require review by @JSunRae (see CODEOWNERS).

## Fixtures

- Both CSV and Parquet formats are provided in `fixtures/`.
- Parquet files can be regenerated using `fixtures/make_parquet.py`.

## Consumption

- Consumers must:
  - Track schema changes via tags and `schema_version`.
  - See CODEOWNERS for governance and change approval.
  - Update submodules and validation logic when schema changes.

## Contents
- schemas/manifest.schema.json — model export manifest (v1)
- rules/promotion.rule.json — JSON-Logic promotion thresholds
- fixtures/l2_fixture.csv / .parquet — tiny canonical L2/curated sample
- tools/validate.py — helper for CI/tests

## Data Collection Policy

This repo is the source of truth for cross-boundary data collection defaults. See:

- `contracts/policies/data_collection_policy_v1.json`

Downstream repos (ML/Trading) should:
- Use this policy for defaults (timezone, L2 session window, calendar, symbol normalization policy, recommended lookbacks).
- Stamp effective values into `export_manifest.data_collection` on model export for reproducibility.
- Optionally call `tools/validate.py <manifest.json> <policy.json>` to print non-fatal warnings if a manifest diverges from policy.

Questions (answered here pending PR discussion)
- calendar_id: Using "XNYS" (canonical NYSE calendar identifier). Happy to switch if you prefer another canonical ID.
- provider default in policy: Intentionally omitted; downstream can specify `export_manifest.data_collection.provider` if needed.
- symbol normalization examples: Included BRK.B→BRK-B and BF.B→BF-B. Propose adding RDS.B→RDS-B and HEI.A→HEI-A if helpful; we keep only examples here (no mapping tables).

Verification notes
- Old manifest sample: PASS (contracts/fixtures/export_manifest_old.json)
- New manifest with data_collection: PASS (contracts/fixtures/export_manifest_with_policy.json)
- Policy mismatch produces warnings (e.g., changing l2_window to 09:30-12:00 emits a WARNING without failing)
🌟 North-Star: Trading + ML Ecosystem Alignment

This ecosystem is designed around clear separation of concerns with a single shared source of truth for contracts.

Repositories & Roles

ml-contracts

Scope: Canonical schemas, promotion rules, and L2 fixtures.

Governance: Versioned, tagged, CODEOWNERS enforced.

Responsibility: Defines what “valid” looks like. No model code, no trading logic.

TF_1 (Machine Learning)

Scope: Data preparation, deep learning models (CNN/LSTM/Transformers), evaluation, export.

Responsibility: Train → evaluate → export → promote ML models.

Boundary: Consumes contracts/ as a submodule. Produces manifests + models.

Explicit Non-Goals: No execution, no broker logic, no order routing.

Trading Platform

Scope: Market data ingestion, backfill, execution orchestration, observability.

Responsibility: Use validated contracts + manifests from TF_1.

Boundary: No ML training or experiment management.

🔄 Flow of Responsibility

Contracts: Define schemas + promotion thresholds (ml-contracts).

Modeling: Train, evaluate, and export models (TF_1) → validated against contracts.

Execution: Consume model manifests + signals (Trading) → enforce risk, P&L, compliance.

🚧 Guardrails

Contracts-first: All schema/rule/fixture evolution starts in ml-contracts.

Pre-commit hooks: Prevent local drift (no duplicate schema/rules in TF_1 or Trading).

Cross-repo smoke CI: Each repo validates artifacts against contracts.

Branch protection: Only reviewed, green builds hit main.

🎯 North-Star

Keep each repo laser-focused:

ml-contracts = the law.

TF_1 = build the brains.

Trading = run the business.

This preserves velocity, enforces trust, and ensures Future You (and collaborators) always know where to look.