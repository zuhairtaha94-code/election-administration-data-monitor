import unittest

import pandas as pd

from src.outliers import (
    add_mail_state_context,
    add_removal_state_context,
    fit_beta_binomial,
    modified_z_scores,
)


class OutlierScreenTest(unittest.TestCase):
    def test_beta_binomial_fit_returns_positive_parameters(self) -> None:
        fit = fit_beta_binomial(
            pd.Series([5, 7, 8, 10, 12]),
            pd.Series([1_000] * 5),
        )

        self.assertTrue(fit.converged)
        self.assertGreater(fit.alpha, 0)
        self.assertGreater(fit.beta, 0)

    def test_modified_z_score_identifies_extreme_high_value(self) -> None:
        scores = modified_z_scores(pd.Series([0, 1, 2, 3, 100]))

        self.assertGreater(scores.iloc[-1], 3.5)

    def test_mail_screen_flags_extreme_count_with_sufficient_peers(self) -> None:
        frame = pd.DataFrame(
            {
                "State_Abbr": ["EX"] * 12,
                "mail_comparison_eligible": [True] * 12,
                "mail_returned_total": [1_000] * 12,
                "mail_rejected_total": [10] * 11 + [100],
                "mail_rejection_ci95_lower_pct": [0.5] * 11 + [8.3],
            }
        )

        result = add_mail_state_context(frame)

        self.assertFalse(result.loc[:10, "mail_high_priority_review"].any())
        self.assertTrue(result.loc[11, "mail_high_priority_review"])

    def test_removal_screen_requires_ten_state_peers(self) -> None:
        frame = pd.DataFrame(
            {
                "State_Abbr": ["EX"] * 12 + ["SM"] * 3,
                "removal_comparison_eligible": [True] * 15,
                "removals_per_1000_registered": (
                    [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 500]
                    + [10, 11, 500]
                ),
            }
        )

        result = add_removal_state_context(frame)

        self.assertTrue(result.loc[11, "removal_high_priority_review"])
        self.assertFalse(result.loc[14, "removal_high_priority_review"])


if __name__ == "__main__":
    unittest.main()
