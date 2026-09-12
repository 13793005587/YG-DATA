"""界面层冒烟测试（offscreen 模式，不需要真实桌面）。

覆盖本次重构的核心回归点：
  * SampleTableModel 的编辑权限与数据同步（原先的双份状态）
  * 主窗口 / 页面 / 数据模型的整体装配
  * 手册外置文件能被正确读取
"""

import sys
import unittest
import unittest.mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests import requires_qt  # noqa: E402


class FakeMessageBox:
    """替代真实 QMessageBox，避免测试阻塞在模态对话框上。

    同时记录调用，便于断言"是否给用户提示过"。
    """

    def __init__(self, answer=None):
        self.answer = answer
        self.calls = []

    def _record(self, kind, args, kwargs):
        self.calls.append((kind, args, kwargs))

    def information(self, *args, **kwargs):
        self._record("information", args, kwargs)
        return self.answer

    def warning(self, *args, **kwargs):
        self._record("warning", args, kwargs)
        return self.answer

    def critical(self, *args, **kwargs):
        self._record("critical", args, kwargs)
        return self.answer

    def question(self, *args, **kwargs):
        self._record("question", args, kwargs)
        return self.answer

    def about(self, *args, **kwargs):
        self._record("about", args, kwargs)
        return self.answer

    def kinds(self):
        return [kind for kind, _, _ in self.calls]


if requires_qt:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    _qt_app = None

    def app_instance():
        """进程内唯一的 QApplication（unittest 可能多次调用 setUpClass）。"""
        global _qt_app
        _qt_app = QApplication.instance() or _qt_app or QApplication([])
        return _qt_app

    class QtTestCase(unittest.TestCase):
        @classmethod
        def setUpClass(cls):
            cls.app = app_instance()

else:  # pragma: no cover - 无 PySide6 时占位，跳过所有用例
    QtTestCase = unittest.TestCase


