"""Build a documented contextual review of mail-ballot screening candidates."""

from __future__ import annotations

from collections.abc import Mapping

import pandas as pd

from src.data import valid_numeric


REASON_LABELS = {
    "C9b": "late arrival",
    "C9c": "missing voter signature",
    "C9d": "missing witness signature",
    "C9e": "nonmatching voter signature",
    "C9f": "unofficial envelope",
    "C9g": "ballot missing from envelope",
    "C9h": "missing secrecy envelope",
    "C9i": "multiple ballots in one envelope",
    "C9j": "unsealed envelope",
    "C9k": "missing postmark",
    "C9l": "missing resident address",
    "C9m": "voter reported deceased",
    "C9n": "voter already voted",
    "C9o": "missing documentation",
    "C9p": "voter not eligible",
    "C9q": "missing ballot application",
    "C9r": "other reason 1",
    "C9s": "other reason 2",
    "C9t": "other reason 3",
}

OTHER_TEXT_COLUMNS = {
    "C9r": "C9r_Other",
    "C9s": "C9s_Other",
    "C9t": "C9t_Other",
}

ALLOWED_STATUSES = {
    "externally corroborated",
    "internally reconciled",
    "partially reconciled",
    "unresolved",
}


def _reason_label(row: pd.Series, column: str) -> str:
    """Return a readable reason label, retaining useful free-text detail."""

    label = REASON_LABELS[column]
    text_column = OTHER_TEXT_COLUMNS.get(column)
    if text_column is None:
        return label
    detail = row.get(text_column)
    if pd.isna(detail) or not str(detail).strip():
        return label
    return f"{label}: {str(detail).strip().lower()}"


def reason_profile(row: pd.Series) -> dict[str, object]:
    """Summarize reported rejection reasons for one EAVS jurisdiction record."""

    rejected = valid_numeric(pd.Series([row["C9a"]])).iloc[0]
    values = {
        column: valid_numeric(pd.Series([row.get(column)])).iloc[0]
        for column in REASON_LABELS
    }
    reported = [
        (_reason_label(row, column), int(value))
        for column, value in values.items()
        if pd.notna(value) and value > 0
    ]
    reported.sort(key=lambda item: (-item[1], item[0]))

    known_total = sum(value for _, value in reported)
    coverage = known_total / rejected * 100 if pd.notna(rejected) and rejected > 0 else None
    gap = known_total - int(rejected) if pd.notna(rejected) else None
    top_label, top_total = reported[0] if reported else ("no reason detail reported", 0)
    top_share = top_total / rejected * 100 if pd.notna(rejected) and rejected > 0 else None

    return {
        "reported_reason_total": known_total,
        "reason_reconciliation_gap": gap,
        "reason_coverage_pct": coverage,
        "dominant_reported_reason": top_label,
        "dominant_reason_total": top_total,
        "dominant_reason_share_pct": top_share,
        "reported_reason_profile": "; ".join(
            f"{label} ({value})" for label, value in reported[:4]
        )
        or "no positive reason counts reported",
    }


def build_context_review(
    triage: pd.DataFrame,
    raw: pd.DataFrame,
    context_by_fips: Mapping[str, Mapping[str, object]],
) -> pd.DataFrame:
    """Combine statistical candidates, raw reason fields, and curated context."""

    candidates = triage.loc[triage["mail_high_priority_review"].fillna(False)].copy()
    candidates["FIPSCode"] = candidates["FIPSCode"].astype("string")

    flagged_fips = set(candidates["FIPSCode"])
    configured_fips = set(context_by_fips)
    if flagged_fips != configured_fips:
        missing = sorted(flagged_fips - configured_fips)
        extra = sorted(configured_fips - flagged_fips)
        raise ValueError(
            "Context configuration must match flagged candidates exactly; "
            f"missing={missing}, extra={extra}"
        )

    raw_subset = raw.copy()
    raw_subset["FIPSCode"] = raw_subset["FIPSCode"].astype("string")

    reason_columns = list(REASON_LABELS) + list(OTHER_TEXT_COLUMNS.values()) + [
        "FIPSCode",
        "C9a",
        "C9Comments",
        "C7a",
        "C7b",
        "C7c",
    ]
    missing_raw = sorted(set(reason_columns) - set(raw_subset.columns))
    if missing_raw:
        raise KeyError(f"Missing contextual-review columns: {missing_raw}")

    merged = candidates.merge(
        raw_subset[reason_columns],
        on="FIPSCode",
        how="left",
        validate="one_to_one",
    )
    rows: list[dict[str, object]] = []
    for _, row in merged.iterrows():
        fips = str(row["FIPSCode"])
        context = dict(context_by_fips[fips])
        status = str(context["validation_status"])
        if status not in ALLOWED_STATUSES:
            raise ValueError(f"Unsupported validation status for {fips}: {status}")

        profile = reason_profile(row)
        returned = int(row["mail_returned_total"])
        rejected = int(row["mail_rejected_total"])
        counted = int(row["mail_counted_total"])
        source_titles = " | ".join(
            str(source["title"]) for source in context["sources"]
        )
        source_urls = " | ".join(str(source["url"]) for source in context["sources"])

        rows.append(
            {
                "FIPSCode": fips,
                "jurisdiction": context["display_name"],
                "state": row["State_Abbr"],
                "mail_returned_total": returned,
                "mail_counted_total": counted,
                "mail_rejected_total": rejected,
                "mail_rejection_rate_pct": row["mail_rejection_rate_pct"],
                "state_weighted_rate_pct": row["mail_state_weighted_rate_pct"],
                "aggregate_reconciliation_gap": counted + rejected - returned,
                **profile,
                "cure_entered": valid_numeric(pd.Series([row["C7a"]])).iloc[0],
                "cure_successful": valid_numeric(pd.Series([row["C7b"]])).iloc[0],
                "cure_unsuccessful": valid_numeric(pd.Series([row["C7c"]])).iloc[0],
                "validation_status": status,
                "evidence_level": context["evidence_level"],
                "responsible_conclusion": context["responsible_conclusion"],
                "external_evidence": context["external_evidence"],
                "source_titles": source_titles,
                "source_urls": source_urls,
                "eavs_comment": row["C9Comments"],
            }
        )

    output = pd.DataFrame(rows)
    numeric_columns = [
        "mail_rejection_rate_pct",
        "state_weighted_rate_pct",
        "reason_coverage_pct",
        "dominant_reason_share_pct",
    ]
    output[numeric_columns] = output[numeric_columns].round(3)
    integer_nullable = ["cure_entered", "cure_successful", "cure_unsuccessful"]
    output[integer_nullable] = output[integer_nullable].astype("Int64")
    return output.sort_values(
        ["validation_status", "mail_rejection_rate_pct"],
        ascending=[True, False],
    ).reset_index(drop=True)
