"""Word 解析辅助函数测试（不需要安装 Office）。"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import doc_utils  # noqa: E402
from core.doc_utils import ComUnavailableError, parse_doc_contact_angle, parse_number  # noqa: E402


class TestParseNumber(unittest.TestCase):
    def test_plain_numbers(self):
        self.assertEqual(parse_number("103.085"), 103.085)
        self.assertEqual(parse_number("-3.5"), -3.5)
        self.assertEqual(parse_number("1.2e-3"), 1.2e-3)

    def test_numbers_with_units_and_noise(self):
        """Word 单元格文本带 \r\x07 控制符，必须先清洗。"""
        self.assertEqual(parse_number("103.085\x07\r"), 103.085)
        self.assertEqual(parse_number("77.336°"), 77.336)
        self.assertEqual(parse_number("平均角度：77.336"), 77.336)

    def test_labels_are_not_parsed_as_numbers(self):
        self.assertIsNone(parse_number("左接触角"))
        self.assertIsNone(parse_number(""))
        self.assertIsNone(parse_number(None))


class TestComAvailability(unittest.TestCase):
    def test_module_imports_without_pywin32(self):
        """回归：以前 pywin32 缺失时连界面都起不来。"""
        self.assertTrue(hasattr(doc_utils, "parse_doc_contact_angle"))
        self.assertIsNone(doc_utils.win32com)  # 惰性导入，模块级未加载

    def test_empty_file_list_short_circuits(self):
        self.assertEqual(parse_doc_contact_angle([]), ([], []))

    def test_missing_pywin32_raises_helpful_error(self):
        original = doc_utils.win32com
        doc_utils.win32com = None
        try:
            try:
                import win32com.client  # noqa: F401

                has_pywin32 = True
            except ImportError:
                has_pywin32 = False

            if has_pywin32:
                self.skipTest("本机已安装 pywin32，跳过缺失场景")
            with self.assertRaises(ComUnavailableError) as ctx:
                parse_doc_contact_angle(["x.doc"])
            self.assertIn("pywin32", str(ctx.exception))
        finally:
            doc_utils.win32com = original


class TestHeaderHeuristics(unittest.TestCase):
    def test_priority_ordering(self):
        self.assertLess(
            doc_utils._priority_of("平均角度", "平均角度"),
            doc_utils._priority_of("平均角度(°)", "平均角度"),
        )

    def test_header_detection(self):
        self.assertTrue(doc_utils._is_header("平均接触角(°)"))
        self.assertFalse(doc_utils._is_header("平均接触角"))

    def test_cell_clean_removes_control_chars(self):
        self.assertEqual(doc_utils._clean("103.085\x07\r\n"), "103.085")


if __name__ == "__main__":
    unittest.main()
