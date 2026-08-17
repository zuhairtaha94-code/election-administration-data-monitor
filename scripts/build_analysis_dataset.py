"""Build the analysis-ready jurisdiction file and metric-validation summary."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.data import load_eavs  # noqa: E402
from src.metrics import (  # noqa: E402
    MAIL_COMPARISON_MIN_RETURNED,
    MAIL_DESCRIPTIVE_MIN_RETURNED,
    MAIL_RECONCILIATION_ABSOLUTE_TOLERANCE,
    MAIL_RECONCILIATION_RELATIVE_TOLERANCE,
    REMOVAL_COMPARISON_MIN_REGISTERED,
    build_jurisdiction_metrics,
)


CSV_PATH = PROJECT_ROOT / "data" / "raw" / "2024_EAVS_for_Public_Release_nolabel_V2.csv"
PROCESSED_PATH = PROJECT_ROOT / "data" / "processed" / "analysis_jurisdictions.csv"
SUMMARY_PATH = PROJECT_ROOT / "reports" / "metric_validation_summary.json"


def rounded_distribution(series: pd.Series) -> dict[str, float | int | None]:
    clean = series.dropna()
    if clean.empty:
        return {
            "count": 0,
            "minimum": None,
            "median": None,
            "p95": None,
            "p99": None,
            "maximum": None,
        }
    return {
        "count": int(clean.size),
        "minimum": round(float(clean.min()), 4),
        "median": round(float(clean.median()), 4),
        "p95": round(float(clean.quantile(0.95)), 4),
        "p99": round(float(clean.quantile(0.99)), 4),
        "maximum": round(float(clean.max()), 4),
    }


def threshold_sensitivity(
    analysis: pd.DataFrame,
    denominator: str,
    metric: str,
    thresholds: list[int],
) -> list[dict[str, float | int]]:
    results = []
    for threshold in thresholds:
        mask = analysis[denominator].ge(threshold) & analysis[metric].notna()
        results.append(
            {
                "minimum_denominator": threshold,
                "jurisdictions": int(mask.sum()),
                "states_and_territories": int(
                    analysis.loc[mask, "State_Abbr"].nunique()
                ),
                "median": round(float(analysis.loc[mask, metric].median()), 4),
                "p99": round(float(analysis.loc[mask, metric].quantile(0.99)), 4),
                "maximum": round(float(analysis.loc[mask, metric].max()), 4),
            }
        )
    return results


def main() -> None:
    data = load_eavs(CSV_PATH)
    analysis = build_jurisdiction_metrics(data)

    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)
    analysis.to_csv(PROCESSED_PATH, index=False)

    mail_eligible = analysis["mail_comparison_eligible"]
    removal_eligible = analysis["removal_comparison_eligible"]
    mail_minimum_denominator = analysis["mail_returned_total"].ge(
        MAIL_COMPARISON_MIN_RETURNED
    ) & analysis["mail_rejection_rate_pct"].notna()

    summary = {
        "rules": {
            "mail_descriptive_minimum_returned": MAIL_DESCRIPTIVE_MIN_RETURNED,
            "mail_comparison_minimum_returned": MAIL_COMPARISON_MIN_RETURNED,
            "mail_material_reconciliation_gap": {
                "absolute_ballots_greater_than": MAIL_RECONCILIATION_ABSOLUTE_TOLERANCE,
                "relative_share_greater_than": MAIL_RECONCILIATION_RELATIVE_TOLERANCE,
                "logic": "both conditions must be true",
            },
            "removal_comparison_minimum_registered": REMOVAL_COMPARISON_MIN_REGISTERED,
        },
        "mail_rejection_metric": {
            "definition": "C9a / C1b * 100",
            "rate_available": int(analysis["mail_rejection_rate_pct"].notna().sum()),
            "meets_comparison_denominator": int(mail_minimum_denominator.sum()),
            "material_reconciliation_exclusions_at_comparison_threshold": int(
                (mail_minimum_denominator & analysis["mail_reconciliation_material"]).sum()
            ),
            "comparison_eligible": int(mail_eligible.sum()),
            "eligible_states_and_territories": int(
                analysis.loc[mail_eligible, "State_Abbr"].nunique()
            ),
            "eligible_rate_distribution_pct": rounded_distribution(
                analysis.loc[mail_eligible, "mail_rejection_rate_pct"]
            ),
            "denominator_sensitivity": threshold_sensitivity(
                analysis,
                "mail_returned_total",
                "mail_rejection_rate_pct",
                [1, 50, 100, 250, 500, 1_000],
            ),
        },
        "list_maintenance_metric": {
            "definition": "A12a / A1a * 1000",
            "interpretation": (
                "Two-year removal activity relative to a point-in-time registration count; "
                "not a probability and may exceed 1000."
            ),
            "rate_available": int(
                analysis["removals_per_1000_registered"].notna().sum()
            ),
            "comparison_eligible": int(removal_eligible.sum()),
            "eligible_states_and_territories": int(
                analysis.loc[removal_eligible, "State_Abbr"].nunique()
            ),
            "complete_reason_detail": int(
                analysis["removal_reason_detail_complete"].sum()
            ),
            "complete_reason_detail_nonzero_reconciliation_gaps": int(
                analysis["removal_reason_reconciliation_gap"].fillna(0).ne(0).sum()
            ),
            "eligible_rate_distribution_per_1000": rounded_distribution(
                analysis.loc[removal_eligible, "removals_per_1000_registered"]
            ),
            "denominator_sensitivity": threshold_sensitivity(
                analysis,
                "registered_total",
                "removals_per_1000_registered",
                [1, 500, 1_000, 5_000, 10_000],
            ),
        },
    }

    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {PROCESSED_PATH.relative_to(PROJECT_ROOT)}")
    print(f"Wrote {SUMMARY_PATH.relative_to(PROJECT_ROOT)}")
    print(
        json.dumps(
            {
                "mail_comparison_eligible": int(mail_eligible.sum()),
                "removal_comparison_eligible": int(removal_eligible.sum()),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
