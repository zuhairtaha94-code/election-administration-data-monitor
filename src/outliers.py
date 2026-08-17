"""State-aware statistical screening for EAVS jurisdiction review candidates."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import betaln, gammaln
from scipy.stats import betabinom


MINIMUM_STATE_PEERS = 10
FAMILYWISE_ALPHA = 0.05
MODIFIED_Z_THRESHOLD = 3.5
MODIFIED_Z_SCALE = 0.6744897501960817


@dataclass(frozen=True)
class BetaBinomialFit:
    """Parameters and convergence status for a beta-binomial state model."""

    alpha: float
    beta: float
    converged: bool


def fit_beta_binomial(successes: pd.Series, totals: pd.Series) -> BetaBinomialFit:
    """Estimate beta-binomial shape parameters by maximum likelihood."""

    success = successes.to_numpy(dtype=float)
    total = totals.to_numpy(dtype=float)
    if success.size == 0 or success.size != total.size:
        raise ValueError("Success and total counts must have equal, positive length.")
    if np.any(total <= 0) or np.any(success < 0) or np.any(success > total):
        raise ValueError("Beta-binomial counts must satisfy 0 <= successes <= totals.")

    def negative_log_likelihood(log_parameters: np.ndarray) -> float:
        alpha, beta = np.exp(log_parameters)
        log_likelihood = (
            gammaln(total + 1)
            - gammaln(success + 1)
            - gammaln(total - success + 1)
            + betaln(success + alpha, total - success + beta)
            - betaln(alpha, beta)
        ).sum()
        return float(-log_likelihood)

    pooled_rate = (success.sum() + 0.5) / (total.sum() + 1)
    initial = np.log(
        [
            max(pooled_rate * 20, 0.01),
            max((1 - pooled_rate) * 20, 0.01),
        ]
    )
    result = minimize(
        negative_log_likelihood,
        initial,
        method="L-BFGS-B",
        bounds=[(-10, 15), (-10, 15)],
    )
    alpha, beta = np.exp(result.x)
    return BetaBinomialFit(
        alpha=float(alpha),
        beta=float(beta),
        converged=bool(result.success),
    )


def modified_z_scores(values: pd.Series) -> pd.Series:
    """Return median/MAD-based modified z-scores, or missing values when MAD is zero."""

    numeric = pd.to_numeric(values, errors="coerce")
    median = numeric.median()
    mad = (numeric - median).abs().median()
    if pd.isna(mad) or mad == 0:
        return pd.Series(np.nan, index=values.index, dtype=float)
    return MODIFIED_Z_SCALE * (numeric - median) / mad


def add_mail_state_context(analysis: pd.DataFrame) -> pd.DataFrame:
    """Add state beta-binomial screening fields for eligible mail-rejection records."""

    output = analysis.copy()
    output["mail_state_peer_count"] = pd.Series(pd.NA, index=output.index, dtype="Int64")
    output["mail_state_weighted_rate_pct"] = np.nan
    output["mail_state_beta_alpha"] = np.nan
    output["mail_state_beta_beta"] = np.nan
    output["mail_upper_tail_probability"] = np.nan
    output["mail_bonferroni_threshold"] = np.nan
    output["mail_state_model_converged"] = False

    eligible = output["mail_comparison_eligible"].fillna(False)
    for _, group in output.loc[eligible].groupby("State_Abbr"):
        index = group.index
        peer_count = len(group)
        state_rate = (
            group["mail_rejected_total"].sum()
            / group["mail_returned_total"].sum()
            * 100
        )
        output.loc[index, "mail_state_peer_count"] = peer_count
        output.loc[index, "mail_state_weighted_rate_pct"] = state_rate

        if peer_count < MINIMUM_STATE_PEERS:
            continue

        fit = fit_beta_binomial(
            group["mail_rejected_total"],
            group["mail_returned_total"],
        )
        output.loc[index, "mail_state_beta_alpha"] = fit.alpha
        output.loc[index, "mail_state_beta_beta"] = fit.beta
        output.loc[index, "mail_state_model_converged"] = fit.converged
        if not fit.converged:
            continue

        upper_tail = betabinom.sf(
            group["mail_rejected_total"].to_numpy(dtype=float) - 1,
            group["mail_returned_total"].to_numpy(dtype=float),
            fit.alpha,
            fit.beta,
        )
        output.loc[index, "mail_upper_tail_probability"] = upper_tail
        output.loc[index, "mail_bonferroni_threshold"] = (
            FAMILYWISE_ALPHA / peer_count
        )

    output["mail_high_priority_review"] = (
        eligible
        & output["mail_state_model_converged"]
        & output["mail_upper_tail_probability"].lt(
            output["mail_bonferroni_threshold"]
        )
        & output["mail_rejection_ci95_lower_pct"].gt(
            output["mail_state_weighted_rate_pct"]
        )
    )
    return output


def add_removal_state_context(analysis: pd.DataFrame) -> pd.DataFrame:
    """Add within-state robust screening fields for list-maintenance intensity."""

    output = analysis.copy()
    output["removal_state_peer_count"] = pd.Series(
        pd.NA, index=output.index, dtype="Int64"
    )
    output["removal_state_median_per_1000"] = np.nan
    output["removal_state_percentile"] = np.nan
    output["removal_modified_z"] = np.nan

    eligible = output["removal_comparison_eligible"].fillna(False)
    for _, group in output.loc[eligible].groupby("State_Abbr"):
        index = group.index
        peer_count = len(group)
        output.loc[index, "removal_state_peer_count"] = peer_count
        output.loc[index, "removal_state_median_per_1000"] = group[
            "removals_per_1000_registered"
        ].median()
        output.loc[index, "removal_state_percentile"] = group[
            "removals_per_1000_registered"
        ].rank(method="max", pct=True)

        if peer_count < MINIMUM_STATE_PEERS:
            continue

        transformed = np.log1p(group["removals_per_1000_registered"])
        output.loc[index, "removal_modified_z"] = modified_z_scores(transformed)

    output["removal_high_priority_review"] = (
        eligible
        & output["removal_state_peer_count"].ge(MINIMUM_STATE_PEERS)
        & output["removal_modified_z"].gt(MODIFIED_Z_THRESHOLD)
    )
    return output


def build_outlier_triage(analysis: pd.DataFrame) -> pd.DataFrame:
    """Apply both state-aware screening methods to the jurisdiction dataset."""

    return add_removal_state_context(add_mail_state_context(analysis))
