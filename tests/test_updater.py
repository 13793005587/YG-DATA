"""版本号解析测试。"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.updater import parse_version  # noqa: E402


class TestParseVersion(unittest.TestCase):
    def test_three_part(self):
        self.assertEqual(parse_version("2.1.0"), (2, 1, 0))

    def test_v_prefix(self):
        self.assertEqual(parse_version("v2.1.0"), (2, 1, 0))

    def test_only_one_prefix_is_stripped(self):
        """回归：lstrip('vV') 会剥掉任意多个 v，'vv2.1.0' 曾被当作 2.1.0。"""
        self.assertEqual(parse_version("v2.1.0"), (2, 1, 0))
        self.assertEqual(parse_version("vv2.1.0"), (0, 1, 0))

    def test_missing_parts_padded(self):
        self.assertEqual(parse_version("2.0"), (2, 0, 0))
        self.assertEqual(parse_version("3"), (3, 0, 0))

    def test_prerelease_suffix_is_ignored(self):
        self.assertEqual(parse_version("2.1.0-beta"), (2, 1, 0))
        self.assertEqual(parse_version("2.1.0-rc1"), (2, 1, 0))

    def test_extra_parts_truncated(self):
        self.assertEqual(parse_version("1.0.0.5"), (1, 0, 0))

    def test_double_digit_segments(self):
        self.assertEqual(parse_version("2.10.3"), (2, 10, 3))
        self.assertGreater(parse_version("2.10.0"), parse_version("2.9.9"))

    def test_invalid_input(self):
        self.assertEqual(parse_version(None), (0, 0, 0))
        self.assertEqual(parse_version(""), (0, 0, 0))
        self.assertEqual(parse_version("abc"), (0, 0, 0))

    def test_comparison_drives_update_prompt(self):
        self.assertGreater(parse_version("2.0.1"), parse_version("2.0.0"))
        self.assertEqual(parse_version("2.0.0"), parse_version("v2.0.0"))


if __name__ == "__main__":
    unittest.main()
