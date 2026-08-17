"""Build the contextual-validation table and machine-readable summary."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.context_review import build_context_review  # noqa: E402
from src.data import load_eavs  # noqa: E402


RAW_PATH = PROJECT_ROOT / "data" / "raw" / "2024_EAVS_for_Public_Release_nolabel_V2.csv"
TRIAGE_PATH = PROJECT_ROOT / "data" / "processed" / "outlier_triage.csv"
CONTEXT_PATH = PROJECT_ROOT / "data" / "context_sources.json"
OUTPUT_PATH = PROJECT_ROOT / "reports" / "context_review.csv"
SUMMARY_PATH = PROJECT_ROOT / "reports" / "context_review_summary.json"


def main() -> None:
    context = json.loads(CONTEXT_PATH.read_text(encoding="utf-8"))
    context_by_fips = {
        candidate["fips"]: candidate for candidate in context["candidates"]
    }
    raw = load_eavs(RAW_PATH)
    triage = pd.read_csv(TRIAGE_PATH, dtype={"FIPSCode": "string"})
    review = build_context_review(triage, raw, context_by_fips)
    review.to_csv(OUTPUT_PATH, index=False)

    status_counts = {
        key: int(value)
        for key, value in review["validation_status"].value_counts().sort_index().items()
    }
    summary = {
        "review_date": context["review_date"],
        "interpretation": context["interpretation"],
        "status_definitions": context["status_definitions"],
        "candidates_reviewed": int(len(review)),
        "aggregate_reconciliation_gaps": int(
            review["aggregate_reconciliation_gap"].ne(0).sum()
        ),
        "complete_reason_reconciliations": int(
            review["reason_reconciliation_gap"].eq(0).sum()
        ),
        "status_counts": status_counts,
        "candidates": review[
            [
                "jurisdiction",
                "FIPSCode",
                "mail_rejection_rate_pct",
                "state_weighted_rate_pct",
                "dominant_reported_reason",
                "dominant_reason_total",
                "dominant_reason_share_pct",
                "reason_coverage_pct",
                "validation_status",
                "responsible_conclusion",
            ]
        ].to_dict(orient="records"),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(PROJECT_ROOT)}")
    print(f"Wrote {SUMMARY_PATH.relative_to(PROJECT_ROOT)}")
    print(json.dumps(status_counts, indent=2))


if __name__ == "__main__":
    main()
