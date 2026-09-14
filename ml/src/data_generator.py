"""Generate and validate realistic synthetic land-acquisition case snapshots."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from .config import (PROJECT_TYPES, RANDOM_SEED, RAW_DATA_PATH, STAGE_NAMES, STATE_DISTRICTS)
except ImportError:  # Allows: python ml/src/data_generator.py
    from config import PROJECT_TYPES, RANDOM_SEED, RAW_DATA_PATH, STAGE_NAMES, STATE_DISTRICTS


def _clip_int(values: np.ndarray, low: int, high: int | None = None) -> np.ndarray:
    """Round and constrain a numeric array to an integer range."""
    result = np.rint(values).astype(int)
    return np.maximum(result, low) if high is None else np.clip(result, low, high)


def generate_dataset(rows: int = 5_000, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """Return reproducible, non-identifying synthetic acquisition case snapshots."""
    if rows < 1:
        raise ValueError("rows must be at least 1")
    rng = np.random.default_rng(seed)
    stage_index = rng.choice(len(STAGE_NAMES), size=rows, p=[.09, .14, .14, .15, .19, .16, .13])
    stages = np.array(STAGE_NAMES, dtype=object)[stage_index]
    states = rng.choice(tuple(STATE_DISTRICTS), size=rows)
    districts = np.array([rng.choice(STATE_DISTRICTS[state]) for state in states], dtype=object)
    project_types = rng.choice(PROJECT_TYPES, size=rows, p=[.27, .16, .12, .18, .14, .13])

    land_area = np.round(np.clip(rng.lognormal(4.45, .8, rows), 8, 3_500), 2)
    families = _clip_int(land_area * rng.uniform(.65, 2.35, rows) + rng.normal(18, 30, rows), 3)
    villages = _clip_int(np.sqrt(land_area) / 2.4 + rng.normal(1.7, 1.2, rows), 1, 30)
    complexity = rng.normal(0, 1, rows) + .17 * np.log1p(families) + .25 * (project_types == "Industrial Corridor")
    legal_disputes = _clip_int(rng.poisson(np.clip(.55 + .42 * complexity, .1, 5)), 0, 20)
    ownership_conflicts = _clip_int(rng.poisson(np.clip(1.1 + .62 * complexity + .012 * families, .15, 16)), 0, 45)
    court_cases = _clip_int(rng.poisson(np.clip(.35 + .55 * legal_disputes + .18 * ownership_conflicts, .1, 25)), 0, 60)

    progress_base = np.clip((stage_index / (len(STAGE_NAMES) - 1)) * 100 + rng.normal(0, 16, rows), 0, 100)
    documentation = np.clip(81 - 7.5 * complexity + 2.5 * stage_index + rng.normal(0, 11, rows), 5, 100)
    missing_docs = _clip_int((100 - documentation) / 13 + .45 * ownership_conflicts + rng.normal(0, 1.5, rows), 0, 35)
    compensation = np.clip(progress_base - 6.5 * complexity - 3 * legal_disputes + rng.normal(0, 12, rows), 0, 100)
    pending_comp = _clip_int(families * (1 - compensation / 100) * rng.uniform(.55, .95, rows), 0)
    comp_delay = _clip_int((100 - compensation) * .8 + 5 * legal_disputes + rng.normal(5, 18, rows), 0, 500)
    rehabilitation = np.clip(progress_base - 9 * complexity + rng.normal(0, 13, rows), 0, 100)
    resettlement = np.clip(rehabilitation + rng.normal(-2, 8, rows), 0, 100)
    families_rehab = _clip_int(families * rehabilitation / 100 * rng.uniform(.88, 1, rows), 0)
    pending_approvals = _clip_int(rng.poisson(np.clip(1.2 + .75 * complexity + .22 * legal_disputes, .1, 12)), 0, 30)
    approval_delay = _clip_int(12 * pending_approvals + 7 * legal_disputes + rng.normal(8, 18, rows), 0, 500)
    stakeholder_delay = _clip_int(3.3 * families / np.maximum(villages, 1) + 9 * ownership_conflicts + rng.normal(5, 20, rows), 0, 500)
    days_stage = _clip_int(rng.gamma(2.2, 24, rows) + 17 * legal_disputes + 8 * pending_approvals, 1, 900)
    possession = np.clip(progress_base + 4 * stage_index - 8 * complexity + rng.normal(0, 12, rows), 0, 100)
    historical_rate = np.clip(rng.beta(2.4, 4.2, rows) + .055 * complexity, 0, 1)
    target_remaining = _clip_int(rng.normal(285 - 28 * stage_index, 115, rows), 7, 730)
    previous_delay = _clip_int(rng.gamma(1.7, 17, rows) + 9 * legal_disputes + 6 * ownership_conflicts, 0, 600)

    risk_signal = (
        -5.1 + .22 * legal_disputes + .095 * ownership_conflicts + .075 * court_cases
        + .028 * (100 - documentation) + .018 * (100 - compensation)
        + .021 * (100 - rehabilitation) + .12 * pending_approvals + .007 * approval_delay
        + .003 * stakeholder_delay + .0045 * days_stage + 1.6 * historical_rate
        + .006 * previous_delay - .004 * target_remaining + rng.normal(0, 1.05, rows)
    )
    probability = 1 / (1 + np.exp(-risk_signal))
    delay_flag = rng.binomial(1, probability)
    delay_days = _clip_int(
        delay_flag * (22 + 23 * legal_disputes + 5 * ownership_conflicts + .34 * approval_delay
                      + .20 * stakeholder_delay + .32 * days_stage + .55 * previous_delay
                      + (100 - compensation) * 1.3 + rng.normal(0, 42, rows)), 0, 1_500)
    delay_days = np.where(delay_flag == 1, np.maximum(delay_days, 1), 0)

    return pd.DataFrame({
        "project_id": [f"BG-{seed}-{i:06d}" for i in range(1, rows + 1)], "project_type": project_types,
        "state": states, "district": districts, "land_area_acres": land_area, "affected_families": families,
        "villages_affected": villages, "legal_disputes": legal_disputes, "ownership_conflicts": ownership_conflicts,
        "pending_court_cases": court_cases, "documentation_completion_pct": np.round(documentation, 2),
        "missing_documents": missing_docs, "compensation_completion_pct": np.round(compensation, 2),
        "compensation_pending_cases": pending_comp, "average_compensation_delay_days": comp_delay,
        "rehabilitation_completion_pct": np.round(rehabilitation, 2), "resettlement_completion_pct": np.round(resettlement, 2),
        "affected_families_rehabilitated": families_rehab, "pending_approvals": pending_approvals,
        "approval_delay_days": approval_delay, "stakeholder_response_delay_days": stakeholder_delay,
        "current_stage": stages, "days_in_current_stage": days_stage, "possession_completion_pct": np.round(possession, 2),
        "historical_delay_rate": np.round(historical_rate, 4), "days_remaining_to_target": target_remaining,
        "previous_stage_delay_days": previous_delay, "delay_flag": delay_flag, "actual_delay_days": delay_days,
    })


def validate_dataset(data: pd.DataFrame) -> dict[str, object]:
    """Validate schema constraints and return a printable validation summary."""
    percentage_columns = [column for column in data if column.endswith("_pct")]
    nonnegative_columns = [column for column in data.select_dtypes(include="number") if column not in percentage_columns]
    invalid_categories = (
        ~data["current_stage"].isin(STAGE_NAMES) | ~data["project_type"].isin(PROJECT_TYPES)
        | ~data.apply(lambda row: row["district"] in STATE_DISTRICTS.get(row["state"], ()), axis=1)
    )
    impossible = (
        (data["affected_families_rehabilitated"] > data["affected_families"])
        | ((data["delay_flag"] == 0) & (data["actual_delay_days"] != 0))
        | ((data["delay_flag"] == 1) & (data["actual_delay_days"] <= 0))
    )
    numeric = data.select_dtypes(include="number")
    corr = numeric.corr(numeric_only=True)[["delay_flag", "actual_delay_days"]].drop(index=["delay_flag", "actual_delay_days"], errors="ignore")
    suspicious = int((corr.abs() > .98).sum().sum())
    return {
        "rows": len(data), "missing_values": int(data.isna().sum().sum()),
        "duplicate_project_ids": int(data["project_id"].duplicated().sum()),
        "invalid_percentages": int(((data[percentage_columns] < 0) | (data[percentage_columns] > 100)).sum().sum()),
        "negative_values": int((data[nonnegative_columns] < 0).sum().sum()),
        "invalid_categories": int(invalid_categories.sum()), "impossible_combinations": int(impossible.sum()),
        "suspicious_perfect_correlations": suspicious,
        "target_class_distribution": data["delay_flag"].value_counts().sort_index().to_dict(),
    }


def print_validation_summary(summary: dict[str, object]) -> None:
    """Print a concise human-readable validation report."""
    print("Validation summary")
    for key, value in summary.items():
        print(f"- {key.replace('_', ' ')}: {value}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate BhoomiGuard synthetic acquisition cases.")
    parser.add_argument("--rows", type=int, default=5_000)
    parser.add_argument("--seed", type=int, default=RANDOM_SEED)
    parser.add_argument("--output", type=Path, default=RAW_DATA_PATH)
    args = parser.parse_args()
    data = generate_dataset(args.rows, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(args.output, index=False)
    print(f"Saved {len(data)} rows to {args.output}")
    print_validation_summary(validate_dataset(data))


if __name__ == "__main__":
    main()