class TestSampleTableModel(QtTestCase):
    def setUp(self):
        from core.surface_energy.processor import HEADERS, empty_row
        from views.models.sample_table_model import SampleTableModel

        self.HEADERS = HEADERS
        self.empty_row = empty_row
        self.model = SampleTableModel()

    def _index(self, row, key):
        return self.model.index(row, self.HEADERS.index(key))

    def test_starts_empty(self):
        self.assertEqual(self.model.rowCount(), 0)
        self.assertEqual(self.model.columnCount(), len(self.HEADERS))

    def test_set_rows(self):
        self.model.set_rows([self.empty_row(**{"样品": "A"})])
        self.assertEqual(self.model.rowCount(), 1)
        self.assertEqual(self.model.data(self._index(0, "样品")), "A")

    def test_rows_returns_copies(self):
        self.model.set_rows([self.empty_row(**{"样品": "A"})])
        snapshot = self.model.rows()
        snapshot[0]["样品"] = "changed"
        self.assertEqual(self.model.data(self._index(0, "样品")), "A")

    def test_editable_columns(self):
        self.model.set_rows([self.empty_row()])
        for key in ("样品", "水接触角", "二碘甲烷接触角"):
            self.assertTrue(
                self.model.flags(self._index(0, key)) & Qt.ItemIsEditable, key
            )

    def test_readonly_columns(self):
        self.model.set_rows([self.empty_row()])
        for key in ("序号", "极性分量", "色散分量", "估值方法", "表面能"):
            self.assertFalse(
                self.model.flags(self._index(0, key)) & Qt.ItemIsEditable, key
            )

    def test_set_data_stores_float_for_angle_columns(self):
        self.model.set_rows([self.empty_row()])
        self.assertTrue(
            self.model.setData(self._index(0, "水接触角"), "103.085", Qt.EditRole)
        )
        self.assertEqual(self.model.rows()[0]["水接触角"], 103.085)

    def test_set_data_rejects_invalid_float(self):
        self.model.set_rows([self.empty_row(**{"样品": "A"})])
        changed = self.model.setData(self._index(0, "水接触角"), "1.2.3", Qt.EditRole)
        self.assertFalse(changed)
        self.assertEqual(self.model.rows()[0]["水接触角"], "")

    def test_set_data_allows_clearing(self):
        self.model.set_rows([self.empty_row(**{"水接触角": 90})])
        self.assertTrue(self.model.setData(self._index(0, "水接触角"), "", Qt.EditRole))
        self.assertEqual(self.model.rows()[0]["水接触角"], "")

    def test_sample_column_accepts_arbitrary_text(self):
        self.model.set_rows([self.empty_row()])
        self.model.setData(self._index(0, "样品"), "样品①-A/2", Qt.EditRole)
        self.assertEqual(self.model.rows()[0]["样品"], "样品①-A/2")

    def test_readonly_column_cannot_be_written(self):
        self.model.set_rows([self.empty_row()])
        self.assertFalse(self.model.setData(self._index(0, "表面能"), 99, Qt.EditRole))

    def test_clear_cells_only_touches_editable_columns(self):
        self.model.set_rows([self.empty_row(**{"样品": "A", "水接触角": 90})])
        self.model.clear_cells(
            [
                self._index(0, "样品"),
                self._index(0, "水接触角"),
                self._index(0, "表面能"),
            ]
        )
        row = self.model.rows()[0]
        self.assertEqual(row["样品"], "")
        self.assertEqual(row["水接触角"], "")

    def test_insert_and_remove_rows(self):
        self.model.set_rows([self.empty_row(**{"样品": "A"})])
        self.model.insert_empty_rows(0, 2)
        self.assertEqual(self.model.rowCount(), 3)
        self.assertEqual(self.model.rows()[2]["样品"], "A")   # 原有行被下移
        self.assertEqual(self.model.rows()[0]["样品"], "")
        self.assertEqual(self.model.rows()[1]["样品"], "")

        self.model.remove_rows([0, 1])
        self.assertEqual(self.model.rowCount(), 1)
        self.assertEqual(self.model.rows()[0]["样品"], "A")

    def test_remove_rows_tolerates_out_of_range(self):
        self.model.set_rows([self.empty_row()])
        self.model.remove_rows([0, 5])
        self.assertEqual(self.model.rowCount(), 0)

    def test_row_at_returns_copy(self):
        self.model.set_rows([self.empty_row(**{"样品": "A"})])
        row = self.model.row_at(0)
        row["样品"] = "changed"
        self.assertEqual(self.model.rows()[0]["样品"], "A")
        self.assertIsNone(self.model.row_at(3))

    def test_header_data(self):
        self.assertEqual(
            self.model.headerData(0, Qt.Horizontal, Qt.DisplayRole), self.HEADERS[0]
        )
        self.assertEqual(self.model.headerData(0, Qt.Vertical, Qt.DisplayRole), 1)


