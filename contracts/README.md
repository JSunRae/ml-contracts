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

## Usage

- Validate only: `tools/validate.py <manifest.json> schema=schemas/manifest.schema.json`
- Validate + compare to policy: `tools/validate.py <manifest.json> contracts/fixtures/policy_v1.json schema=schemas/manifest.schema.json`

### Bars Manifests (Trading)

- Append-only downloads log: `bars_download_manifest.jsonl` (schema: `schemas/bars_download_manifest.schema.json`; sample: `contracts/fixtures/bars_download_manifest.sample.jsonl`)
- Coverage index: `bars_coverage_manifest.json` (schema: `schemas/bars_coverage_manifest.schema.json`; sample: `contracts/fixtures/bars_coverage_manifest.sample.json`)

Usage guidance:
- Prefer the coverage manifest for planning/resume and gap detection vs policy windows.
- Use the append-only manifest for lineage, validation, and reconciliation.

## Notes

- The manifest schema change is backward-compatible; manifests without `export_manifest.data_collection` still validate.
