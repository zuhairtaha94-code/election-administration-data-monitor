"""Run state-aware statistical screening and write a transparent summary."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.outliers import (  # noqa: E402
    FAMILYWISE_ALPHA,
    MINIMUM_STATE_PEERS,
    MODIFIED_Z_THRESHOLD,
    build_outlier_triage,
)


ANALYSIS_PATH = PROJECT_ROOT / "data" / "processed" / "analysis_jurisdictions.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "outlier_triage.csv"
SUMMARY_PATH = PROJECT_ROOT / "reports" / "outlier_triage_summary.json"


def records(frame: pd.DataFrame, columns: list[str]) -> list[dict[str, object]]:
    """Convert selected rows to JSON-safe records with readable numeric precision."""

    selected = frame[columns].copy()
    for column in selected.select_dtypes(include="number"):
        if column.endswith("_total") or column.endswith("_peer_count"):
            selected[column] = selected[column].round().astype("Int64")
        elif "probability" in column or "threshold" in column:
            selected[column] = selected[column].round(12)
        else:
            selected[column] = selected[column].round(6)
    return selected.where(pd.notna(selected), None).to_dict(orient="records")


def main() -> None:
    analysis = pd.read_csv(ANALYSIS_PATH, dtype={"FIPSCode": "string"})
    triage = build_outlier_triage(analysis)
    triage.to_csv(OUTPUT_PATH, index=False)

    mail_modeled = triage["mail_state_model_converged"]
    mail_candidates = triage.loc[triage["mail_high_priority_review"]].sort_values(
        "mail_upper_tail_probability"
    )
    removal_modeled = triage["removal_state_peer_count"].ge(MINIMUM_STATE_PEERS)
    removal_candidates = triage.loc[
        triage["removal_high_priority_review"]
    ].sort_values("removal_modified_z", ascending=False)

    summary = {
        "interpretation": (
            "Flags identify statistical review candidates, not errors, misconduct, "
            "fraud, or disenfranchisement. Policy and reporting context is required."
        ),
        "mail_rejection_screen": {
            "method": (
                "Within-state beta-binomial upper-tail screen with a Bonferroni "
                "familywise correction and a Wilson-interval confirmation rule."
            ),
            "minimum_state_peers": MINIMUM_STATE_PEERS,
            "familywise_alpha_per_state": FAMILYWISE_ALPHA,
            "comparison_eligible": int(triage["mail_comparison_eligible"].sum()),
            "modeled_jurisdictions": int(mail_modeled.sum()),
            "modeled_states_and_territories": int(
                triage.loc[mail_modeled, "State_Abbr"].nunique()
            ),
            "high_priority_review_candidates": int(
                triage["mail_high_priority_review"].sum()
            ),
            "candidate_states": int(mail_candidates["State_Abbr"].nunique()),
            "candidates": records(
                mail_candidates,
                [
                    "State_Abbr",
                    "Jurisdiction_Name",
                    "FIPSCode",
                    "mail_returned_total",
                    "mail_rejected_total",
                    "mail_rejection_rate_pct",
                    "mail_rejection_ci95_lower_pct",
                    "mail_rejection_ci95_upper_pct",
                    "mail_state_weighted_rate_pct",
                    "mail_state_peer_count",
                    "mail_upper_tail_probability",
                    "mail_bonferroni_threshold",
                ],
            ),
        },
        "list_maintenance_screen": {
            "method": (
                "Within-state modified z-score on log1p removals per 1,000 "
                "registered voters."
            ),
            "minimum_state_peers": MINIMUM_STATE_PEERS,
            "modified_z_threshold": MODIFIED_Z_THRESHOLD,
            "comparison_eligible": int(
                triage["removal_comparison_eligible"].sum()
            ),
            "screened_jurisdictions": int(removal_modeled.sum()),
            "screened_states_and_territories": int(
                triage.loc[removal_modeled, "State_Abbr"].nunique()
            ),
            "high_priority_review_candidates": int(
                triage["removal_high_priority_review"].sum()
            ),
            "candidate_states": int(removal_candidates["State_Abbr"].nunique()),
            "top_candidates_by_modified_z": records(
                removal_candidates.head(15),
                [
                    "State_Abbr",
                    "Jurisdiction_Name",
                    "FIPSCode",
                    "registered_total",
                    "removed_total",
                    "removals_per_1000_registered",
                    "removal_state_median_per_1000",
                    "removal_state_peer_count",
                    "removal_state_percentile",
                    "removal_modified_z",
                ],
            ),
        },
    }

    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(PROJECT_ROOT)}")
    print(f"Wrote {SUMMARY_PATH.relative_to(PROJECT_ROOT)}")
    print(
        json.dumps(
            {
                "mail_review_candidates": len(mail_candidates),
                "removal_review_candidates": len(removal_candidates),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