class TestMainWindowSmoke(QtTestCase):
    def setUp(self):
        from PySide6.QtWidgets import QMessageBox

        from views.dialogs import compat
        from views.main_window import MainWindow

        self.QMessageBox = QMessageBox
        self.compat = compat
        self.fake = FakeMessageBox(QMessageBox.Yes)
        compat.set_messagebox(self.fake)
        # 提取失败明细对话框也是模态的
        self._dialog_patch = unittest.mock.patch(
            "views.pages.surface_energy_page.ExtractionFailureDialog"
        )
        self.dialog_mock = self._dialog_patch.start()

        self.window = MainWindow()

    def tearDown(self):
        self._dialog_patch.stop()
        self.compat.set_messagebox(None)
        self.window.close()
        self.window.deleteLater()
        app_instance().processEvents()

    def test_pages_are_registered(self):
        from views.pages.conductivity_page import ConductivityPage
        from views.pages.home_page import HomePage
        from views.pages.surface_energy_page import SurfaceEnergyPage

        self.assertIn(HomePage.PAGE_KEY, self.window.pages)
        self.assertIn(SurfaceEnergyPage.PAGE_KEY, self.window.pages)
        self.assertIn(ConductivityPage.PAGE_KEY, self.window.pages)

    def test_all_pages_switch_without_error(self):
        for key in self.window.pages:
            self.window._activate_page(key)
            self.assertIs(self.window.stack.currentWidget(), self.window.pages[key])

    def test_home_page_has_cards_for_every_function(self):
        from views.main_window import _PAGE_REGISTRY

        self.assertEqual(
            self.window.home_page.cards_layout.count(), len(_PAGE_REGISTRY)
        )

    def test_window_title_uses_config(self):
        from core import config

        self.assertEqual(self.window.windowTitle(), config.APP_NAME)

    def test_updater_instance_is_reused(self):
        first = self.window.updater
        self.assertIsNotNone(first)
        self.window._check_update(silent=True)
        self.assertIs(self.window.updater, first)

    def test_activate_unknown_page_is_noop(self):
        before = self.window.stack.currentWidget()
        self.window._activate_page("does-not-exist")
        self.assertIs(self.window.stack.currentWidget(), before)

    def test_manual_dialog_loads_external_html(self):
        from views.main_window import ManualDialog

        html = ManualDialog._load_html()
        self.assertIn("使用手册", html)
        self.assertIn("OWRK", html)
        self.assertIn("计算失败", html)      # 本次新增章节

    def test_manual_dialog_falls_back_when_file_missing(self):
        from views import main_window as mw

        original = mw.resource_path
        mw.resource_path = lambda *parts: str(Path("Z:/definitely/missing.html"))
        try:
            html = mw.ManualDialog._load_html()
        finally:
            mw.resource_path = original
        self.assertIn("使用手册缺失", html)

    def test_surface_energy_page_model_is_wired(self):
        page = self.window.pages["surface_energy"]
        page.model.append_empty_row()
        self.assertEqual(page.model.rowCount(), 1)
        self.assertIs(page.results_table.model, page.model)

    def test_surface_energy_page_keeps_manual_rows_on_import(self):
        """回归：导入后手工录入的行不能被丢弃。"""
        from core.surface_energy.processor import empty_row

        page = self.window.pages["surface_energy"]
        page.model.set_rows(
            [empty_row(**{"样品": "手工样品", "水接触角": "90", "二碘甲烷接触角": "70"})]
        )
        page._on_extract_done(
            [[{"filename": "1.doc", "angle": 103.085}], []], True
        )
        names = [r["样品"] for r in page.model.rows()]
        self.assertIn("手工样品", names)
        self.assertIn("1", names)

    def test_reimport_does_not_duplicate_rows(self):
        """回归：第二次导入曾把上一次的导入行当成手工行再插一遍。

        对应真实操作「先导入水滴角，再导入二碘甲烷」。
        """
        page = self.window.pages["surface_energy"]
        page._on_extract_done([[{"filename": "S1.doc", "angle": 103.085}], []], True)
        self.assertEqual(page.model.rowCount(), 1)

        page._on_extract_done([[{"filename": "S1.doc", "angle": 66.5}], []], False)
        rows = page.model.rows()
        self.assertEqual(len(rows), 1, f"rows={rows}")
        self.assertEqual(rows[0]["水接触角"], 103.085)
        self.assertEqual(rows[0]["二碘甲烷接触角"], 66.5)

    def test_reimport_pairs_rows_and_keeps_manual_rows(self):
        from core.surface_energy.processor import empty_row

        page = self.window.pages["surface_energy"]
        page.model.set_rows([empty_row(**{"样品": "手工", "水接触角": "80"})])
        page._on_extract_done([[{"filename": "A.doc", "angle": 90.0}], []], True)
        page._on_extract_done([[{"filename": "A.doc", "angle": 60.0}], []], False)

        names = [r["样品"] for r in page.model.rows()]
        self.assertEqual(names.count("A"), 1, f"names={names}")
        self.assertEqual(names.count("手工"), 1, f"names={names}")

    def test_conductivity_page_validates_input(self):
        page = self.window.pages["conductivity"]
        # 空输入 / 非数值都不应写入结果
        page.res_edit.setText("")
        page._calculate()
        self.assertEqual(page.result_data, [])

    def test_conductivity_page_records_result(self):
        page = self.window.pages["conductivity"]
        page.name_edit.setText("A")
        page.res_edit.setText("10")
        page.len_edit.setText("2")
        page.area_edit.setText("0.5")
        page._calculate()
        self.assertEqual(len(page.result_data), 1)
        self.assertAlmostEqual(page.result_data[0]["电阻率 (Ω·cm)"], 2.5)
        self.assertEqual(page.table.rowCount(), 1)

    def test_extraction_failures_are_surfaced_to_user(self):
        """回归：以前失败文件只 print 到不存在的控制台。"""
        page = self.window.pages["surface_energy"]
        page._on_extract_done(
            [
                [{"filename": "ok.doc", "angle": 90.0}],
                [{"filename": "bad.doc", "reason": "未找到平均角度"}],
            ],
            True,
        )
        self.dialog_mock.assert_called_once()
        args = self.dialog_mock.call_args[0][0]
        self.assertEqual(args[0]["filename"], "bad.doc")

    def test_all_files_failed_shows_warning_and_details(self):
        page = self.window.pages["surface_energy"]
        page._on_extract_done(
            [[], [{"filename": "bad.doc", "reason": "无法打开"}]], True
        )
        self.assertIn("warning", self.fake.kinds())
        self.dialog_mock.assert_called_once()

    def test_calculation_reports_failures_without_blocking_success(self):
        """配对成功的行照常计算，失败行给出可展开的明细。"""
        from core.surface_energy.processor import empty_row

        page = self.window.pages["surface_energy"]
        page.model.set_rows([
            empty_row(**{"样品": "好样品", "水接触角": 103.085, "二碘甲烷接触角": 66.5}),
            empty_row(**{"样品": "坏样品", "水接触角": 120, "二碘甲烷接触角": 30}),
        ])
        page._calculate()

        rows = page.model.rows()
        self.assertEqual(rows[0]["表面能"], 24.977)
        self.assertEqual(rows[1]["表面能"], "")
        self.assertIn("information", self.fake.kinds())


