import sys
import os
from PySide6.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QProgressDialog
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon
from ui.main_window_ui import Ui_MainWindow
from core.data_processor import parse_doc_contact_angle, calculate_surface_energies, export_to_excel


# ---------- 资源路径辅助函数（用于打包后访问嵌入资源） ----------
def resource_path(relative_path):
    """获取资源文件的绝对路径，兼容开发环境和 PyInstaller 打包后的环境"""
    try:
        # PyInstaller 会将资源解压到临时目录，并将路径存储在 _MEIPASS 中
        base_path = sys._MEIPASS
    except AttributeError:
        # 开发环境，使用当前文件所在目录
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class ExtractionWorker(QThread):
    result_ready = Signal(list)
    error_occurred = Signal(str)

    def __init__(self, files, is_water):
        super().__init__()
        self.files = files
        self.is_water = is_water

    def run(self):
        try:
            data = parse_doc_contact_angle(self.files)
            self.result_ready.emit(data)
        except Exception as e:
            self.error_occurred.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # ---------- 设置窗口标题和图标 ----------
        self.setWindowTitle("YG DATA")
        icon_path = resource_path("resources/app_icon.ico")
        self.setWindowIcon(QIcon(icon_path))

        # 初始化表格模型
        self.model = QStandardItemModel(self)
        self.model.setHorizontalHeaderLabels(
            ["文件名", "水接触角", "二碘甲烷接触角", "极性分量", "色散分量", "估值方法", "表面能"])
        self.ui.tableView.setModel(self.model)

        # 临时存储角度数据
        self.water_data = []
        self.diiodo_data = []
        self.progress_dialog = None

        # 连接信号与槽
        self.ui.btn_h2o.clicked.connect(self.import_water_angles)
        self.ui.btn_ch2i2.clicked.connect(self.import_diiodo_angles)
        self.ui.btn_open_file.clicked.connect(self.calculate_surface_energy)
        self.ui.btn_export_xlsx.clicked.connect(self.export_xlsx)
        self.ui.action_surface_energy.triggered.connect(self.calculate_surface_energy)

    def set_buttons_enabled(self, enabled):
        """启用/禁用所有操作按钮"""
        self.ui.btn_h2o.setEnabled(enabled)
        self.ui.btn_ch2i2.setEnabled(enabled)
        self.ui.btn_open_file.setEnabled(enabled)
        self.ui.btn_export_xlsx.setEnabled(enabled)
        self.ui.action_surface_energy.setEnabled(enabled)

    def start_extraction(self, files, is_water):
        """启动后台提取线程，并显示进度对话框"""
        self.set_buttons_enabled(False)
        self.progress_dialog = QProgressDialog("正在提取数据，请稍候...", None, 0, 0, self)
        self.progress_dialog.setWindowTitle("提示")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setCancelButton(None)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.show()

        self.worker = ExtractionWorker(files, is_water)
        self.worker.result_ready.connect(self.on_extraction_finished)
        self.worker.error_occurred.connect(self.on_extraction_error)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

    def on_extraction_finished(self, data):
        """提取成功回调"""
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        self.set_buttons_enabled(True)

        if not data:
            QMessageBox.warning(self, "提示", "未在文件中提取到有效接触角！\n注意：请确保文件格式正确。")
            return

        if self.worker.is_water:
            self.water_data = data
        else:
            self.diiodo_data = data

        QMessageBox.information(self, "成功", f"已提取 {len(data)} 个文件的数据！")
        self.update_table_view()

    def on_extraction_error(self, error_msg):
        """提取错误回调"""
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        self.set_buttons_enabled(True)
        QMessageBox.critical(self, "错误", f"提取过程中发生错误：\n{error_msg}")

    def import_water_angles(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择水滴角文件", "", "Word文档 (*.doc *.docx)")
        if files:
            self.start_extraction(files, is_water=True)

    def import_diiodo_angles(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择二碘甲烷文件", "", "Word文档 (*.doc *.docx)")
        if files:
            self.start_extraction(files, is_water=False)

    def update_table_view(self):
        """更新表格（仅填充文件名和角度，不计算）"""
        row_count = max(len(self.water_data), len(self.diiodo_data))
        self.model.setRowCount(row_count)

        for row in range(row_count):
            if row < len(self.water_data):
                self.model.setItem(row, 0, QStandardItem(self.water_data[row]['filename']))
                self.model.setItem(row, 1, QStandardItem(str(self.water_data[row]['angle'])))
            if row < len(self.diiodo_data):
                self.model.setItem(row, 2, QStandardItem(str(self.diiodo_data[row]['angle'])))

    def calculate_surface_energy(self):
        """执行表面能计算"""
        if not self.water_data or not self.diiodo_data:
            QMessageBox.warning(self, "提示", "请先导入水滴角和二碘甲烷角度数据！")
            return

        results = calculate_surface_energies(self.water_data, self.diiodo_data)
        self.model.setRowCount(len(results))

        for row, data in enumerate(results):
            self.model.setItem(row, 0, QStandardItem(str(data['文件名'])))
            self.model.setItem(row, 1, QStandardItem(str(data['水接触角'])))
            self.model.setItem(row, 2, QStandardItem(str(data['二碘甲烷接触角'])))
            self.model.setItem(row, 3, QStandardItem(str(data['极性分量'])))
            self.model.setItem(row, 4, QStandardItem(str(data['色散分量'])))
            self.model.setItem(row, 5, QStandardItem(str(data['估值方法'])))
            self.model.setItem(row, 6, QStandardItem(str(data['表面能'])))

        QMessageBox.information(self, "完成", "表面能计算完成！")

    def export_xlsx(self):
        """导出表格数据为 Excel 文件"""
        if self.model.rowCount() == 0:
            QMessageBox.warning(self, "提示", "当前没有可导出的数据！")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "导出Excel", "", "Excel文件 (*.xlsx)")
        if file_path:
            headers = ["文件名", "水接触角", "二碘甲烷接触角", "极性分量", "色散分量", "估值方法", "表面能"]
            data = []
            for row in range(self.model.rowCount()):
                row_data = {}
                for col in range(self.model.columnCount()):
                    item = self.model.item(row, col)
                    row_data[headers[col]] = item.text() if item else ""
                data.append(row_data)

            export_to_excel(data, file_path)
            QMessageBox.information(self, "成功", f"文件已导出至：{file_path}")