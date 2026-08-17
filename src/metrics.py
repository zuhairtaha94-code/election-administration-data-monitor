"""Construct transparent, quality-controlled EAVS jurisdiction metrics."""

from __future__ import annotations

import pandas as pd

from src.data import valid_numeric


MAIL_DESCRIPTIVE_MIN_RETURNED = 100
MAIL_COMPARISON_MIN_RETURNED = 500
MAIL_RECONCILIATION_ABSOLUTE_TOLERANCE = 10
MAIL_RECONCILIATION_RELATIVE_TOLERANCE = 0.01
REMOVAL_COMPARISON_MIN_REGISTERED = 1_000
WILSON_Z_95 = 1.959963984540054

IDENTIFIER_COLUMNS = ["FIPSCode", "Jurisdiction_Name", "State_Full", "State_Abbr"]
REMOVAL_REASON_COLUMNS = [f"A12{suffix}" for suffix in "bcdefghijk"]


def wilson_interval_percent(
    successes: pd.Series,
    totals: pd.Series,
    z: float = WILSON_Z_95,
) -> tuple[pd.Series, pd.Series]:
    """Return a Wilson score interval as percentages for binomial counts."""

    success = valid_numeric(successes)
    total = valid_numeric(totals)
    valid = total.gt(0) & success.notna() & success.le(total)

    proportion = success / total
    denominator = 1 + z**2 / total
    center = (proportion + z**2 / (2 * total)) / denominator
    spread = (
        z
        * (proportion * (1 - proportion) / total + z**2 / (4 * total**2)) ** 0.5
        / denominator
    )

    lower = ((center - spread) * 100).where(valid)
    upper = ((center + spread) * 100).where(valid)
    return lower, upper


def _mail_denominator_tier(returned: pd.Series) -> pd.Series:
    tier = pd.Series("unavailable_or_zero", index=returned.index, dtype="string")
    tier.loc[returned.gt(0) & returned.lt(MAIL_DESCRIPTIVE_MIN_RETURNED)] = "below_100"
    tier.loc[
        returned.ge(MAIL_DESCRIPTIVE_MIN_RETURNED)
        & returned.lt(MAIL_COMPARISON_MIN_RETURNED)
    ] = "descriptive_100_to_499"
    tier.loc[returned.ge(MAIL_COMPARISON_MIN_RETURNED)] = "comparison_500_plus"
    return tier


def _removal_denominator_tier(registered: pd.Series) -> pd.Series:
    tier = pd.Series("unavailable_or_zero", index=registered.index, dtype="string")
    tier.loc[
        registered.gt(0) & registered.lt(REMOVAL_COMPARISON_MIN_REGISTERED)
    ] = "below_1000"
    tier.loc[registered.ge(REMOVAL_COMPARISON_MIN_REGISTERED)] = "comparison_1000_plus"
    return tier


def build_jurisdiction_metrics(data: pd.DataFrame) -> pd.DataFrame:
    """Build analysis-ready metrics while retaining explicit quality-control flags."""

    required = set(
        IDENTIFIER_COLUMNS
        + ["A1a", "A12a", "C1b", "C8a", "C9a"]
        + REMOVAL_REASON_COLUMNS
    )
    missing = sorted(required - set(data.columns))
    if missing:
        raise KeyError(f"Missing required metric columns: {missing}")

    output = data[IDENTIFIER_COLUMNS].copy()

    registered = valid_numeric(data["A1a"])
    removed = valid_numeric(data["A12a"])
    returned = valid_numeric(data["C1b"])
    counted = valid_numeric(data["C8a"])
    rejected = valid_numeric(data["C9a"])

    for name, values in {
        "registered_total": registered,
        "removed_total": removed,
        "mail_returned_total": returned,
        "mail_counted_total": counted,
        "mail_rejected_total": rejected,
    }.items():
        output[name] = values.astype("Int64")

    removal_available = registered.gt(0) & removed.notna()
    output["removals_per_1000_registered"] = (
        removed / registered * 1_000
    ).where(removal_available)
    output["removal_denominator_tier"] = _removal_denominator_tier(registered)
    output["removal_comparison_eligible"] = (
        removal_available & registered.ge(REMOVAL_COMPARISON_MIN_REGISTERED)
    )

    reason_values = pd.concat(
        {column: valid_numeric(data[column]) for column in REMOVAL_REASON_COLUMNS},
        axis=1,
    )
    reason_detail_complete = reason_values.notna().all(axis=1) & removed.notna()
    reason_sum = reason_values.sum(axis=1, min_count=len(REMOVAL_REASON_COLUMNS))
    output["removal_reason_detail_complete"] = reason_detail_complete
    output["removal_reason_reconciliation_gap"] = (
        reason_sum - removed
    ).where(reason_detail_complete).astype("Int64")

    mail_counts_logically_valid = (
        returned.gt(0) & rejected.notna() & rejected.le(returned)
    )
    output["mail_counts_logically_valid"] = mail_counts_logically_valid
    output["mail_denominator_tier"] = _mail_denominator_tier(returned)
    output["mail_rejection_rate_pct"] = (
        rejected / returned * 100
    ).where(mail_counts_logically_valid)
    interval_lower, interval_upper = wilson_interval_percent(rejected, returned)
    output["mail_rejection_ci95_lower_pct"] = interval_lower
    output["mail_rejection_ci95_upper_pct"] = interval_upper

    reconciliation_available = returned.gt(0) & counted.notna() & rejected.notna()
    reconciliation_gap = (counted + rejected - returned).where(
        reconciliation_available
    )
    reconciliation_relative_gap = (
        reconciliation_gap.abs() / returned
    ).where(reconciliation_available)
    material_reconciliation_gap = (
        reconciliation_available
        & reconciliation_gap.abs().gt(MAIL_RECONCILIATION_ABSOLUTE_TOLERANCE)
        & reconciliation_relative_gap.gt(MAIL_RECONCILIATION_RELATIVE_TOLERANCE)
    )

    output["mail_reconciliation_available"] = reconciliation_available
    output["mail_reconciliation_gap"] = reconciliation_gap.astype("Int64")
    output["mail_reconciliation_gap_pct"] = reconciliation_relative_gap * 100
    output["mail_reconciliation_material"] = material_reconciliation_gap
    output["mail_comparison_eligible"] = (
        mail_counts_logically_valid
        & returned.ge(MAIL_COMPARISON_MIN_RETURNED)
        & reconciliation_available
        & ~material_reconciliation_gap
    )

    return output
