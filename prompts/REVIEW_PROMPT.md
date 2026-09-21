# Implementation review prompt

Review the actual DataMind implementation against PRD.md, ARCHITECTURE.md, docs/ML_SPEC.md, docs/DATA_CONTRACTS.md and docs/TEST_PLAN.md. Start read-only and run relevant non-destructive checks. Do not accept progress files as proof without inspecting code and evidence.

Inspect: real training rather than mocked output; target exclusion; fold-local preprocessing; holdout isolation and exposure; metric formulas/directions; baseline; reproducible split manifests; comparable cohorts; saved inference/schema validation; persistence after restart; duplicate submissions; failure recovery; file/DB integrity; upload limits; export correctness; clustering score validity; playground separation.

Return a table: Requirement/Test ID | Pass/Fail/Not implemented/Not verified | Evidence | Severity | Concrete fix. Prioritize correctness and user-visible defects. Cite actual local files and observed test output. Do not make changes during this review unless I separately request fixes. Provide one paste-ready implementation prompt covering the highest-priority observed defects.
