# Decisions, assumptions and implementation risks

The user supplied the title and requested an Antigravity-ready implementation pack. Dataset type, team size, deadline and mandatory faculty stack were not specified. The following are explicit proposed defaults, not claimed user requirements.

## Decision log

| Decision | Rationale | Revisit when |
|---|---|---|
| Tabular CSV focus | Allows a complete understandable experiment workflow | Faculty explicitly requires image/text modeling |
| Streamlit UI | Keeps most implementation in Python and prioritizes ML | Custom frontend/user-management becomes a real requirement |
| SQLite + artifacts | Low setup burden, clear persistence | Multiple concurrent users require stronger ownership/concurrency |
| Single-user localhost | Fits academic laptop demonstration | Hosting/sharing is explicitly requested |
| Synchronous bounded training | Simple, traceable execution | Larger tasks need cancellation/timeouts/workers |
| Classical scikit-learn models | CPU-friendly and easy to compare/explain | Deep-learning learning goals are explicitly added |
| CV selection + final holdout | Defines meaningful evaluation roles | Group/time dependence requires a different splitter |
| No LLM requirement | Core project concerns ML experimentation | Optional natural-language explanations have a justified purpose |
| No mandatory Docker | Simplifies first working Windows environment | Reproducible deployment is added after local success |
| Fixed dependency lock after verification | Reproducible working environment | A deliberate tested upgrade is needed |

## Risk register

| Risk | Observable sign | Planned response |
|---|---|---|
| Scope growth | Login/chat/cloud added before end-to-end ML works | Follow roadmap gates and keep future work deferred |
| Data leakage | Unexpectedly high scores; fit sees validation IDs | Spy-transformer tests and explicit split manifests |
| Holdout overuse | Many experiments repeatedly finalized on same split | Exposure flag, frozen evaluations, no test-score leaderboard |
| UI rerun duplication | Training begins after changing a chart control | Forms, submission token and DB uniqueness |
| Lost state | History vanishes after restart | DB authoritative; artifacts and recovery tested |
| Memory blow-up | Dense one-hot matrix exceeds local capacity | Feature/category/cell caps before allocation |
| Dependency/API mismatch | Installation/import/test errors | Resolve clean env, inspect official APIs, pin tested versions |
| Partial writes | DB points to missing model or orphan file exists | Atomic publish, checksum verification, guarded reconciliation |
| Misleading explanation | Importance presented as causal proof | Development diagnostic label and correlation limitation |
| Weak academic positioning | Only library calls shown in presentation | Demonstrate validation, reproducibility, comparison and interaction engineering |

## Change control

When requirements change, record the new decision, affected scope, revised contracts/tests and roadmap effect. Preserve completed work where possible. If the title is later intended to mean an automated literature or algorithm-search engine, revise PRD explicitly; this pack uses 'discovery' to mean data/algorithm exploration and hands-on learning.

## Possible future modules

Group/time-aware validation; controlled randomized hyperparameter search; SHAP; optional XGBoost; project authentication; FastAPI/React UI; process job runner; cloud storage; experiment tracking integration. Each requires its own validation and UI design. None is part of current acceptance.
