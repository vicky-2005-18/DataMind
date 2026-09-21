# Milestone prompts for Antigravity

Paste one prompt at a time after the preceding gate works. These are chat instructions, not PowerShell commands. Each prompt authorizes its own local implementation and relevant checks, subject to the environment's actual permissions.

## M1 — Dataset workspace

Read AGENTS.md, PROJECT_STATE.md, TASKS.md, PRD.md and docs/DATA_CONTRACTS.md. Verify M0 exists and works. Implement M1: strict UTF-8/BOM CSV ingestion, immutable raw files and hashes, parser metadata, SQLite dataset records, offline Iris/synthetic regression/blobs loaders, structural profile, missingness/duplicates/type warnings and role suggestions. Follow the upload/row/column limits; do not silently truncate training data. Add meaningful T02–T07 checks and connect the Datasets page. Update state/tasks with actual results. End with a manual demo and next step.

## M2 — Correct supervised experiment engine

Read the current state plus docs/ML_SPEC.md, DATA_CONTRACTS.md, SERVICE_CONTRACTS.md and TEST_PLAN.md. Implement M2 in small vertical slices: task/target/feature validation, row policies, exact development/holdout/CV manifests, development EDA, unfitted preprocessing pipelines, baseline and initial classifier/regressor, then the remaining registry. Compare identical folds; choose by CV; refit/save the champion on development only. Keep holdout metrics unavailable until finalization. Prove T08–T19, T43 and T44 with real tests, especially spy-transformer leakage tests and independent metric oracles. Add required persistence plumbing without pretending the complete M3 UX is done. Update state/tasks, show an Iris and synthetic regression run, and state remaining work.

## M3 — Persistent MVP, finalization and prediction

Read current code/state and persistence/service/UI specifications. Implement complete trial history, safe artifact publication, workspace locking, submit idempotency, guarded crash recovery, compatible comparison, config cloning, explicit idempotent holdout finalization and holdout-exposure tracking. Prediction must validate raw features and reuse the saved fitted pipeline; support single row and bounded CSV batches. Verify T20–T31, T41 and T42, then the full MVP restart walkthrough. Save exact results in PROJECT_STATE. Fix incomplete M2 integration before adding unrelated functionality.

## M4 — Explanation and evidence export

Implement M4 according to ML_SPEC, DATA_CONTRACTS and UI_SPEC. Add bounded original-feature permutation importance as a development-set diagnostic. Generate HTML/Markdown reports and model/experiment ZIPs from stored records, including actual configuration, CV/holdout scope, failures, exposure flags, environment and artifact hashes. Exclude raw training data by default. Use escaped HTML and safe CSV text export. Verify T32–T34 and model export/reload consistency. Update state/tasks and provide a real downloaded report example.

## M5 — Clustering and interactive discovery

Complete the numeric K-Means lab with median imputation, standardization, k validation, inertia, valid silhouette, cluster sizes, elbow artifacts and PCA display projection. Persist one selected-k K-Means trial per clustering experiment; save the elbow sweep as diagnostic JSON/plot artifacts rather than duplicate algorithm trial IDs. Then add algorithm cards and seeded tree/kNN/clustering playgrounds with real fitted outputs. Keep unsupervised and synthetic demonstration metrics separate from supervised comparisons. Verify T35–T38. Update the user guide and current state with actual evidence.

## M6 — Final verification and academic demo

Read PRD acceptance criteria, TEST_PLAN and DEMO_AND_EVALUATION. Audit implemented behavior against all P0/P1 requirements. Resolve real defects; do not add future-scope features. Run the final necessary tests, validate fresh setup and offline demos, inspect laptop-sized UI and measure performance goals on recorded hardware. Verify T39–T40 and any still-open required cases. Prepare truthful demo screenshots, results and limitations. Update README/TASKS/PROJECT_STATE. Report completed, partial and missing requirements with evidence; never invent completion percentages or metrics.
