"""公共导出流程：保存对话框 + 异常兜底。

两个功能页原来各写了一遍「选路径 → 补扩展名 → 调导出 → 弹成功框」，
且都没有处理写入失败（文件被 Excel 占用时直接崩溃）。这里统一收口。
"""

import logging

from PySide6.QtWidgets import QFileDialog

from core.excel_export import ExportError, export_to_excel
from views.dialogs.compat import qmessagebox

logger = logging.getLogger(__name__)


def export_rows_with_dialog(parent, rows, headers=None, title="导出Excel"):
    """把 rows 导出为 xlsx（带保存对话框与完整异常处理）。

    返回实际写入的路径；用户取消或导出失败时返回 None。
    """
    if not rows:
        qmessagebox().warning(parent, "提示", "当前没有可导出的数据！")
        return None

    file_path, _ = QFileDialog.getSaveFileName(
        parent, title, "", "Excel文件 (*.xlsx)"
    )
    if not file_path:
        return None
    if not file_path.lower().endswith(".xlsx"):
        file_path += ".xlsx"

    try:
        export_to_excel(rows, file_path, headers=headers)
    except ExportError as e:
        qmessagebox().critical(parent, "导出失败", str(e))
        return None

    qmessagebox().information(parent, "成功", f"文件已导出至：\n{file_path}")
    return file_path
