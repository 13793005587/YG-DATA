"""导电性计算测试。"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.conductivity.calculator import (  # noqa: E402
    HEADERS,
    compute_conductivity,
    fmt,
)


class TestComputeConductivity(unittest.TestCase):
    def test_basic_formula(self):
        res = compute_conductivity(10.0, 2.0, 0.5)
        self.assertAlmostEqual(res["rho"], 2.5)
        self.assertAlmostEqual(res["sigma"], 0.4)

    def test_string_input_is_accepted(self):
        res = compute_conductivity("10", "2", "0.5")
        self.assertAlmostEqual(res["rho"], 2.5)

    def test_scientific_notation(self):
        res = compute_conductivity("1e3", "2.5", "0.04")
        self.assertAlmostEqual(res["rho"], 16.0)

    def test_non_positive_values_rejected(self):
        for args in [(0, 1, 1), (1, 0, 1), (1, 1, 0), (-1, 1, 1), (1, -1, 1)]:
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    compute_conductivity(*args)

    def test_non_finite_values_rejected(self):
        with self.assertRaises(ValueError):
            compute_conductivity(float("inf"), 1, 1)
        with self.assertRaises(ValueError):
            compute_conductivity(float("nan"), 1, 1)

    def test_invalid_text_rejected(self):
        with self.assertRaises(ValueError):
            compute_conductivity("abc", 1, 1)

    def test_headers_are_stable(self):
        self.assertEqual(len(HEADERS), 6)
        self.assertEqual(HEADERS[0], "样品名称")


class TestFmt(unittest.TestCase):
    def test_scientific_for_tiny_and_huge(self):
        self.assertIn("e", fmt(1.2e-7))
        self.assertIn("e", fmt(1.2e6))

    def test_fixed_for_normal(self):
        self.assertEqual(fmt(2.5), "2.5000")

    def test_empty_and_zero(self):
        self.assertEqual(fmt(None), "")
        self.assertEqual(fmt(0), "0")


if __name__ == "__main__":
    unittest.main()
