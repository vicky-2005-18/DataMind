# UI and interaction specification

## Visual direction

An accessible ML lab, with a clear workspace sidebar, generous spacing, restrained blue/teal accents, readable tables and chart titles that explain what is plotted. Use Streamlit native controls and Plotly; do not make unsupported claims that the layout must look exactly like a custom React application.

Global sidebar: project, dataset, active experiment, page navigation and short workspace status. Main area: page title, one-sentence purpose, relevant action, content. Hide implementation-only paths and hashes behind an 'Experiment details' expander.

## Pages and flows

| Page | Controls and content | Empty / loading / error behavior |
|---|---|---|
| Home | Create/select project, recent actual runs, load demo CTA | Empty project explains first step; never invent activity |
| Datasets | Upload or demo picker, structure summary, quality warnings, column roles | Rejected file keeps explanatory errors; successful import shows saved ID/name |
| Explore | Confirm task/target, prepare split, chart selectors, development row previews | Before split show structural profile only; explain why modeling EDA uses development rows |
| Experiment | Dataset/target summary, feature lists, preprocessing, split, algorithm multiselect, bounded parameters, Run | Form validates before fit; training shows stage/elapsed time; failed trials remain visible |
| Results | CV score table, baseline, selected model, fold variation, finalize action | No test metrics before finalize; unavailable metrics show N/A/reason |
| Compare | Choose compatible completed runs, CV metric bars/table, config differences | State mismatch fields; no misleading cross-dataset ranking |
| Predict | Saved model picker, schema-generated form, CSV batch, prediction download | Explain missing/extra/type-mismatched columns; model missing/corrupt has recovery instruction |
| Explain & Export | Bounded permutation chart, development diagnostic note, export report/model buttons | No causal wording; explicit success/error for generated files |
| Clustering | Numeric feature selection, k, fit, cluster sizes, inertia/silhouette, elbow/PCA view | No target/accuracy fields; invalid k or undefined silhouette explains reason |
| Discover | Algorithm cards, family filter, parameter guide, playground | Playground requires explicit Run; controls update true model outputs |

Results may be a subview of the Experiment page, not necessarily a separate navigation item.

## Interaction rules

- Form labels include units and examples: 'Test fraction', 'Random seed', 'Maximum tree depth'. Explain `max_depth` in plain language.
- Dataset/task changes invalidate dependent draft target, roles and split. Do not silently reuse an old model or chart after changing dataset.
- Use consistent metric formatting: F1/accuracy 3 decimals or clearly labeled percentages; errors with target units; R² unbounded below; duration seconds.
- Chart titles include data scope: 'Development rows', 'Holdout — finalized', or 'Synthetic playground'. Sampled plots show the sample count/seed.
- Legends and tables supplement color. Confusion matrix axes are explicitly labeled. Numeric correlation is association, not causation.
- The Run button exists only for implemented behavior. Disable during submission; DB idempotency still guards duplicates.
- Navigating away must not lose completed results; reopening uses stored IDs. Drafts may reset on browser session loss and should be labeled unsaved.
- Show model-selection reason, including when the baseline wins. Never label a model 'best overall' across unrelated datasets.
- Report generation reads saved state. Changing an unsaved dropdown must not change exported experiment facts.

## Suggested chart set

Data: histogram, missingness bar, category count bar, numeric scatter, numeric correlation heatmap. Classification: CV bars with fold-variation information, confusion matrix after finalization and binary ROC when valid. Regression: holdout actual-versus-predicted and residual plot after finalization. Clustering: cluster scatter, sizes and elbow. Discovery: real decision boundary or fitted regression curve.

## Algorithm card template

Name; supported task; simple intuition; when it is useful; one limitation; scaling relevance; parameters exposed in this app; related playground action. Example: kNN predicts from nearby examples; scaling changes distances; large k smooths decisions; high dimensions can weaken distance-based intuition.

## UI verification

Use Streamlit AppTest for deterministic page/form behaviors and manual browser checks for Plotly interactions and downloads. Check laptop resolution 1366×768, keyboard label clarity, long column names, empty history, partially failed experiments and restarting with an existing workspace.
