# Contracts

## Table of Contents

- Data Collection Policy
- Usage
- Notes

## Data Collection Policy

This repo is the source of truth for cross-boundary data collection defaults.

- See `policies/data_collection_policy_v1.json` for the canonical policy (timezone, L2 session window, calendar, symbol normalization policy, recommended lookbacks).
- ML exports should stamp effective values into `export_manifest.data_collection` for reproducibility.
- Optional: compare a manifest to the policy and print non-fatal warnings:

### Manifest v2 quick reference

- Required identity fields: `dataset_version`, `data_hash`, `feature_hash`, `train_window.{from_utc,to_utc}`.
- Required diagnostics:
	- Aggregate KPIs (`metrics`) with `sharpe_sim`, `max_drawdown_sim`, `f1_macro`, `minority_recall`.
	- `latency_metrics` (`p50_ms`, `p95_ms`, `p99_ms`, `max_ms`).
	- `stability` (`variance`, `max_regime_delta`, optional `rolling_sharpe_std`, `notes`).
	- `regime_metrics[]` per regime plus sample sizes.
	- `calibration.metrics` with `ece` and `brier` whenever `calibration.method != "none"`.
- See `fixtures/model_manifest_valid.json` for a canonical instance and `rules/promotion.rule.json` for the promotion thresholds.

## Usage

- Validate only: `tools/validate.py <manifest.json> schema=schemas/manifest.schema.json`
- Validate + compare to policy: `tools/validate.py <manifest.json> contracts/fixtures/policy_v1.json schema=schemas/manifest.schema.json`

### Bars Manifests (Trading)

- Append-only downloads log: `bars_download_manifest.jsonl` (schema: `schemas/bars_download_manifest.schema.json`; sample: `contracts/fixtures/bars_download_manifest.sample.jsonl`)
- Coverage index: `bars_coverage_manifest.json` (schema: `schemas/bars_coverage_manifest.schema.json`; sample: `contracts/fixtures/bars_coverage_manifest.sample.json`)

Usage guidance:
- Prefer the coverage manifest for planning/resume and gap detection vs policy windows.
- Use the append-only manifest for lineage, validation, and reconciliation.

### Promotion rule summary

Promotion gating relies on `rules/promotion.rule.json`. The rule expects the manifest fields above and enforces sharpe/drawdown, F1 macro, minority recall, latency (p95 + max), and stability variance/max-regime-delta thresholds. Trading should evaluate manifests against this rule before promoting model artifacts.

## Notes

- The manifest schema change is backward-compatible; manifests without `export_manifest.data_collection` still validate.
