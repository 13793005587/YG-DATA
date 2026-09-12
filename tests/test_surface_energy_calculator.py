"""OWRK 计算器测试：数值正确性 + 数学域失败的显式报错。"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.surface_energy.calculator import (  # noqa: E402
    OWRKError,
    owrk_from_template,
)


class TestOwrkCalculation(unittest.TestCase):
    def test_known_pair_matches_expected_values(self):
        """水 103.085° / 二碘甲烷 66.5° 的既有结果不得回归。"""
        res = owrk_from_template(103.085, 66.5)
        self.assertAlmostEqual(res["gamma_total"], 24.9774, places=3)
        self.assertAlmostEqual(res["gamma_p"], 0.5021, places=3)
        self.assertAlmostEqual(res["gamma_d"], 24.4753, places=3)

    def test_total_is_sum_of_components(self):
        res = owrk_from_template(90, 70)
        self.assertAlmostEqual(
            res["gamma_total"], res["gamma_d"] + res["gamma_p"], places=9
        )

    def test_components_are_non_negative(self):
        for water, diiodo in [(60, 40), (75, 55), (95, 45)]:
            res = owrk_from_template(water, diiodo)
            self.assertGreaterEqual(res["gamma_d"], 0.0)
            self.assertGreaterEqual(res["gamma_p"], 0.0)

    def test_negative_root_raises_explicit_error(self):
        """水角偏大 + 二碘甲烷角偏小 → 方程无实数解，必须显式报错。"""
        with self.assertRaises(OWRKError) as ctx:
            owrk_from_template(120, 30)
        self.assertIn("无实数解", str(ctx.exception))
        self.assertIn("120", str(ctx.exception))

    def test_negative_root_is_not_silently_zeroed(self):
        """修复前该组合会被静默算成 0 或抛 ValueError，现在必须是 OWRKError。"""
        with self.assertRaises(OWRKError):
            owrk_from_template(98, 22)

    def test_angle_out_of_range_rejected(self):
        for bad in [(0, 70), (180, 70), (90, 0), (90, 180), (-5, 70), (90, 200)]:
            with self.subTest(bad=bad):
                with self.assertRaises(OWRKError):
                    owrk_from_template(*bad)

    def test_non_numeric_angle_rejected(self):
        for bad in [("abc", 70), (None, 70), (90, "")]:
            with self.subTest(bad=bad):
                with self.assertRaises(OWRKError):
                    owrk_from_template(*bad)

    def test_error_message_is_user_facing_chinese(self):
        with self.assertRaises(OWRKError) as ctx:
            owrk_from_template(200, 70)
        self.assertIn("水接触角", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
