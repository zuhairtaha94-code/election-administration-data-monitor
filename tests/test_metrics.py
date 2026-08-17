import unittest

import pandas as pd

from src.metrics import build_jurisdiction_metrics, wilson_interval_percent


def example_data() -> pd.DataFrame:
    data = pd.DataFrame(
        {
            "FIPSCode": ["001", "002", "003", "004"],
            "Jurisdiction_Name": ["Exact", "Gap", "Small", "Invalid"],
            "State_Full": ["Example"] * 4,
            "State_Abbr": ["EX"] * 4,
            "A1a": [1_000, 1_000, 999, 1_000],
            "A12a": [1_200, 100, 10, 20],
            "C1b": [600, 600, 499, 100],
            "C8a": [594, 500, 494, 0],
            "C9a": [6, 30, 5, 101],
        }
    )
    for column in [f"A12{suffix}" for suffix in "bcdefghijk"]:
        data[column] = 0
    return data


class MetricConstructionTest(unittest.TestCase):
    def test_wilson_interval_for_ten_of_one_hundred(self) -> None:
        lower, upper = wilson_interval_percent(
            pd.Series([10]),
            pd.Series([100]),
        )

        self.assertAlmostEqual(lower.iloc[0], 5.5229, places=4)
        self.assertAlmostEqual(upper.iloc[0], 17.4366, places=4)

    def test_mail_comparison_gate_combines_size_and_quality_rules(self) -> None:
        result = build_jurisdiction_metrics(example_data())

        self.assertTrue(result.loc[0, "mail_comparison_eligible"])
        self.assertTrue(result.loc[1, "mail_reconciliation_material"])
        self.assertFalse(result.loc[1, "mail_comparison_eligible"])
        self.assertEqual(result.loc[2, "mail_denominator_tier"], "descriptive_100_to_499")
        self.assertFalse(result.loc[2, "mail_comparison_eligible"])
        self.assertFalse(result.loc[3, "mail_counts_logically_valid"])
        self.assertTrue(pd.isna(result.loc[3, "mail_rejection_rate_pct"]))

    def test_removal_intensity_can_exceed_one_thousand(self) -> None:
        result = build_jurisdiction_metrics(example_data())

        self.assertEqual(result.loc[0, "removals_per_1000_registered"], 1_200)
        self.assertTrue(result.loc[0, "removal_comparison_eligible"])


if __name__ == "__main__":
    unittest.main()
