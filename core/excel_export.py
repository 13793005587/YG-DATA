from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter


def export_to_excel(data, file_path):
    """
    将 list[dict] 导出为 xlsx 文件。
    data: [{"列名1": 值1, "列名2": 值2, ...}, ...]
    """
    if not data:
        return

    headers = list(data[0].keys())

    wb = Workbook()
    ws = wb.active
    ws.title = "结果"

    # 表头样式
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="4A90E2")
    center = Alignment(horizontal="center", vertical="center")
    thin = Side(style="thin", color="D0D0D0")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    # 写表头
    for col_idx, name in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=name)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center
        cell.border = border

    # 写数据
    for row_idx, row in enumerate(data, start=2):
        for col_idx, key in enumerate(headers, start=1):
            value = row.get(key, "")
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.alignment = center
            cell.border = border

    # 列宽自适应（按内容长度估算）
    for col_idx, key in enumerate(headers, start=1):
        max_len = len(str(key))
        for row in data:
            v = str(row.get(key, ""))
            if len(v) > max_len:
                max_len = len(v)
        ws.column_dimensions[get_column_letter(col_idx)].width = min(max_len + 4, 40)

    # 冻结表头
    ws.freeze_panes = "A2"

    wb.save(file_path)