import os
import pythoncom
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QTableView,
    QFileDialog, QMessageBox, QProgressDialog, QAbstractItemView,
    QMenu, QApplication, QInputDialog, QWidget, QSizePolicy,
    QStyledItemDelegate, QLineEdit
)
from PySide6.QtCore import (
    QThread, Signal, Qt, QItemSelection, QItemSelectionModel, QTimer, QLocale
)
from PySide6.QtGui import (
    QStandardItemModel, QStandardItem, QShortcut, QKeySequence, QDoubleValidator
)

from views.pages.base_page import BaseCalculatorPage
from core.doc_utils import parse_doc_contact_angle
from core.excel_export import export_to_excel
from core.surface_energy.processor import HEADERS, build_sample_rows
from core.surface_energy.calculator import owrk_from_template


def _strip_ext(filename):
    return os.path.splitext(filename)[0]


# ==================== 数字编辑器 ====================
class _NumberDelegate(QStyledItemDelegate):
    """编辑单元格时只允许输入数字（整数 / 小数 / 科学计数法），允许空值"""

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        v = QDoubleValidator(editor)
        v.setLocale(QLocale.c())                       # 小数点固定为 '.'
        v.setNotation(QDoubleValidator.ScientificNotation)   # 单值，不用 |
        editor.setValidator(v)
        editor.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        return editor


class _ExtractionWorker(QThread):
    result_ready = Signal(list)
    error_occurred = Signal(str)

    def __init__(self, files, is_water):
        super().__init__()
        self.files = files
        self.is_water = is_water

    def run(self):
        pythoncom.CoInitialize()
        try:
            data = parse_doc_contact_angle(self.files)
            self.result_ready.emit(data)
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            pythoncom.CoUninitialize()


