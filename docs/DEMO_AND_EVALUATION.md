# Academic positioning, demo and evaluation

## Project statement

DataMind integrates data discovery, reproducible ML experimentation and interactive algorithm learning in a local browser application. It helps users understand the effect of preprocessing and model choices while preserving experimental evidence.

This is an applied ML/software engineering project using established algorithms. Its contribution is the integrated workflow, understandable interactions and traceable experiments. Do not claim that it invents a new learning algorithm or is the first tool of its kind without a separate literature review.

## Objectives suitable for a report

1. Develop a guided interface for tabular data profiling and exploration.
2. Implement reproducible classification/regression pipelines with leakage-aware validation.
3. Compare algorithms using task-appropriate metrics and baseline evidence.
4. Persist configurations, datasets, models and results for repeatable experiments.
5. Support validated inference, explanations and downloadable experiment reports.
6. Provide interactive visualizations for understanding decision boundaries and clustering.

## Demonstration script — approximately 10 minutes

| Time | Action | Point to explain |
|---|---|---|
| 0:00–1:00 | Open project and load offline Iris | Dataset discovery and reproducible source |
| 1:00–2:00 | Show schema/quality, choose target, prepare split | Inputs versus output; preserved evaluation data |
| 2:00–3:00 | Explore development charts | Understand distributions and class balance |
| 3:00–5:00 | Train baseline and three classifiers | Consistent folds, real scores, bounded parameters |
| 5:00–6:00 | Show CV selection and finalize | Selection evidence differs from final held-out evaluation |
| 6:00–7:00 | Enter a new row; reopen saved experiment | Inference uses fitted pipeline and persisted history |
| 7:00–8:00 | Show report and permutation diagnostic | Results remain traceable; importance is not causation |
| 8:00–9:00 | Load synthetic blobs and vary k | Unsupervised groups use different metrics |
| 9:00–10:00 | Change playground tree depth | Interactive learning and visible model behavior |

Keep synthetic regression ready as an additional task demo. If training is slow during the presentation, open a genuinely saved prior run and clearly say it is a previous run; never pretend a cached report is live training.

## Demo dataset definitions

- **Iris:** scikit-learn's bundled loader; retain its source metadata. Explicitly rename the four columns to `sepal_length`, `sepal_width`, `petal_length`, `petal_width` (measurements in cm), and map target integers to species names under `species`. This matches examples/classification_config.json.
- **Synthetic regression:** make_regression with n_samples=500, n_features=6, n_informative=4, noise=10, random_state=42; columns `feature_1`…`feature_6`, target `target`.
- **Synthetic clustering:** make_blobs with n_samples=600, centers=3, n_features=4, cluster_std=1.0, random_state=42; columns `feature_1` through `feature_4`. Do not include generator labels as clustering features; labels can remain outside the modeled table for demo authoring, with no accuracy claim.
- **Mixed-data test/demo:** deterministic numeric and categorical synthetic table with inserted missing values. Label it synthetic; document generation parameters.

## Evaluation questions

| Question | Experiment / evidence |
|---|---|
| Does model choice matter? | Compare baseline and three models using one fixed CV manifest |
| Does preprocessing matter? | Compare scaled and passthrough kNN under identical folds |
| Does complexity affect fit? | Vary tree depth on seeded toy data and inspect validation behavior |
| Are experiments reproducible? | Repeat config with same environment/seed and compare fold membership/scores |
| Does persistence work? | Restart and reproduce predictions with the stored artifact |
| Is the tool usable? | If volunteers are available, observe task completion and record actual feedback |

Do not invent user-study participants or claim improvements without measured evidence. Cross-validation comparisons in this project are exploratory, not a formal proof that one algorithm is universally superior.

## Results table to populate after implementation

| Dataset/version | Task | Model | CV primary mean ± fold SD | Baseline | Holdout metric if finalized | Time | Environment |
|---|---|---|---|---|---|---|---|
| Iris / raw SHA-256 `e404da8a…` | Classification | Logistic regression | 0.957971 ± 0.026772 macro F1 | 0.166667 macro F1 | 0.933333 macro F1 | 3.3684 s for baseline + three selected models | Windows 11, Python 3.12.10, scikit-learn 1.9.1, AMD64 12 logical CPUs |

Measured by `scripts/final_verification.py` on 24 September 2026 with seed 42. The reported peak memory is Python allocation observed by `tracemalloc` (0.8411 MiB), not whole-process resident memory.

## Suggested final report chapters

Introduction and problem statement; existing tools/literature; objectives and scope; architecture/database; data preparation; methodology and evaluation; module implementation; test evidence and results; limitations and future work; references. Use Mermaid architecture/ER diagrams from this pack as source diagrams.

## Viva-ready explanations

- **Why Streamlit?** It provides a practical Python-first way to build an interactive academic ML interface.
- **Why SQLite?** It keeps experiment history durable without requiring a separate database server for one local user.
- **Why not only accuracy?** Class imbalance can hide poor minority-class behavior; classification and regression need different metrics.
- **Why a pipeline?** The saved preprocessing and estimator work together consistently during training and prediction.
- **Why CV and a holdout?** CV supports model selection on development data; holdout supplies a separate final assessment when it has remained unexposed.
- **Does DataMind create its own ML algorithm?** No. It integrates established algorithms into an explainable experiment workflow.
- **Where is discovery?** Dataset exploration, algorithm cards and interactive parameter/decision-boundary experiments.

## Known limitations to disclose

Local single user, bounded tabular data, synchronous training, limited algorithms, no forecasting/grouped validation, no causal explanation and no guarantee of generalization to new domains. An exposed holdout should not be described as an untouched test in later iterations.
