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

## Action & Recommendation Engine

`src/recommend.py` is a deterministic rules layer between SHAP and future alerting. Prediction tells an officer the current risk; SHAP provides the model factors; `generate_recommendations(record)` converts positive SHAP risk contributors into role-owned interventions, deadlines, escalation flags, and monitoring instructions. It never uses an LLM or infers factors independently.

For example, positive SHAP contributions from `Compensation Pending Cases` and `Average Compensation Delay` produce one de-duplicated **Compensation** recommendation for the Compensation/Finance Officer. Its reason preserves the actual factor names and SHAP values, its action requests verification and escalation of unresolved cases, and its monitoring tracks pending cases and payment-approval ageing.

Priority and deadline rules are centralized in `config.py`: Critical (2 days), High (5), Medium (10), and Low (21). A recommendation becomes Critical only when overall risk is Critical and the grouped model evidence is strong; the system does not label every action Critical. Recommendations are model-guided interventions, not proof of real-world causality, and should be recalculated after material project updates.

### Prototype decision policy

Positive SHAP factors are first aggregated by action category. A category becomes an intervention recommendation only when both the overall risk category and its summed positive contribution pass the conservative prototype rules in `config.py`. Weak or Low-risk contributors are retained in `monitoring_signals`, but do not create officer interventions. These are prototype decision rules, not validated government operational thresholds.

## Alert & Escalation System

`src/alerts.py` completes the deterministic chain: **Prediction → SHAP explanation → Recommendation → Alert → Escalation**. `generate_alerts(project_id, recommendation_output)` creates one `OPEN` alert for each distinct Stage 4 recommendation category. Each alert retains the recommendation's SHAP-backed reason and trigger, recommended action, responsible role, deadline, and monitoring instruction, so a future API or frontend can present the full explanation chain.

For example, a Compensation recommendation for a project with High risk produces a `COMPENSATION` alert for the Compensation/Finance Officer. It uses a stable project/category/action-derived ID, a High severity, the five-day recommendation deadline, and escalation when the recommendation requires it. Critical project risk can upgrade an eligible High recommendation to Critical. Low-priority monitoring-only signals do not create `OPEN` alerts; eligible Medium recommendations create non-escalated operational alerts. No email, SMS, persistence, acknowledgement workflow, or risk recalculation is performed in this stage.

## What-If Scenario Simulator

`src/what_if.py` lets officers simulate potential interventions before acting. `simulate_scenario(original, changes)` copies the original project input, validates one or more changed model features, reruns the existing saved `predict_case` pipeline for baseline and scenario inputs, and reports the combined projected risk impact. It does not retrain or use a separate what-if model.

For example, an officer can change `compensation_completion_pct` from 45 to 90, `documentation_completion_pct` from 60 to 95, and `pending_approvals` from 3 to 0. The response reports baseline and scenario risk scores, the percentage-point difference, category transition, exact before/after inputs, and a machine-generated projection statement. Scenario values are constrained to the original schema's numerical ranges and known categorical values, including valid state/district combinations.

This is a **model-based projection**, not a guaranteed real-world outcome. The current saved classifier does not predict delay duration, so `delay_days_change` is explicitly unavailable until the planned duration-regression model is implemented; no arbitrary delay-day estimate is created. Scenario changes outside observed synthetic-training support are rejected; changes near the outer 1% of observed support run but are explicitly marked as `edge_of_training_support`.

## Core pipeline integration

`src/pipeline.py` is a thin, service-independent orchestration layer for one project snapshot: **project input → saved-model prediction → SHAP explanation → structured recommendations → structured alerts**. `run_project_pipeline(project_input)` requires `project_id` only for stable alert identity; it is never included in model features. The prediction is created once with `predict_case`, then passed to `explain_prediction`, while the resulting explanation is passed to `generate_recommendations`; this preserves one shared source of truth instead of duplicating decision logic.

What-if simulation remains separate: `simulate_scenario(project_input, changes)` invokes the same `predict_case` contract for both baseline and scenario inputs and retains the explicit unavailable delay-duration fields. No API, persistence, or notification system is part of this integration layer.

## Model Calibration & Reliability

Phase 2 evaluates probability reliability on the existing deterministic 80/20 stratified split. The held-out partition is never used to fit a calibration mapping. Instead, five-fold stratified out-of-fold predictions from the training partition fit the candidate mapping, which is then evaluated once on the held-out partition. Metadata records ROC-AUC, Brier score, log loss, classification metrics, confusion matrix, reliability bins, probability/risk-band distributions, and upper-tail counts for raw, sigmoid (Platt), and isotonic candidates.

On the current synthetic prototype data, the raw Logistic Regression probability has Brier score **0.178911**, log loss **0.533184**, and ROC-AUC **0.809299**. Sigmoid produced Brier **0.179026** and log loss **0.534732**; isotonic produced Brier **0.178869** but log loss **0.564311**. Therefore, no calibration mapping is adopted: the small isotonic Brier difference is not material and its log-loss deterioration indicates instability, while sigmoid worsens both reliability metrics. The public prediction path continues to use the saved base pipeline probability, and SHAP continues to explain that exact pipeline; SHAP values are never rescaled.

The saved `model_metadata.json` documents this result, the evaluation strategy, random seed, base model type, feature count, target, and the absence of a calibration artifact. A calibrated probability, if selected in a future run, means the model's estimated probability under the prototype training/evaluation distribution—not a real-world government delay chance. The data remains synthetic, so neither these metrics nor the prototype Low/Moderate/High/Critical bands are government-validated or operationally approved thresholds. Threshold redesign requires a separate stakeholder and authorized-data exercise.

Phase 1 support protections remain in place: What-If rejects values outside observed synthetic-training support and marks near-boundary inputs as edge-of-support. Calibration diagnostics assess valid held-out inputs only; they do not authorize extrapolation or guarantee that extreme inputs are reliable.

## Officer-Facing Explainability

The fitted preprocessing pipeline expands categorical inputs such as district and project stage into one-hot transformed columns. SHAP correctly attributes the saved Logistic Regression prediction to those transformed columns. `explain_prediction()` now preserves every one of those direct contributions in `audit_factors`, including inactive one-hot indicators, with the transformed feature name, transformed value, source feature, and SHAP value.

For officer presentation, `officer_facing_factors` deterministically groups the audit evidence by its original source feature. A numerical feature has one direct contribution. For a categorical input, all fitted one-hot SHAP values belonging to that source feature are summed, while the project input identifies the active category shown to the officer (for example, `District` with active category `Chennai`). Risk-increasing and risk-reducing contributors are separated and ranked by absolute aggregated SHAP magnitude. This makes the view less cluttered without changing the underlying model, probability, SHAP mathematics, or individual audit evidence.

The existing transformed `top_factors` contract remains available for the recommendation engine and traceability. SHAP values describe how factors contributed to this prototype model prediction; they do not establish that a factor caused a real-world delay. Recommendations and alerts remain deterministic Phase 1 layers grounded in the same retained SHAP evidence.
