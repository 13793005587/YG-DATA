"""表面能结果表的 Qt 数据模型。

替代原先「``list[dict]`` + ``QStandardItemModel`` 双份状态、靠
disconnect/reconnect ``itemChanged`` 手工同步」的做法：
这里以 ``list[dict]`` 为唯一数据源，增删改都通过标准模型通知，
选中状态与滚动位置不会在每次操作后丢失。
"""

import logging

from PySide6.QtCore import QAbstractTableModel, QLocale, QModelIndex, Qt
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import QLineEdit, QStyledItemDelegate

from core.surface_energy.processor import (
    EDITABLE_KEYS,
    FLOAT_KEYS,
    HEADERS,
    empty_row,
)

logger = logging.getLogger(__name__)


def make_number_validator(parent):
    """数字校验器：小数点固定为 '.'，支持科学计数法。"""
    validator = QDoubleValidator(parent)
    validator.setLocale(QLocale.c())
    validator.setNotation(QDoubleValidator.ScientificNotation)
    return validator


class NumberDelegate(QStyledItemDelegate):
    """编辑单元格时只允许输入数字（整数 / 小数 / 科学计数法），允许空值"""

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setValidator(make_number_validator(editor))
        editor.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        return editor


class SampleTableModel(QAbstractTableModel):
    """以 ``list[dict]`` 为唯一数据源的表格模型。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows = []

    # ---------------- 只读接口 ----------------
    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(HEADERS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return HEADERS[section]
        return section + 1

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = self._rows[index.row()]
        key = HEADERS[index.column()]

        if role in (Qt.DisplayRole, Qt.EditRole):
            return str(row.get(key, ""))
        if role == Qt.TextAlignmentRole:
            return int(Qt.AlignHCenter | Qt.AlignVCenter)
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if HEADERS[index.column()] in EDITABLE_KEYS:
            flags |= Qt.ItemIsEditable
        return flags

    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole or not index.isValid():
            return False

        key = HEADERS[index.column()]
        if key not in EDITABLE_KEYS:
            return False

        text = "" if value is None else str(value).strip()

        if key in FLOAT_KEYS:
            if text == "":
                stored = ""
            else:
                try:
                    stored = float(text)
                except ValueError:
                    # 校验器通常已拦下，这里兜底：保留原值并给出可见反馈
                    logger.warning(
                        "第 %d 行「%s」输入非法，已忽略：%r",
                        index.row() + 1, key, text,
                    )
                    return False
        else:
            stored = text

        if self._rows[index.row()].get(key) == stored:
            return False

        self._rows[index.row()][key] = stored
        self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
        return True

    # ---------------- 批量接口 ----------------
    def rows(self):
        """返回数据副本（外部修改不会影响模型）。"""
        return [dict(r) for r in self._rows]

    def row_at(self, index):
        if 0 <= index < len(self._rows):
            return dict(self._rows[index])
        return None

    def set_rows(self, rows):
        self.beginResetModel()
        self._rows = [dict(r) for r in (rows or [])]
        self.endResetModel()

    def insert_empty_rows(self, at, count):
        if count <= 0:
            return
        at = max(0, min(at, len(self._rows)))
        self.beginInsertRows(QModelIndex(), at, at + count - 1)
        for offset in range(count):
            self._rows.insert(at + offset, empty_row())
        self.endInsertRows()

    def append_empty_row(self):
        self.insert_empty_rows(len(self._rows), 1)

    def remove_rows(self, row_indexes):
        """删除给定行号（自动去重、降序删除）。"""
        for row in sorted({r for r in row_indexes}, reverse=True):
            if 0 <= row < len(self._rows):
                self.beginRemoveRows(QModelIndex(), row, row)
                self._rows.pop(row)
                self.endRemoveRows()

    def clear_cells(self, indexes):
        """清空给定单元格（仅限可编辑列）。"""
        changed = set()
        for index in indexes:
            if not index.isValid() or HEADERS[index.column()] not in EDITABLE_KEYS:
                continue
            row = self._rows[index.row()]
            key = HEADERS[index.column()]
            if row.get(key, "") != "":
                row[key] = ""
                changed.add(index.row())

        for row in changed:
            left = self.index(row, 0)
            right = self.index(row, len(HEADERS) - 1)
            self.dataChanged.emit(left, right, [Qt.DisplayRole, Qt.EditRole])
