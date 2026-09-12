"""表面能计算页面。

业务规则全部位于 ``core.surface_energy``；本模块只负责：
  * 文件选择与后台提取（含线程生命周期管理）
  * 表格渲染（数据源为 SampleTableModel）
  * 结果与失败信息的展示
"""

import logging
import os

from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QProgressDialog,
    QPushButton,
    QVBoxLayout,
)

from core.doc_utils import parse_doc_contact_angle
from core.surface_energy.processor import (
    EXPORT_HEADERS,
    FLOAT_KEYS,
    HEADERS,
    build_sample_rows,
    calculate_surface_energies,
    row_has_content,
    summarize,
)
from views.dialogs.compat import create_message_box, qmessagebox
from views.dialogs.extraction_failures import ExtractionFailureDialog
from views.exporter import export_rows_with_dialog
from views.pages.base_page import BaseCalculatorPage
from views.widgets.results_table import ResultsTableWidget

logger = logging.getLogger(__name__)

# 图标/按钮常量取真实实现，不随测试替身变化
_MessageBox = qmessagebox()


class _ExtractionWorker(QThread):
    """后台解析 Word 报告。is_water 随信号回传，不再回读 self.worker。"""

    result_ready = Signal(list, bool)   # results, is_water
    error_occurred = Signal(str)

    def __init__(self, files, is_water, parent=None):
        super().__init__(parent)
        self.files = list(files)
        self.is_water = is_water

    def run(self):
        try:
            results, failures = parse_doc_contact_angle(self.files)
            self.result_ready.emit([results, failures], self.is_water)
        except Exception as e:  # noqa: BLE001 - 必须回报到 UI，不能静默
            logger.exception("提取 Word 数据失败")
            self.error_occurred.emit(str(e))


