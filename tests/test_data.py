import unittest

import pandas as pd

from src.data import response_profile, valid_numeric


class DataUtilitiesTest(unittest.TestCase):
    def test_valid_numeric_replaces_eavs_sentinels_and_blanks(self) -> None:
        source = pd.Series([10, 0, -77, -88, -99, None, "not numeric"])

        result = valid_numeric(source)

        self.assertEqual(result.iloc[0], 10)
        self.assertEqual(result.iloc[1], 0)
        self.assertTrue(result.iloc[2:].isna().all())

    def test_response_profile_keeps_missing_categories_distinct(self) -> None:
        source = pd.Series([5, 0, -77, -88, -99, None, "not numeric"])

        self.assertEqual(
            response_profile(source),
            {
                "valid_skip": 1,
                "does_not_apply": 1,
                "data_not_available": 1,
                "missing_blank_or_invalid": 2,
                "valid_nonnegative": 2,
            },
        )


if __name__ == "__main__":
    unittest.main()
