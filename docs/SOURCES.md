# Official technical references

Consulted 21 September 2026. These references support selected implementation principles; the product scope, architecture and limits in this pack are original design proposals. No dependency combination was installed or tested while preparing the pack.

| Reference | Used for |
|---|---|
| [Google Antigravity — Rules](https://antigravity.google/docs/rules-workflows) | Current workspace rule locations and activation modes; starter prompt remains explicit |
| [Streamlit — Session State](https://docs.streamlit.io/develop/concepts/architecture/session-state) | Rerun behavior, session lifetime and distinction from durable persistence |
| [scikit-learn — Common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html) | Data leakage, consistent preprocessing and randomness |
| [scikit-learn — Model persistence](https://scikit-learn.org/stable/model_persistence.html) | Persistence choices, trust and environment compatibility |
| [scikit-learn — cross_validate](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.cross_validate.html) | Cross-validation interface and returned score information |
| [scikit-learn — silhouette_score](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.silhouette_score.html) | Silhouette definition and valid label-count conditions |

At implementation time, check official API pages for the selected installed versions, particularly Streamlit navigation/AppTest, OneHotEncoder dense output, missing-column handling, RMSE scoring and estimator parameter compatibility. Do not mix code copied from different library versions without checking it.
