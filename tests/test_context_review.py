import unittest

import pandas as pd

from src.context_review import build_context_review, reason_profile


class ContextReviewTests(unittest.TestCase):
    def test_reason_profile_ignores_sentinel_codes(self) -> None:
        row = pd.Series(
            {
                "C9a": 10,
                "C9b": 6,
                "C9c": 2,
                "C9d": -88,
                "C9e": -99,
                "C9f": -77,
                "C9g": 0,
                "C9h": 0,
                "C9i": 0,
                "C9j": 0,
                "C9k": 0,
                "C9l": 0,
                "C9m": 0,
                "C9n": 0,
                "C9o": 0,
                "C9p": 0,
                "C9q": 0,
                "C9r": 2,
                "C9s": 0,
                "C9t": 0,
                "C9r_Other": "Affidavit incomplete",
            }
        )
        profile = reason_profile(row)
        self.assertEqual(profile["reported_reason_total"], 10)
        self.assertEqual(profile["reason_reconciliation_gap"], 0)
        self.assertEqual(profile["dominant_reported_reason"], "late arrival")
        self.assertEqual(profile["dominant_reason_share_pct"], 60.0)
        self.assertIn("affidavit incomplete", profile["reported_reason_profile"])

    def test_context_configuration_must_match_candidates(self) -> None:
        triage = pd.DataFrame(
            {
                "FIPSCode": pd.Series(["001"], dtype="string"),
                "mail_high_priority_review": [True],
            }
        )
        with self.assertRaisesRegex(ValueError, "match flagged candidates exactly"):
            build_context_review(triage, pd.DataFrame(), {})


if __name__ == "__main__":
    unittest.main()
