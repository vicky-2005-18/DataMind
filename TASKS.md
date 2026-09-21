# Implementation tasks

Status convention: `[ ]` not implemented, `[x]` verified complete. All implementation tasks start unchecked. Evidence belongs in PROJECT_STATE, not invented completion percentages.

## M0 — Foundation

- [x] Verify Python target and create local virtual environment.
- [x] Resolve/install dependencies; record working versions and lockfiles.
- [x] Create package skeleton, typed config and error contracts.
- [x] Implement SQLite migration runner from docs/schema.sql.
- [x] Implement project create/list and storage directory handling.
- [x] Build navigation shell and honest empty states.
- [x] Verify app launch and restart persistence.

## M1 — Dataset workspace

- [x] Add strict CSV/BOM/header/row/size validation.
- [x] Preserve original bytes, hash and parser metadata.
- [x] Add Iris and seeded synthetic regression/blobs demos.
- [x] Add structural profile, quality warnings and role suggestions.
- [x] Validate all input-limit and malformed-input cases.

## M2 — Supervised ML

- [x] Confirm task, target, feature roles and row policies.
- [x] Build exact split/fold manifests with stable source row IDs.
- [x] Add development-only EDA charts and labeled samples.
- [x] Build train-fitted preprocessing pipelines.
- [x] Add baseline, initial classifier and initial regressor.
- [x] Expand to all v1 registry algorithms and parameter bounds.
- [x] Store per-fold and aggregate metrics with correct direction.
- [x] Select champion by CV, refit on development and save pipeline.
- [x] Pass target exclusion, split, leakage and metric oracle tests.

## M3 — Persistent MVP

- [x] Add trial/experiment history and failure records.
- [x] Add workspace lock, submit idempotency and guarded recovery.
- [x] Add explicit idempotent holdout finalization/exposure flags.
- [x] Add compatible-run comparison and config cloning.
- [x] Add schema-validated single/batch prediction.
- [x] Verify same predictions after restart and trusted model reload.
- [x] Complete full MVP demonstration.

## M4 — Explain and export

- [ ] Add bounded original-column permutation diagnostic.
- [ ] Generate HTML/Markdown experiment report from saved records.
- [ ] Generate model/experiment ZIP with manifest and checksums.
- [ ] Validate exports, HTML escaping and CSV formula handling.

## M5 — Discovery and clustering

- [ ] Add numeric K-Means, elbow and cluster size summary.
- [ ] Add valid silhouette calculation and N/A reasons.
- [ ] Add PCA display projection distinct from scoring space.
- [ ] Add algorithm cards and reviewed educational text.
- [ ] Add seeded tree/kNN decision-boundary playground.
- [ ] Verify real parameter changes update actual fitted outputs.

## M6 — Completion

- [ ] Resolve required test failures and run final suite.
- [ ] Check UI at laptop resolution and inspect error paths.
- [ ] Measure performance targets with recorded hardware/versions.
- [ ] Verify fresh-environment setup and offline demos.
- [ ] Prepare demo screenshots/logs and honest results table.
- [ ] Update README, limitations and PROJECT_STATE for handover.
