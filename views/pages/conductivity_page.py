"""导电性计算页面。"""

import logging

from PySide6.QtWidgets import (
    QAbstractItemView,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from core.conductivity.calculator import (
    DISPLAY_PRECISION,
    HEADERS,
    INPUT_PRECISION,
    compute_conductivity,
    fmt,
)
from views.dialogs.compat import qmessagebox
from views.exporter import export_rows_with_dialog
from views.models.sample_table_model import make_number_validator
from views.pages.base_page import BaseCalculatorPage

logger = logging.getLogger(__name__)

# 按钮常量取真实实现，不随测试替身变化
_MessageBox = qmessagebox()


class ConductivityPage(BaseCalculatorPage):
    PAGE_TITLE = "导电性计算"
    PAGE_KEY = "conductivity"

    HEADERS = HEADERS

    def __init__(self, parent=None):
        super().__init__(parent)
        self.result_data = []
        self._build_ui()

    # ==================== UI ====================
    def _build_ui(self):
        layout = QVBoxLayout(self)

        input_group = QGroupBox("输入参数")
        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("留空时默认记为「样品」")
        self.res_edit = self._make_number_edit("例如 1250")
        self.len_edit = self._make_number_edit("例如 2.5")
        self.area_edit = self._make_number_edit("例如 0.04")
        form.addRow("样品名称：", self.name_edit)
        form.addRow("电阻 R (Ω)：", self.res_edit)
        form.addRow("长度 L (cm)：", self.len_edit)
        form.addRow("横截面积 A (cm²)：", self.area_edit)
        input_group.setLayout(form)
        layout.addWidget(input_group)

        btn_row = QHBoxLayout()
        self.btn_calc = QPushButton("计算")
        self.btn_clear = QPushButton("清空")
        self.btn_export = QPushButton("导出.xlsx文件")
        btn_row.addWidget(self.btn_calc)
        btn_row.addWidget(self.btn_clear)
        btn_row.addWidget(self.btn_export)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        self.table = QTableWidget(0, len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        note = QLabel(
            f"说明：表格中按 {INPUT_PRECISION} 位小数 / {DISPLAY_PRECISION} 位有效数字显示，"
            "导出的 Excel 保存完整精度数值。"
        )
        note.setStyleSheet("color: #6b7c8f; font-size: 9pt;")
        layout.addWidget(note)

        self.btn_calc.clicked.connect(self._calculate)
        self.btn_clear.clicked.connect(self._clear)
        self.btn_export.clicked.connect(self._export)

    def _make_number_edit(self, placeholder=""):
        """带数字校验器的输入框：支持 1e-5 这类科学计数法。"""
        edit = QLineEdit()
        edit.setValidator(make_number_validator(edit))
        if placeholder:
            edit.setPlaceholderText(placeholder)
        return edit

    # ==================== 操作 ====================
    def _calculate(self):
        name = self.name_edit.text().strip() or "样品"
        texts = (self.res_edit.text(), self.len_edit.text(), self.area_edit.text())

        if not all(t.strip() for t in texts):
            qmessagebox().warning(self, "提示", "请先填写电阻、长度与横截面积！")
            return

        try:
            values = [float(t) for t in texts]
        except ValueError:
            qmessagebox().warning(self, "提示", "请输入有效的数值！")
            return

        try:
            res = compute_conductivity(*values)
        except ValueError as e:
            qmessagebox().warning(self, "提示", str(e))
            return

        resistance, length, area = values
        row_index = self.table.rowCount()
        self.table.insertRow(row_index)
        display_values = [
            name, fmt(resistance), fmt(length), fmt(area),
            fmt(res['rho']), fmt(res['sigma']),
        ]
        for column, text in enumerate(display_values):
            self.table.setItem(row_index, column, QTableWidgetItem(text))

        # 导出保存完整精度，避免与界面显示不一致造成误解
        self.result_data.append({
            "样品名称": name,
            "电阻 (Ω)": resistance,
            "长度 (cm)": length,
            "横截面积 (cm²)": area,
            "电阻率 (Ω·cm)": res['rho'],
            "电导率 (S/cm)": res['sigma'],
        })

        for edit in (self.name_edit, self.res_edit, self.len_edit, self.area_edit):
            edit.clear()
        self.res_edit.setFocus()

    def _clear(self):
        if not self.result_data:
            return
        ret = qmessagebox().question(
            self, "确认清空", "确定要清空所有已计算的记录吗？",
            _MessageBox.Yes | _MessageBox.No, _MessageBox.No,
        )
        if ret != _MessageBox.Yes:
            return
        self.table.setRowCount(0)
        self.result_data.clear()

    def _export(self):
        export_rows_with_dialog(self, self.result_data, headers=self.HEADERS)