class TestLoggingSetup(QtTestCase):
    def test_setup_logging_is_idempotent(self):
        from core import logging_setup

        first = logging_setup.setup_logging()
        second = logging_setup.setup_logging()
        self.assertEqual(first, second)

    def test_excepthook_is_installed(self):
        import sys as _sys

        from core import logging_setup

        logging_setup.install_excepthook()
        self.assertIs(_sys.excepthook, logging_setup._on_uncaught_exception)

    def test_log_directory_is_writable(self):
        from core.paths import log_dir, user_data_dir

        self.assertTrue(log_dir().is_dir())
        self.assertTrue(user_data_dir().is_dir())

    def test_uncaught_exception_is_logged_and_surfaced(self):
        """回归：兜底处理器曾用错误的 QMetaObject.invokeMethod 签名。

        替换掉真正弹窗的槽函数（真实 QMessageBox 在 offscreen 下会永久阻塞），
        验证「异常钩子 → 排队信号 → 主线程槽」这条链路本身是通的。
        """
        from core import logging_setup

        seen = []
        original_handler = logging_setup._show_error_dialog
        logging_setup._show_error_dialog = lambda title, msg: seen.append((title, msg))
        logging_setup.unregister_bridge()     # 用替换后的槽重建桥接对象
        try:
            try:
                raise ValueError("boom")
            except ValueError:
                logging_setup._on_uncaught_exception(*sys.exc_info())

            app_instance().processEvents()
        finally:
            logging_setup._show_error_dialog = original_handler
            logging_setup.unregister_bridge()

        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0][0], "程序错误")
        self.assertIn("boom", seen[0][1])

    def test_excepthook_without_qapplication_does_not_raise(self):
        from core import logging_setup

        logging_setup._on_uncaught_exception(ValueError, ValueError("x"), None)


if __name__ == "__main__":
    unittest.main()