class SurfaceEnergyPage(BaseCalculatorPage):
    PAGE_TITLE = "表面能计算"
    PAGE_KEY = "surface_energy"

    HEADERS = HEADERS
    TABLE_MAX_HEIGHT = 420

    # 可手动输入的列
    EDITABLE_KEYS = {"样品", "水接触角", "二碘甲烷接触角"}
    # 内部要转成 float 的列
    FLOAT_KEYS = {"水接触角", "二碘甲烷接触角"}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.water_data = []
        self.diiodo_data = []
        self.current_rows = []
        self.progress_dialog = None
        self.worker = None
        self._build_ui()

    # ==================== 工具 ====================
    @staticmethod
    def _empty_row():
        return {
            "样品": "", "水接触角": "", "二碘甲烷接触角": "",
            "极性分量": "", "色散分量": "", "估值方法": "", "表面能": ""
        }

    @staticmethod
    def _to_float(v):
        if v is None:
            return None
        s = str(v).strip()
        if s == "":
            return None
        try:
            return float(s)
        except ValueError:
            return None

    # ==================== UI ====================
    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(4)

        # ---------- 表格 ----------
        self.model = QStandardItemModel(self)
        self.model.setHorizontalHeaderLabels(self.HEADERS)

        self.table_view = QTableView(self)
        self.table_view.setModel(self.model)

        self.table_view.setEditTriggers(
            QAbstractItemView.DoubleClicked
            | QAbstractItemView.EditKeyPressed
            | QAbstractItemView.AnyKeyPressed
        )
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table_view.setAlternatingRowColors(True)

        self.table_view.horizontalHeader().setDefaultAlignment(
            Qt.AlignHCenter | Qt.AlignVCenter
        )
        self.table_view.verticalHeader().setDefaultAlignment(
            Qt.AlignHCenter | Qt.AlignVCenter
        )
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.verticalHeader().setDefaultSectionSize(28)
        self.table_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # 只给“水接触角 / 二碘甲烷接触角”挂数字 delegate
        # “样品”列用默认编辑器，可输入数字、汉字、字母、符号等任意文本
        self._number_delegate = _NumberDelegate(self.table_view)
        for c, key in enumerate(self.HEADERS):
            if key in self.FLOAT_KEYS:
                self.table_view.setItemDelegateForColumn(c, self._number_delegate)

        # 行号点击 → 选中整行
        self.table_view.verticalHeader().setSectionsClickable(True)
        self.table_view.verticalHeader().sectionClicked.connect(self._on_header_clicked)

        # 右键菜单
        self.table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self._on_context_menu)

        # Delete 键 → 清空选中单元格
        self._del_shortcut = QShortcut(QKeySequence.Delete, self.table_view)
        self._del_shortcut.setContext(Qt.WidgetShortcut)
        self._del_shortcut.activated.connect(self._delete_selected_cells)

        # 单元格编辑同步
        self.model.itemChanged.connect(self._on_item_changed)

        # ---------- 表格 + 紧贴其下的 "+" 按钮 ----------
        table_container = QWidget()
        table_container_layout = QVBoxLayout(table_container)
        table_container_layout.setContentsMargins(0, 0, 0, 0)
        table_container_layout.setSpacing(0)

        table_container_layout.addWidget(self.table_view)

        plus_row = QHBoxLayout()
        plus_row.setContentsMargins(0, 0, 0, 0)
        plus_row.addStretch(1)
        self.btn_add_row = QPushButton("+")
        self.btn_add_row.setFixedSize(36, 28)
        self.btn_add_row.setToolTip("点击新增一行空行，可手动输入数据")
        self.btn_add_row.setStyleSheet(
            "QPushButton {"
            "  font-weight: bold; font-size: 18px;"
            "  color: #2a7; border: 1px solid #c8e6d5;"
            "  border-radius: 4px; background: #f4fbf6;"
            "}"
            "QPushButton:hover { background: #e0f5e8; }"
            "QPushButton:pressed { background: #cceedd; }"
        )
        self.btn_add_row.clicked.connect(self._on_add_row_clicked)
        plus_row.addWidget(self.btn_add_row)
        plus_row.addStretch(1)
        table_container_layout.addLayout(plus_row)

        main_layout.addWidget(table_container)
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

        btns.addWidget(self.btn_h2o,    0, 0)
        btns.addWidget(self.btn_ch2i2,  0, 1)
        btns.addWidget(self.btn_calc,   1, 0)
        btns.addWidget(self.btn_clear,  1, 1)
        btns.addWidget(self.btn_export, 2, 0, 1, 2)

        main_layout.addLayout(btns)

        # ---------- 信号 ----------
        self.btn_h2o.clicked.connect(lambda: self._import(is_water=True))
        self.btn_ch2i2.clicked.connect(lambda: self._import(is_water=False))
        self.btn_calc.clicked.connect(self._calculate)
        self.btn_clear.clicked.connect(self._clear_all)
        self.btn_export.clicked.connect(self._export)

        # 初始渲染
        self._render_rows([])

    # ==================== 表格高度自适应 ====================
    def _adjust_table_height(self):
        header_h = self.table_view.horizontalHeader().height()
        rows_h = sum(self.table_view.rowHeight(r) for r in range(self.model.rowCount()))
        frame = 2 * self.table_view.frameWidth()

        if self.model.rowCount() == 0:
            total = header_h + frame + 2
        else:
            total = header_h + rows_h + frame + 4

        total = max(total, header_h + frame + 2)
        total = min(total, self.TABLE_MAX_HEIGHT)
        self.table_view.setFixedHeight(total)

    # ==================== 渲染 ====================
    def _render_rows(self, rows):
        self.current_rows = [dict(r) for r in rows]

        try:
            self.model.itemChanged.disconnect(self._on_item_changed)
        except (RuntimeError, TypeError):
            pass

        self.model.setRowCount(len(self.current_rows))
        for r, row in enumerate(self.current_rows):
            for c, key in enumerate(self.HEADERS):
                v = row.get(key, "")
                item = QStandardItem(str(v))
                item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                # 只有三列可编辑，其余列锁定
                if key not in self.EDITABLE_KEYS:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.model.setItem(r, c, item)

        self.model.itemChanged.connect(self._on_item_changed)
        QTimer.singleShot(0, self._adjust_table_height)

    def _on_item_changed(self, item):
        r = item.row()
        c = item.column()
        if r < 0 or r >= len(self.current_rows):
            return
        key = self.HEADERS[c]
        if key not in self.EDITABLE_KEYS:
            return

        text = item.text().strip()

        if key in self.FLOAT_KEYS:
            if text == "":
                self.current_rows[r][key] = ""
            else:
                try:
                    self.current_rows[r][key] = float(text)
                except ValueError:
                    # 理论上被 delegate 拦下，这里做兜底
                    self.current_rows[r][key] = ""
                    self.model.blockSignals(True)
                    item.setText("")
                    self.model.blockSignals(False)
        else:  # 样品
            self.current_rows[r][key] = text

    # ==================== 行号点击 ====================
    def _on_header_clicked(self, row):
        if row < 0 or row >= len(self.current_rows):
            return

        model = self.model
        sm = self.table_view.selectionModel()
        col_count = model.columnCount()
        modifiers = QApplication.keyboardModifiers()

        if modifiers & Qt.ControlModifier:
            selection = QItemSelection(
                model.index(row, 0),
                model.index(row, col_count - 1)
            )
            sm.select(selection, QItemSelectionModel.Select)
        elif modifiers & Qt.ShiftModifier:
            sel_rows = [i.row() for i in sm.selectedIndexes()
                        if i.row() < len(self.current_rows)]
            if sel_rows:
                r0 = min(min(sel_rows), row)
                r1 = max(max(sel_rows), row)
            else:
                r0 = r1 = row
            selection = QItemSelection(
                model.index(r0, 0),
                model.index(r1, col_count - 1)
            )
            sm.select(selection, QItemSelectionModel.ClearAndSelect)
        else:
            selection = QItemSelection(
                model.index(row, 0),
                model.index(row, col_count - 1)
            )
            sm.select(selection, QItemSelectionModel.ClearAndSelect)

    # ==================== 导入 ====================
    def _import(self, is_water):
        title = "选择水滴角文件" if is_water else "选择二碘甲烷文件"
        files, _ = QFileDialog.getOpenFileNames(self, title, "", "Word文档 (*.doc *.docx)")
        if files:
            self._start_extraction(files, is_water)

    def _set_buttons_enabled(self, enabled):
        for b in (self.btn_h2o, self.btn_ch2i2, self.btn_calc,
                  self.btn_clear, self.btn_export, self.btn_add_row):
            b.setEnabled(enabled)

    def _start_extraction(self, files, is_water):
        self._set_buttons_enabled(False)
        self.progress_dialog = QProgressDialog("正在提取数据，请稍候...", None, 0, 0, self)
        self.progress_dialog.setWindowTitle("提示")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setCancelButton(None)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.show()

        self.worker = _ExtractionWorker(files, is_water)
        self.worker.result_ready.connect(self._on_extract_done)
        self.worker.error_occurred.connect(self._on_extract_error)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

    def _on_extract_done(self, data):
        self._close_progress()
        self._set_buttons_enabled(True)

        if not data:
            QMessageBox.warning(self, "提示", "未在文件中提取到有效接触角！\n请确认文件格式。")
            return

        if self.worker.is_water:
            self.water_data = data
        else:
            self.diiodo_data = data

        QMessageBox.information(self, "成功", f"已提取 {len(data)} 个文件的数据！")

        imported_rows = build_sample_rows(self.water_data, self.diiodo_data)
        manual_rows = [
            r for r in self.current_rows
            if not str(r.get("样品", "")).strip()
            and self._to_float(r.get("水接触角")) is None
            and self._to_float(r.get("二碘甲烷接触角")) is None
            and not str(r.get("极性分量", "")).strip()
            and not str(r.get("表面能", "")).strip()
        ]
        self._render_rows(imported_rows + manual_rows)

    def _on_extract_error(self, msg):
        self._close_progress()
        self._set_buttons_enabled(True)
        QMessageBox.critical(self, "错误", f"提取过程中发生错误：\n{msg}")

    def _close_progress(self):
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

    # ==================== 追加空行 ====================
    def _on_add_row_clicked(self):
        self.current_rows.append(self._empty_row())
        self._render_rows(self.current_rows)

    # ==================== 计算 ====================
    def _calculate(self):
        if not self.current_rows:
            QMessageBox.warning(self, "提示", "请先导入数据或手动添加行！")
            return

        new_rows = []
        paired = only_w = only_d = empty = 0

        for row in self.current_rows:
            theta_w = self._to_float(row.get("水接触角", ""))
            theta_d = self._to_float(row.get("二碘甲烷接触角", ""))

            new_row = dict(row)

            if theta_w is None and theta_d is None:
                empty += 1
                new_row["极性分量"] = ""
                new_row["色散分量"] = ""
                new_row["估值方法"] = ""
                new_row["表面能"] = ""
            elif theta_w is None:
                only_d += 1
                new_row["极性分量"] = ""
                new_row["色散分量"] = ""
                new_row["估值方法"] = ""
                new_row["表面能"] = ""
            elif theta_d is None:
                only_w += 1
                new_row["极性分量"] = ""
                new_row["色散分量"] = ""
                new_row["估值方法"] = ""
                new_row["表面能"] = ""
            else:
                try:
                    res = owrk_from_template(theta_w, theta_d)
                    new_row["水接触角"] = round(theta_w, 3)
                    new_row["二碘甲烷接触角"] = round(theta_d, 3)
                    new_row["极性分量"] = round(res["gamma_p"], 3)
                    new_row["色散分量"] = round(res["gamma_d"], 3)
                    new_row["估值方法"] = "OWRK"
                    new_row["表面能"] = round(res["gamma_total"], 3)
                    paired += 1
                except Exception as e:
                    print(f"[ERR] 计算 {new_row.get('样品')} 失败: {e}")
                    new_row["极性分量"] = ""
                    new_row["色散分量"] = ""
                    new_row["估值方法"] = ""
                    new_row["表面能"] = ""

            new_rows.append(new_row)

        self._render_rows(new_rows)

        msg = f"表面能计算完成！\n\n成功配对并计算：{paired} 个样品"
        if only_w:
            msg += f"\n仅有水滴角（未计算）：{only_w} 个"
        if only_d:
            msg += f"\n仅有二碘甲烷角（未计算）：{only_d} 个"
        if empty:
            msg += f"\n空行（未计算）：{empty} 个"
        QMessageBox.information(self, "完成", msg)

    # ==================== 清空全部 ====================
    def _clear_all(self):
        if not self.current_rows and not self.water_data and not self.diiodo_data:
            return
        ret = QMessageBox.question(
            self, "确认清空",
            "确定要清空所有已导入的数据和计算结果吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if ret != QMessageBox.Yes:
            return

        self.water_data = []
        self.diiodo_data = []
        self._render_rows([])

    # ==================== 删除选中单元格 ====================
    def _delete_selected_cells(self):
        sm = self.table_view.selectionModel()
        indexes = sm.selectedIndexes()
        if not indexes:
            return

        indexes = [i for i in indexes if 0 <= i.row() < len(self.current_rows)]
        if not indexes:
            return

        try:
            self.model.itemChanged.disconnect(self._on_item_changed)
        except (RuntimeError, TypeError):
            pass

        for idx in indexes:
            # 只清可编辑的列
            key = self.HEADERS[idx.column()]
            if key not in self.EDITABLE_KEYS:
                continue

            item = self.model.itemFromIndex(idx)
            if item is None:
                item = QStandardItem("")
                item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                self.model.setItem(idx.row(), idx.column(), item)
            else:
                item.setText("")
            self.current_rows[idx.row()][key] = ""

        self.model.itemChanged.connect(self._on_item_changed)

    # ==================== 删除选中行 ====================
    def _delete_selected_rows(self):
        sm = self.table_view.selectionModel()
        selected_rows = sorted(
            {i.row() for i in sm.selectedIndexes() if 0 <= i.row() < len(self.current_rows)},
            reverse=True
        )
        if not selected_rows:
            return

        keys_to_delete = set()
        for r in selected_rows:
            key = str(self.current_rows[r].get("样品", "")).strip()
            if key:
                keys_to_delete.add(key)

        for r in selected_rows:
            self.current_rows.pop(r)

        if keys_to_delete:
            self.water_data = [
                w for w in self.water_data
                if _strip_ext(w['filename']) not in keys_to_delete
            ]
            self.diiodo_data = [
                d for d in self.diiodo_data
                if _strip_ext(d['filename']) not in keys_to_delete
            ]

        self._render_rows(self.current_rows)

    # ==================== 插入行 ====================
    def _insert_rows(self, above=True):
        sm = self.table_view.selectionModel()
        selected_rows = sorted(
            {i.row() for i in sm.selectedIndexes() if 0 <= i.row() < len(self.current_rows)}
        )

        if not selected_rows:
            insert_at = len(self.current_rows)
        elif above:
            insert_at = selected_rows[0]
        else:
            insert_at = selected_rows[-1] + 1

        count, ok = QInputDialog.getInt(
            self, "插入行", "要插入的行数：", 1, 1, 200
        )
        if not ok:
            return

        for _ in range(count):
            self.current_rows.insert(insert_at, self._empty_row())

        self._render_rows(self.current_rows)

    # ==================== 右键菜单 ====================
    def _on_context_menu(self, pos):
        index = self.table_view.indexAt(pos)
        sm = self.table_view.selectionModel()

        if index.isValid() and not sm.isSelected(index):
            sm.select(index, QItemSelectionModel.ClearAndSelect)

        selected_indexes = [
            i for i in sm.selectedIndexes() if 0 <= i.row() < len(self.current_rows)
        ]
        selected_rows = sorted({i.row() for i in selected_indexes})

        menu = QMenu(self)

        if selected_indexes:
            act_del_cells = menu.addAction(
                f"删除选中单元格内容（{len(selected_indexes)} 格）"
            )
            act_del_rows = menu.addAction(
                f"删除选中行（{len(selected_rows)} 行）"
            )
        else:
            act_del_cells = menu.addAction("删除选中单元格内容")
            act_del_cells.setEnabled(False)
            act_del_rows = menu.addAction("删除选中行")
            act_del_rows.setEnabled(False)

        menu.addSeparator()

        insert_menu = menu.addMenu("插入行")
        act_insert_above = insert_menu.addAction("在上方插入...")
        act_insert_below = insert_menu.addAction("在下方插入...")

        menu.addSeparator()

        act_clear = menu.addAction("清空全部数据")

        chosen = menu.exec(self.table_view.viewport().mapToGlobal(pos))
        if chosen == act_del_cells:
            self._delete_selected_cells()
        elif chosen == act_del_rows:
            self._delete_selected_rows()
        elif chosen == act_insert_above:
            self._insert_rows(above=True)
        elif chosen == act_insert_below:
            self._insert_rows(above=False)
        elif chosen == act_clear:
            self._clear_all()

    # ==================== 导出 ====================
    def _export(self):
        if not self.current_rows:
            QMessageBox.warning(self, "提示", "当前没有可导出的数据！")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "导出Excel", "", "Excel文件 (*.xlsx)")
        if not file_path:
            return
        if not file_path.lower().endswith(".xlsx"):
            file_path += ".xlsx"

        rows_to_export = [
            r for r in self.current_rows
            if any(str(r.get(k, "")).strip() for k in self.HEADERS)
        ]
        if not rows_to_export:
            QMessageBox.warning(self, "提示", "所有行都是空的，无需导出。")
            return

        export_to_excel(rows_to_export, file_path)
        QMessageBox.information(self, "成功", f"文件已导出至：{file_path}")