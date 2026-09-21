# DataMind implementation instructions

## Read first

START_HERE.md, PRD.md, ARCHITECTURE.md, ROADMAP.md and PROJECT_STATE.md define the build. Read docs/ML_SPEC.md, docs/DATA_CONTRACTS.md and docs/TEST_PLAN.md before implementing training or prediction. Use docs/SERVICE_CONTRACTS.md and docs/DATABASE.md for integration.

The user's current explicit directions take precedence over this planning pack. Record any resulting scope changes; do not silently maintain contradictory documents.

## Product and architecture

- Build a working local Python/Streamlit tabular ML platform, according to the current milestone.
- Keep UI, services, ML and persistence separate. Use SQLite plus generated local artifacts.
- Do not add React, a REST backend, cloud services, login, Redis, Docker requirements or an LLM chatbot to v1 without a scope change.
- No real code exists in the initial planning pack. Inspect the workspace before claiming something is implemented.

## ML correctness

- Keep target out of features. Prepare and persist exact split/fold row IDs.
- Fit preprocessing within CV training folds; fit the saved champion only on development rows.
- Compare models on identical folds. Select by CV metric; final holdout evaluation is explicit and immutable.
- Include appropriate dummy baseline and disclose when it wins.
- Use task-appropriate metrics, explicit directions and N/A with reason for undefined values.
- Record configs, seeds, environment, dataset hashes and artifacts. Prediction reuses the same fitted pipeline.
- Never hardcode model scores, pretend sample charts are real, or claim accuracy targets as achieved.

## Engineering

- Resolve/test dependency versions; commit generated lockfiles. Use pathlib for portable paths.
- Validate configurations and incoming bytes. No eval/exec on user input or arbitrary uploaded model deserialization.
- Use parameterized SQL, short transactions, foreign keys, atomic artifact publication and integrity checks.
- Keep training under the workspace lock and protect against duplicate submission.
- Save useful failures and preserve existing user work; avoid unrelated rewrites or deletion.
- Keep raw dataset rows/secrets out of logs. Bind the initial app to loopback.
- Use Streamlit forms/session state for interaction; database for durable history. Widget reruns must not retrain automatically.
- Avoid placeholders that look functional. Unimplemented pages must say so and should not appear in the final completed feature set.

## Execution workflow

1. Inspect real state and identify the next unchecked milestone task.
2. Implement a small end-to-end slice with appropriate unit/integration checks.
3. Run relevant verification. Inspect UI when the slice changes visible behavior.
4. Fix failures caused by the change before expanding scope.
5. Update TASKS.md and PROJECT_STATE.md with exact evidence, remaining defects and next step.

Do not ask for repeated confirmation for ordinary local implementation and tests already requested. Follow the development environment's actual permissions for installations, network and external actions; this file does not grant permission to publish or bypass controls.

## Milestone handover

State what works, important changed paths, commands actually run, test results, how to run/demo the change, and known limitations. If blocked, identify the concrete blocker and preserve a usable checkpoint. Never claim tests passed when they were not run.
