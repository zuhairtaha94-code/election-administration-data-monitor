"""Create a compact, reproducible audit of the raw EAVS data and codebook."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.data import (  # noqa: E402
    SENTINEL_LABELS,
    load_codebook,
    load_eavs,
    response_profile,
    sha256_file,
    valid_numeric,
)


CSV_PATH = PROJECT_ROOT / "data" / "raw" / "2024_EAVS_for_Public_Release_nolabel_V2.csv"
CODEBOOK_PATH = PROJECT_ROOT / "data" / "raw" / "2024_EAVS_Codebook.xlsx"
OUTPUT_PATH = PROJECT_ROOT / "reports" / "data_audit_summary.json"

TARGET_VARIABLES = ["A1a", "A1b", "A1c", "A12a", "C1a", "C1b", "C7a", "C7b", "C7c", "C8a", "C9a"]


def rounded_summary(series: pd.Series) -> dict[str, float | int | None]:
    clean = series.dropna()
    if clean.empty:
        return {"count": 0, "minimum": None, "median": None, "maximum": None}
    return {
        "count": int(clean.size),
        "minimum": round(float(clean.min()), 4),
        "median": round(float(clean.median()), 4),
        "maximum": round(float(clean.max()), 4),
    }


def main() -> None:
    data = load_eavs(CSV_PATH)
    codebook = load_codebook(CODEBOOK_PATH)

    required_identifiers = {"FIPSCode", "Jurisdiction_Name", "State_Full", "State_Abbr"}
    missing_identifiers = sorted(required_identifiers - set(data.columns))
    if missing_identifiers:
        raise KeyError(f"Missing required identifier columns: {missing_identifiers}")

    missing_codebook_columns = sorted(set(data.columns) - set(codebook["VariableName"]))
    extra_codebook_variables = sorted(set(codebook["VariableName"]) - set(data.columns))
    codebook_labels = codebook.set_index("VariableName")["Label"].to_dict()

    numeric = data.select_dtypes(include="number")
    sentinel_totals = {
        label: int((numeric == code).sum().sum())
        for code, label in SENTINEL_LABELS.items()
    }

    returned = valid_numeric(data["C1b"])
    counted = valid_numeric(data["C8a"])
    rejected = valid_numeric(data["C9a"])
    mail_rate_mask = returned.gt(0) & rejected.notna()
    mail_rejection_rate = (rejected / returned * 100).where(mail_rate_mask)

    mail_reconciliation_mask = returned.notna() & counted.notna() & rejected.notna()
    mail_reconciliation_difference = (
        counted + rejected - returned
    ).where(mail_reconciliation_mask)
    comparable_mail_differences = mail_reconciliation_difference[
        mail_reconciliation_mask
    ]

    total_registered = valid_numeric(data["A1a"])
    removed = valid_numeric(data["A12a"])
    removal_mask = total_registered.gt(0) & removed.notna()
    removals_per_1000_registered = (
        removed / total_registered * 1000
    ).where(removal_mask)

    audit = {
        "source_files": {
            CSV_PATH.name: {"sha256": sha256_file(CSV_PATH)},
            CODEBOOK_PATH.name: {"sha256": sha256_file(CODEBOOK_PATH)},
        },
        "dataset_shape": {
            "rows": int(data.shape[0]),
            "columns": int(data.shape[1]),
            "states_and_territories": int(data["State_Abbr"].nunique()),
            "unique_fips_codes": int(data["FIPSCode"].nunique()),
            "duplicate_fips_codes": int(data["FIPSCode"].duplicated().sum()),
        },
        "codebook_alignment": {
            "codebook_variable_rows": int(codebook.shape[0]),
            "data_columns_missing_from_codebook": missing_codebook_columns,
            "codebook_variables_missing_from_data": extra_codebook_variables,
        },
        "sentinel_totals_across_numeric_columns": sentinel_totals,
        "target_variable_profiles": {
            variable: {
                "label": codebook_labels.get(variable),
                **response_profile(data[variable]),
            }
            for variable in TARGET_VARIABLES
        },
        "candidate_metric_audit": {
            "mail_rejection_rate_percent": {
                "definition": "C9a / C1b * 100",
                "summary_before_denominator_threshold": rounded_summary(mail_rejection_rate),
                "values_above_100_percent": int(mail_rejection_rate.gt(100).sum()),
            },
            "mail_ballot_reconciliation": {
                "definition": "C8a + C9a - C1b",
                "comparable_records": int(mail_reconciliation_mask.sum()),
                "exact_matches": int(comparable_mail_differences.eq(0).sum()),
                "nonzero_differences": int(comparable_mail_differences.ne(0).sum()),
            },
            "removals_per_1000_registered": {
                "definition": "A12a / A1a * 1000",
                "summary_before_contextual_filters": rounded_summary(removals_per_1000_registered),
            },
        },
    }

    OUTPUT_PATH.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(PROJECT_ROOT)}")
    print(json.dumps(audit["dataset_shape"], indent=2))
    print(json.dumps(audit["candidate_metric_audit"], indent=2))


if __name__ == "__main__":
    main()