class SurfaceEnergyPage(BaseCalculatorPage):
    PAGE_TITLE = "表面能计算"
    PAGE_KEY = "surface_energy"

    HEADERS = HEADERS

    def __init__(self, parent=None):
        super().__init__(parent)
        self.water_data = []
        self.diiodo_data = []
        self.worker = None
        self.progress_dialog = None
        self._build_ui()

    # ==================== UI ====================
    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(4)

        self.results_table = ResultsTableWidget(
            on_rows_removed=self._on_rows_removed,
            on_clear_requested=self._clear_all,
            parent=self,
        )
        self.model = self.results_table.model
        main_layout.addWidget(self.results_table)
        main_layout.addStretch(1)

        # ---------- 底部按钮区 ----------
        btns = QGridLayout()
        self.btn_h2o = QPushButton("导入水滴角")
        self.btn_ch2i2 = QPushButton("导入二碘甲烷接触角")
        self.btn_calc = QPushButton("计算表面能")
        self.btn_clear = QPushButton("清空数据")
        self.btn_export = QPushButton("导出.xlsx文件")

        self.btn_h2o.setToolTip("选择水滴角文件；\n对应的二碘甲烷文件名要与水滴角文件名一致")
        self.btn_ch2i2.setToolTip("选择二碘甲烷文件；\n对应的水滴角文件名要与二碘甲烷文件名一致")

        btns.addWidget(self.btn_h2o, 0, 0)
        btns.addWidget(self.btn_ch2i2, 0, 1)
        btns.addWidget(self.btn_calc, 1, 0)
        btns.addWidget(self.btn_clear, 1, 1)
        btns.addWidget(self.btn_export, 2, 0, 1, 2)

        main_layout.addLayout(btns)

        self.btn_h2o.clicked.connect(lambda: self._import(is_water=True))
        self.btn_ch2i2.clicked.connect(lambda: self._import(is_water=False))
        self.btn_calc.clicked.connect(self._calculate)
        self.btn_clear.clicked.connect(self._clear_all)
        self.btn_export.clicked.connect(self._export)

    # ==================== 导入 ====================
    def _import(self, is_water):
        title = "选择水滴角文件" if is_water else "选择二碘甲烷文件"
        files, _ = QFileDialog.getOpenFileNames(
            self, title, "", "Word文档 (*.doc *.docx)"
        )
        if files:
            self._start_extraction(files, is_water)

    def _set_buttons_enabled(self, enabled):
        for button in (self.btn_h2o, self.btn_ch2i2, self.btn_calc,
                       self.btn_clear, self.btn_export,
                       self.results_table.btn_add_row):
            button.setEnabled(enabled)

    def _start_extraction(self, files, is_water):
        if self.worker is not None and self.worker.isRunning():
            qmessagebox().information(self, "提示", "正在导入上一个文件列表，请稍候…")
            return

        self._set_buttons_enabled(False)
        self.progress_dialog = QProgressDialog("正在提取数据，请稍候...", None, 0, 0, self)
        self.progress_dialog.setWindowTitle("提示")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setCancelButton(None)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.show()

        self.worker = _ExtractionWorker(files, is_water, self)
        self.worker.result_ready.connect(self._on_extract_done)
        self.worker.error_occurred.connect(self._on_extract_error)
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.start()

    def _on_worker_finished(self):
        worker, self.worker = self.worker, None
        if worker is not None:
            worker.deleteLater()

    def _on_extract_done(self, payload, is_water):
        results, failures = payload
        self._close_progress()
        self._set_buttons_enabled(True)

        if not results:
            qmessagebox().warning(
                self, "提示",
                "未在文件中提取到有效接触角！\n请确认文件格式是否正确。",
            )
            if failures:
                ExtractionFailureDialog(failures, self).exec()
            return

        if is_water:
            self.water_data = results
        else:
            self.diiodo_data = results

        imported_rows = build_sample_rows(self.water_data, self.diiodo_data)

        # 保留下用户手工录入、尚未参与计算的行
        manual_rows = [row for row in self.model.rows() if _is_manual_row(row)]

        self.model.set_rows(imported_rows + manual_rows)

        message = f"已提取 {len(results)} 个文件的数据！"
        if failures:
            message += f"\n其中 {len(failures)} 个文件未能提取到角度。"
        qmessagebox().information(self, "成功", message)

        if failures:
            ExtractionFailureDialog(failures, self).exec()

    def _on_extract_error(self, message):
        self._close_progress()
        self._set_buttons_enabled(True)
        qmessagebox().critical(self, "错误", f"提取过程中发生错误：\n{message}")

    def _close_progress(self):
        if self.progress_dialog is not None:
            self.progress_dialog.close()
            self.progress_dialog = None

    def shutdown_worker(self, timeout_ms=5000):
        """窗口关闭时等待后台线程，避免打断正在进行的 Word COM 调用。"""
        worker = self.worker
        if worker is None or not worker.isRunning():
            return
        logger.info("等待后台提取线程结束…")
        try:
            worker.result_ready.disconnect()
            worker.error_occurred.disconnect()
        except (RuntimeError, TypeError):
            pass
        worker.requestInterruption()
        if not worker.wait(timeout_ms):
            logger.warning("后台提取线程未在 %d ms 内结束", timeout_ms)

    # ==================== 行删除 ====================
    def _on_rows_removed(self, removed_rows):
        """按行内稳定的「序号」清理原始数据，避免同名样品被误删。"""
        ids = {str(r.get("序号", "")).strip() for r in removed_rows if r}
        ids.discard("")
        if not ids:
            return

        self.water_data = [
            w for w in self.water_data
            if _strip_ext(w.get("filename", "")) not in ids
        ]
        self.diiodo_data = [
            d for d in self.diiodo_data
            if _strip_ext(d.get("filename", "")) not in ids
        ]

    # ==================== 计算 ====================
    def _calculate(self):
        rows = self.model.rows()
        if not rows:
            qmessagebox().warning(self, "提示", "请先导入数据或手动添加行！")
            return

        new_rows, stats = calculate_surface_energies(rows)
        self.model.set_rows(new_rows)

        qmessagebox().information(self, "完成", summarize(stats))

        if stats["failed"]:
            details = "\n".join(f"· {name}\n    {reason}" for name, reason in stats["failed"])
            box = create_message_box(
                self,
                icon=_MessageBox.Warning,
                title="部分样品计算失败",
                text=(
                    f"有 {len(stats['failed'])} 个样品无法用 OWRK 模型求解，"
                    "对应行已留空（可展开查看明细）："
                ),
            )
            box.setDetailedText(details)
            box.exec()

    # ==================== 清空 / 导出 ====================
    def _clear_all(self):
        if not self.model.rowCount() and not self.water_data and not self.diiodo_data:
            return
        ret = qmessagebox().question(
            self, "确认清空",
            "确定要清空所有已导入的数据和计算结果吗？",
            _MessageBox.Yes | _MessageBox.No,
            _MessageBox.No,
        )
        if ret != _MessageBox.Yes:
            return

        self.water_data = []
        self.diiodo_data = []
        self.model.set_rows([])

    def _export(self):
        rows = [r for r in self.model.rows() if row_has_content(r)]
        if self.model.rowCount() and not rows:
            qmessagebox().warning(self, "提示", "所有行都是空的，无需导出。")
            return
        export_rows_with_dialog(self, rows, headers=EXPORT_HEADERS)


def _strip_ext(filename):
    return os.path.splitext(str(filename))[0]


def _is_manual_row(row):
    """判断是否为用户手工录入、尚未参与计算的行。

    导入生成的行一定带「序号」（来源文件名），据此与手工行区分——
    否则每次重新导入都会把上一次的导入行当成手工行再插一遍，导致重复。
    """
    if str(row.get("序号", "")).strip():
        return False
    if str(row.get("估值方法", "")).strip() or str(row.get("表面能", "")).strip():
        return False
    if str(row.get("样品", "")).strip():
        return True
    return any(str(row.get(key, "")).strip() for key in FLOAT_KEYS)
