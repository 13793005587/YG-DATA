"""表面能业务层测试：配对、批量计算、失败统计。"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.surface_energy.processor import (  # noqa: E402
    EXPORT_HEADERS,
    HEADERS,
    ID_KEY,
    build_sample_rows,
    calculate_surface_energies,
    empty_row,
    row_has_content,
    strip_ext,
    summarize,
    to_float,
)


class TestBuildSampleRows(unittest.TestCase):
    def test_pairs_by_filename_without_extension(self):
        water = [{"filename": "4.doc", "angle": 103.085}]
        diiodo = [{"filename": "4.docx", "angle": 66.5}]
        rows = build_sample_rows(water, diiodo)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["样品"], "4")
        self.assertEqual(rows[0]["水接触角"], 103.085)
        self.assertEqual(rows[0]["二碘甲烷接触角"], 66.5)
        # 未计算时后 4 列留空
        for key in ("极性分量", "色散分量", "估值方法", "表面能"):
            self.assertEqual(rows[0][key], "")

    def test_unpaired_files_become_separate_rows(self):
        rows = build_sample_rows(
            [{"filename": "a.doc", "angle": 90}],
            [{"filename": "b.doc", "angle": 60}],
        )
        self.assertEqual([r["样品"] for r in rows], ["a", "b"])
        self.assertEqual(rows[0]["二碘甲烷接触角"], "")
        self.assertEqual(rows[1]["水接触角"], "")

    def test_row_id_is_stable_source_key(self):
        """序号列保存来源标识，用户改「样品」不影响它。"""
        rows = build_sample_rows([{"filename": "S-12.doc", "angle": 90}], [])
        self.assertEqual(rows[0][ID_KEY], "S-12")

    def test_empty_input(self):
        self.assertEqual(build_sample_rows([], []), [])
        self.assertEqual(build_sample_rows(None, None), [])


class TestCalculateSurfaceEnergies(unittest.TestCase):
    def test_paired_rows_are_calculated(self):
        rows = build_sample_rows(
            [{"filename": "1.doc", "angle": 103.085}],
            [{"filename": "1.doc", "angle": 66.5}],
        )
        new_rows, stats = calculate_surface_energies(rows)
        self.assertEqual(stats["paired"], 1)
        self.assertEqual(stats["failed"], [])
        self.assertEqual(new_rows[0]["估值方法"], "OWRK")
        self.assertAlmostEqual(new_rows[0]["表面能"], 24.977, places=3)

    def test_manual_rows_can_be_calculated(self):
        row = empty_row(**{"样品": "手输", "水接触角": "90", "二碘甲烷接触角": "70"})
        new_rows, stats = calculate_surface_energies([row])
        self.assertEqual(stats["paired"], 1)
        self.assertEqual(new_rows[0]["样品"], "手输")

    def test_only_one_angle_counts_as_incomplete(self):
        rows = [
            empty_row(**{"样品": "w", "水接触角": 90}),
            empty_row(**{"样品": "d", "二碘甲烷接触角": 70}),
            empty_row(**{"样品": "none"}),
        ]
        _, stats = calculate_surface_energies(rows)
        self.assertEqual(stats["only_water"], 1)
        self.assertEqual(stats["only_diiodo"], 1)
        self.assertEqual(stats["empty"], 1)
        self.assertEqual(stats["paired"], 0)

    def test_infeasible_pair_is_reported_with_reason(self):
        """失败必须带样品名与原因，而不是静默留空。"""
        rows = [empty_row(**{"样品": "X1", "水接触角": 120, "二碘甲烷接触角": 30})]
        new_rows, stats = calculate_surface_energies(rows)
        self.assertEqual(stats["paired"], 0)
        self.assertEqual(len(stats["failed"]), 1)
        name, reason = stats["failed"][0]
        self.assertEqual(name, "X1")
        self.assertIn("无实数解", reason)
        self.assertEqual(new_rows[0]["表面能"], "")

    def test_failed_row_keeps_original_angles(self):
        rows = [empty_row(**{"样品": "X", "水接触角": 120, "二碘甲烷接触角": 30})]
        new_rows, _ = calculate_surface_energies(rows)
        self.assertEqual(new_rows[0]["水接触角"], 120)
        self.assertEqual(new_rows[0]["二碘甲烷接触角"], 30)

    def test_recalculate_clears_previous_results(self):
        """改数据后重算，旧结果不得残留。"""
        rows = [empty_row(**{"样品": "A", "水接触角": 90, "二碘甲烷接触角": 70})]
        rows, _ = calculate_surface_energies(rows)
        self.assertTrue(rows[0]["表面能"])

        rows[0]["水接触角"] = ""          # 清空一个角度
        rows, stats = calculate_surface_energies(rows)
        self.assertEqual(stats["paired"], 0)
        self.assertEqual(rows[0]["表面能"], "")
        self.assertEqual(rows[0]["估值方法"], "")

    def test_non_numeric_input_is_treated_as_missing(self):
        rows = [empty_row(**{"样品": "A", "水接触角": "abc", "二碘甲烷接触角": 70})]
        _, stats = calculate_surface_energies(rows)
        self.assertEqual(stats["paired"], 0)
        self.assertEqual(stats["only_diiodo"], 1)


class TestHelpers(unittest.TestCase):
    def test_to_float(self):
        cases = {
            "103.085": 103.085,
            90: 90.0,
            "1.2e-3": 1.2e-3,
            " 70 ": 70.0,
            "": None,
            None: None,
            "abc": None,
            "1.2.3": None,
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(to_float(value), expected)

    def test_strip_ext(self):
        self.assertEqual(strip_ext("4.doc"), "4")
        self.assertEqual(strip_ext("S-12.docx"), "S-12")
        self.assertEqual(strip_ext("no_ext"), "no_ext")

    def test_row_has_content_ignores_internal_columns(self):
        row = empty_row(**{ID_KEY: "42"})
        self.assertFalse(row_has_content(row))
        row["样品"] = "A"
        self.assertTrue(row_has_content(row))

    def test_export_headers_exclude_internal_column(self):
        self.assertNotIn(ID_KEY, EXPORT_HEADERS)
        self.assertEqual(len(EXPORT_HEADERS), len(HEADERS) - 1)

    def test_summarize_lists_failures(self):
        text = summarize(
            {
                "paired": 2,
                "only_water": 1,
                "only_diiodo": 0,
                "empty": 3,
                "failed": [("X1", "OWRK 方程无实数解")],
            }
        )
        self.assertIn("成功配对并计算：2", text)
        self.assertIn("仅有水滴角", text)
        self.assertIn("X1", text)
        self.assertIn("无实数解", text)


if __name__ == "__main__":
    unittest.main()
