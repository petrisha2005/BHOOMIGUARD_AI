# BhoomiGuard AI — ML/data foundation

This module provides the prototype data foundation for BhoomiGuard AI, a future decision-support system for identifying land-acquisition delay risk. It intentionally contains no trained model, API, frontend, database, or LLM integration.

## Data limitation

**The prototype uses synthetic/anonymized data because authorized government case-level data may not be publicly available. The schema is designed to accept authorized government data during deployment.**

Each record is a non-identifying project/case snapshot. The generator models plausible, noisy relationships: legal and ownership complexity, slow documentation/compensation, approvals, and prior delay tend to increase delay risk; progress in rehabilitation and resettlement tends to reduce it. These relationships are only for prototype development and must not be interpreted as evidence about real projects.

## Dataset and data dictionary

The generator writes `data/raw/land_acquisition_cases.csv` (5,000 rows by default). It has these fields:

| Group | Fields |
| --- | --- |
| Project | `project_id`, `project_type`, `state`, `district`, `land_area_acres`, `affected_families`, `villages_affected` |
| Legal / ownership | `legal_disputes`, `ownership_conflicts`, `pending_court_cases` |
| Documentation | `documentation_completion_pct`, `missing_documents` |
| Compensation | `compensation_completion_pct`, `compensation_pending_cases`, `average_compensation_delay_days` |
| Rehabilitation & resettlement | `rehabilitation_completion_pct`, `resettlement_completion_pct`, `affected_families_rehabilitated` |
| Approvals / coordination | `pending_approvals`, `approval_delay_days`, `stakeholder_response_delay_days` |
| Progress | `current_stage`, `days_in_current_stage`, `possession_completion_pct` |
| Historical / temporal | `historical_delay_rate`, `days_remaining_to_target`, `previous_stage_delay_days` |
| Targets | `delay_flag` (0/1), `actual_delay_days` (non-negative integer) |

Stages are: Notification, Survey, Objections, Award, Compensation, Rehabilitation & Resettlement, and Possession.

## Leakage prevention

`src/config.py` is the single source of truth for feature and target columns. `FEATURE_COLUMNS` includes only information available at the snapshot time. `delay_flag` and `actual_delay_days` are explicitly excluded; `project_id` is excluded too. Any future derived risk category is analysis-only and must never be included as an input feature.

`src/preprocessing.py` exposes `get_feature_frame`, `get_targets`, and `build_preprocessor`. The latter is a scikit-learn `ColumnTransformer` with median/mode imputation, numerical scaling, and one-hot encoding. The same fitted transformer can later be reused by training and inference.

## Commands

From the repository root:

```bash
python ml/src/data_generator.py --rows 5000
python -m pytest ml/tests
```

The generator prints validation results for missing data, duplicate IDs, percentage and non-negative ranges, categories, impossible combinations, target balance, and suspiciously near-perfect target correlations.

## Next

## Step 2 — Delay Prediction Engine

`src/train.py` performs a reproducible 80/20 stratified train/test split for the `delay_flag` target. It prints all 29 available columns, the 26 permitted model inputs, and the three excluded fields (`project_id`, `delay_flag`, and `actual_delay_days`) before training. This makes the leakage boundary explicit.

The held-out test set compares Logistic Regression, Random Forest, and XGBoost classifiers. The current reproducible run (seed 42) produced:

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
| --- | ---: | ---: | ---: | ---: | ---: |
| Logistic Regression | 0.7320 | 0.7098 | 0.7249 | 0.7173 | 0.8093 |
| Random Forest | 0.7170 | 0.6987 | 0.6972 | 0.6980 | 0.8008 |
| XGBoost | 0.7130 | 0.7022 | 0.6738 | 0.6877 | 0.7933 |

Logistic Regression was selected because it has the highest recall, F1, and ROC-AUC on this held-out set. Selection uses a documented score weighted toward recall (40% recall, 30% F1, 30% ROC-AUC). Recall matters because a missed delayed project can be more harmful than an additional warning; precision remains visible to show the trade-off. These metrics are measured on synthetic prototype data and **do not establish real-world government deployment accuracy**.

The complete selected pipeline, including preprocessing, is saved as `models/delay_classifier.joblib`; metadata, including metrics and the synthetic-data disclaimer, is saved as `models/model_metadata.json`.

`src/predict.py` exposes `predict_case(record)`. It loads the saved complete pipeline and returns delay/no-delay probabilities, a predicted class, and a decision-support risk score. `risk_score = delay_probability × 100`; categories are Low (0–24), Moderate (25–49), High (50–74), and Critical (75–100). This score is not a claim of probability calibration.

`actual_delay_days` remains excluded from classification. `DelayDurationRegressor` is an explicit placeholder; Step 2A will implement and evaluate a duration-regression model rather than assigning arbitrary durations.

Run training and tests with:

```bash
python3 ml/src/train.py
python3 -m pytest ml/tests -q
```

The next step can add duration regression, explainability, and serving only when explicitly requested.

## Step 3 — Explainable AI

`src/explain.py` uses SHAP `LinearExplainer` with the saved Logistic Regression classifier and the exact fitted `preprocessor` stored in `models/delay_classifier.joblib`. No second preprocessing path or LLM determines the contributors. The resulting 75 transformed inputs include numerical features and one-hot categorical indicators.

Officers need an explanation alongside a risk score to understand which model inputs most influenced that specific prediction. `explain_prediction(record, top_k=5)` returns the same delay probability and risk classification as `predict_case`, plus the top model contributions. Positive SHAP values are reported as **features increasing predicted risk**; negative values as **features reducing predicted risk**. SHAP values and base value are on the Logistic Regression log-odds scale.

One-hot categories are kept as separate transformed contributions (for example, `State = Karnataka`), not summed into a single categorical contribution. Each factor also includes the original raw field value and its encoded 0/1 value where relevant. This avoids incorrectly merging distinct category-indicator effects, at the expense of occasionally showing the contribution of an inactive category.

`get_global_feature_importance()` ranks mean absolute SHAP values over a deterministic representative sample (up to 1,000 supplied prototype rows; 200 background rows). It describes general model behavior across that data; it is not a causal ranking of real-world causes. Development plots can be saved with `save_global_importance_plot()` and `save_individual_explanation_plot(record)` under `reports/`.

**SHAP explains how input features contributed to an individual model prediction. It should not be interpreted as proof that a feature caused the real-world delay.** These explanations are further limited by the synthetic dataset and require validation against authorized deployment data. A future LLM may phrase the structured explanation, but must not select or invent risk contributors.
