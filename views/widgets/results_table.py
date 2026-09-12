"""表面能页面使用的可编辑结果表组件。

把原先散落在页面里约 300 行的表格交互（行号选择、右键菜单、
Delete 清空、插入多行、高度自适应）收敛到这里，页面只负责业务。

高度策略：
  * 0 行时表格只占表头高度，"+" 号紧贴其下，不多占空间
  * 行数增加时表格随之增高，直到完整显示所有行
  * 可用空间不足时由外层布局压缩（表格出现滚动条），
    底部按钮与 "+" 号始终可见
"""

import logging

from PySide6.QtCore import (
    QItemSelection,
    QItemSelectionModel,
    QSize,
    Qt,
    QTimer,
)
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QHBoxLayout,
    QInputDialog,
    QMenu,
    QPushButton,
    QSizePolicy,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from core.surface_energy.processor import FLOAT_KEYS, HEADERS
from views.models.sample_table_model import NumberDelegate, SampleTableModel

logger = logging.getLogger(__name__)


class ResultsTableWidget(QWidget):
    """可编辑样品表：表格 + 紧贴其下的 "+" 按钮。"""

    MAX_INSERT_ROWS = 200

    # "+" 按钮行的高度（按钮本身 28px）与表格下方的余量
    _PLUS_ROW_HEIGHT = 28
    _BOTTOM_PADDING = 4

    def __init__(self, on_rows_removed=None, on_clear_requested=None, parent=None):
        """
        on_rows_removed(rows)  —— 行被删除后回调，参数为被删行的数据副本
        on_clear_requested()   —— 用户选择「清空全部数据」时回调
        """
        super().__init__(parent)
        self._on_rows_removed = on_rows_removed
        self._on_clear_requested = on_clear_requested

        self.model = SampleTableModel(self)
        self.model.rowsInserted.connect(self._schedule_height_update)
        self.model.rowsRemoved.connect(self._schedule_height_update)
        self.model.modelReset.connect(self._schedule_height_update)

        self._build_ui()
        # 首帧就用正确高度：否则 QTableView 默认 Expanding 会吃掉全部空间
        self._adjust_table_height()

    # ==================== UI ====================
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

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
        self.table_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.table_view.horizontalHeader().setDefaultAlignment(
            Qt.AlignHCenter | Qt.AlignVCenter
        )
        self.table_view.verticalHeader().setDefaultAlignment(
            Qt.AlignHCenter | Qt.AlignVCenter
        )
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.verticalHeader().setDefaultSectionSize(28)

        # 只给「水接触角 / 二碘甲烷接触角」挂数字 delegate；
        # 「样品」列使用默认编辑器，可输入任意文本
        self._number_delegate = NumberDelegate(self.table_view)
        for column, key in enumerate(HEADERS):
            if key in FLOAT_KEYS:
                self.table_view.setItemDelegateForColumn(column, self._number_delegate)

        # 行号点击 → 选中整行
        self.table_view.verticalHeader().setSectionsClickable(True)
        self.table_view.verticalHeader().sectionClicked.connect(self._on_header_clicked)

        # 右键菜单
        self.table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self._on_context_menu)

        # Delete 键 → 清空选中单元格
        self._del_shortcut = QShortcut(QKeySequence.Delete, self.table_view)
        self._del_shortcut.setContext(Qt.WidgetShortcut)
        self._del_shortcut.activated.connect(self.delete_selected_cells)

        layout.addWidget(self.table_view)

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
        self.btn_add_row.clicked.connect(self.model.append_empty_row)
        plus_row.addWidget(self.btn_add_row)
        plus_row.addStretch(1)
        layout.addLayout(plus_row)

    # ==================== 高度自适应 ====================
    def _ideal_table_height(self):
        """完整显示当前所有行所需的表格高度。"""
        header_h = self.table_view.horizontalHeader().height()
        rows_h = sum(
            self.table_view.rowHeight(row) for row in range(self.model.rowCount())
        )
        return header_h + rows_h + 2 * self.table_view.frameWidth() + 4

    def sizeHint(self):
        """整个组件（表格 + "+" 行）的自然高度。"""
        hint = super().sizeHint()
        return QSize(
            hint.width(),
            self._ideal_table_height() + self._PLUS_ROW_HEIGHT + self._BOTTOM_PADDING,
        )

    def showEvent(self, event):
        # 表头高度要等首次显示才最终确定，显示后重算一次
        super().showEvent(event)
        self._adjust_table_height()

    def _schedule_height_update(self, *_args):
        QTimer.singleShot(0, self._adjust_table_height)

    def _adjust_table_height(self):
        """把表格高度限制在「完整显示所有行」以内。

        行少时表格自然短、"+" 号紧贴其下；行多时表格尽量增高，
        空间不够则由外层布局压缩（出现滚动条），不会把按钮挤出窗口。
        """
        ideal = self._ideal_table_height()
        header_h = self.table_view.horizontalHeader().height()
        frame = self.table_view.frameWidth()

        self.table_view.setMaximumHeight(ideal)
        self.table_view.setMinimumHeight(header_h + 2 * frame + 2)
        self.updateGeometry()

    # ==================== 行号点击 ====================
    def _on_header_clicked(self, row):
        if not 0 <= row < self.model.rowCount():
            return

        sm = self.table_view.selectionModel()
        col_count = self.model.columnCount()
        selection = None

        if QApplication.keyboardModifiers() & Qt.ControlModifier:
            selection = QItemSelection(
                self.model.index(row, 0), self.model.index(row, col_count - 1)
            )
            sm.select(selection, QItemSelectionModel.Select)
            return

        if QApplication.keyboardModifiers() & Qt.ShiftModifier:
            selected = [i.row() for i in sm.selectedIndexes()]
            if selected:
                r0, r1 = min(min(selected), row), max(max(selected), row)
            else:
                r0 = r1 = row
        else:
            r0 = r1 = row

        selection = QItemSelection(
            self.model.index(r0, 0), self.model.index(r1, col_count - 1)
        )
        sm.select(selection, QItemSelectionModel.ClearAndSelect)

    # ==================== 选中辅助 ====================
    def _selected_indexes(self):
        return [
            i for i in self.table_view.selectionModel().selectedIndexes()
            if 0 <= i.row() < self.model.rowCount()
        ]

    def _selected_rows(self):
        return sorted({i.row() for i in self._selected_indexes()})

    # ==================== 操作 ====================
    def delete_selected_cells(self):
        indexes = self._selected_indexes()
        if indexes:
            self.model.clear_cells(indexes)

    def delete_selected_rows(self):
        rows = self._selected_rows()
        if not rows:
            return
        removed = [self.model.row_at(r) for r in rows]
        self.model.remove_rows(rows)
        if self._on_rows_removed:
            self._on_rows_removed([r for r in removed if r])

    def insert_rows(self, above=True):
        selected = self._selected_rows()
        if not selected:
            insert_at = self.model.rowCount()
        elif above:
            insert_at = selected[0]
        else:
            insert_at = selected[-1] + 1

        count, ok = QInputDialog.getInt(
            self, "插入行", "要插入的行数：", 1, 1, self.MAX_INSERT_ROWS
        )
        if not ok:
            return
        self.model.insert_empty_rows(insert_at, count)

    # ==================== 右键菜单 ====================
    def _on_context_menu(self, pos):
        index = self.table_view.indexAt(pos)
        sm = self.table_view.selectionModel()

        if index.isValid() and not sm.isSelected(index):
            sm.select(index, QItemSelectionModel.ClearAndSelect)

        selected_indexes = self._selected_indexes()
        selected_rows = sorted({i.row() for i in selected_indexes})

        menu = QMenu(self)
        if selected_indexes:
            act_del_cells = menu.addAction(
                f"删除选中单元格内容（{len(selected_indexes)} 格）"
            )
            act_del_rows = menu.addAction(f"删除选中行（{len(selected_rows)} 行）")
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
        if chosen is None:
            return
        if chosen == act_del_cells:
            self.delete_selected_cells()
        elif chosen == act_del_rows:
            self.delete_selected_rows()
        elif chosen == act_insert_above:
            self.insert_rows(above=True)
        elif chosen == act_insert_below:
            self.insert_rows(above=False)
        elif chosen == act_clear and self._on_clear_requested:
            self._on_clear_requested()