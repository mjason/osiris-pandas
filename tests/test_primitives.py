"""The backend is a real `.py`, so this imports it directly.

Before `py/embed` the body lived inside `core.osr`, and testing it meant running
`osr build` first and then globbing the relocated copy out of `dist/` by its
distribution hash. Being able to import the source is the point of the form.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "osiris_pandas" / "backend"))

import primitives as be  # noqa: E402


class PrimitivesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.values = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        self.keys = pd.Series(["a", "a", "b", "b", "b"])

    def test_rolling_reads_only_the_causal_window(self) -> None:
        self.assertEqual(list(be.rolling_mean(self.values, 3).dropna()), [2.0, 3.0, 4.0])
        self.assertEqual(list(be.rolling_sum(self.values, 2).dropna()), [3.0, 5.0, 7.0, 9.0])

    def test_shifting_refuses_to_read_the_future(self) -> None:
        self.assertEqual(list(be.shift(self.values, 1).dropna()), [1.0, 2.0, 3.0, 4.0])
        with self.assertRaises(ValueError):
            be.shift(self.values, -1)

    def test_reductions_leave_the_row_axis(self) -> None:
        self.assertEqual(be.series_sum(self.values), 15.0)
        self.assertEqual(be.series_quantile(self.values, 0.5), 3.0)
        self.assertEqual(be.series_count(self.values), 5)

    def test_cumulative_reads_every_earlier_row(self) -> None:
        self.assertEqual(list(be.cumulative_sum(self.values)), [1.0, 3.0, 6.0, 10.0, 15.0])
        self.assertEqual(list(be.expanding_mean(self.values)), [1.0, 1.5, 2.0, 2.5, 3.0])

    def test_grouped_transforms_stay_within_their_key(self) -> None:
        self.assertEqual(list(be.group_mean(self.values, self.keys)), [1.5, 1.5, 4.0, 4.0, 4.0])
        self.assertEqual(list(be.group_rank(self.values, self.keys)), [1.0, 2.0, 1.0, 2.0, 3.0])
        self.assertEqual(
            list(be.group_cumulative_sum(self.values, self.keys)), [1.0, 3.0, 3.0, 7.0, 12.0]
        )

    def test_back_fill_reads_later_rows(self) -> None:
        gapped = pd.Series([1.0, None, 3.0])
        self.assertEqual(list(be.back_fill(gapped)), [1.0, 3.0, 3.0])

    def test_row_wise_helpers_align_on_the_index(self) -> None:
        self.assertEqual(list(be.row_sum(self.values, self.values)), [2.0, 4.0, 6.0, 8.0, 10.0])
        self.assertEqual(list(be.where(self.values > 3, 1, 0)), [0, 0, 0, 1, 1])

    def test_invalid_windows_are_refused(self) -> None:
        for bad in (0, -1, True):
            with self.assertRaises(ValueError):
                be.rolling_mean(self.values, bad)


if __name__ == "__main__":
    unittest.main()
