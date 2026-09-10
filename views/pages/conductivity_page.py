from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QFileDialog,
    QMessageBox, QAbstractItemView
)

from views.pages.base_page import BaseCalculatorPage
from core.conductivity.calculator import compute_conductivity
from core.excel_export import export_to_excel


class ConductivityPage(BaseCalculatorPage):
    PAGE_TITLE = "导电性计算"
    PAGE_KEY = "conductivity"

    HEADERS = ["样品名称", "电阻 (Ω)", "长度 (cm)", "横截面积 (cm²)",
               "电阻率 (Ω·cm)", "电导率 (S/cm)"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.result_data = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        input_group = QGroupBox("输入参数")
        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.res_edit = QLineEdit()
        self.len_edit = QLineEdit()
        self.area_edit = QLineEdit()
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
        layout.addLayout(btn_row)

        self.table = QTableWidget(0, len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.btn_calc.clicked.connect(self._calculate)
        self.btn_clear.clicked.connect(self._clear)
        self.btn_export.clicked.connect(self._export)

    def _calculate(self):
        try:
            name = self.name_edit.text().strip() or "样品"
            R = float(self.res_edit.text())
            L = float(self.len_edit.text())
            A = float(self.area_edit.text())
        except ValueError:
            QMessageBox.warning(self, "提示", "请输入有效的数值！")
            return

        try:
            res = compute_conductivity(R, L, A)
        except ValueError as e:
            QMessageBox.warning(self, "提示", str(e))
            return

        row = self.table.rowCount()
        self.table.insertRow(row)
        values = [name, f"{R:.4f}", f"{L:.4f}", f"{A:.4f}",
                  f"{res['rho']:.6e}", f"{res['sigma']:.6e}"]
        for col, v in enumerate(values):
            self.table.setItem(row, col, QTableWidgetItem(v))

        self.result_data.append({
            "样品名称": name,
            "电阻 (Ω)": R,
            "长度 (cm)": L,
            "横截面积 (cm²)": A,
            "电阻率 (Ω·cm)": res['rho'],
            "电导率 (S/cm)": res['sigma'],
        })

        self.name_edit.clear()
        self.res_edit.clear()
        self.len_edit.clear()
        self.area_edit.clear()

    def _clear(self):
        self.table.setRowCount(0)
        self.result_data.clear()

    def _export(self):
        if not self.result_data:
            QMessageBox.warning(self, "提示", "当前没有可导出的数据！")
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "导出Excel", "", "Excel文件 (*.xlsx)")
        if file_path:
            if not file_path.lower().endswith(".xlsx"):
                file_path += ".xlsx"
            export_to_excel(self.result_data, file_path)
            QMessageBox.information(self, "成功", f"文件已导出至：{file_path}")