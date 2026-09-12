"""Word / WPS 报告解析：从仪器导出的 .doc/.docx 表格中提取平均接触角。

设计要点：
  * ``pywin32`` 采用**惰性导入**——没装 pywin32 或本机没有 Office 时，
    首页与导电性计算等其它功能仍可正常使用，只在真正导入 Word 时提示。
  * 返回 ``(结果列表, 失败明细)``，失败文件不会被静默丢弃，UI 可以把
    "哪几个文件没读到、为什么" 明确告诉用户。
  * COM 线程初始化在本模块内部完成（后台线程调用不会踩坑）。
  * 所有诊断信息走 logging，不再用 print（发布版控制台不存在）。
"""

import logging
import os
import re

logger = logging.getLogger(__name__)

# 惰性导入的 COM 客户端（模块级变量，便于测试时替换）
win32com = None


class DocParseError(RuntimeError):
    """无法启动 Word/WPS，或本机缺少 COM 支持。"""


class ComUnavailableError(DocParseError):
    """未安装 pywin32。"""


def _import_win32com():
    global win32com
    if win32com is not None:
        return win32com
    try:
        import win32com.client as _client  # noqa: PLC0415 - 故意的惰性导入
    except ImportError as e:
        raise ComUnavailableError(
            "缺少 pywin32，无法读取 Word 报告。\n"
            "请执行：pip install pywin32"
        ) from e
    win32com = _client
    return win32com


# ---------- 基础清洗 / 数值解析 ----------

_CELL_CLEAN_RE = re.compile(r'[\r\x07\n]')
# 支持 103.085、103.085°、-3.5、1.2e-3
_NUM_RE = re.compile(r'[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?')

# 表头典型特征（含单位符号、括号、序号列等）
_HEADER_HINTS = (
    '°', '(', ')', '（', '）',
    '序号', '时间', '液滴', '判断', '直径',
    '左接触角', '右接触角', '左角', '右角',
)


def _clean(text):
    if text is None:
        return ""
    return _CELL_CLEAN_RE.sub('', str(text)).strip()


def parse_number(text):
    """从任意文本中提取数值；失败返回 None"""
    if text is None:
        return None
    s = _clean(text)
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        pass
    m = _NUM_RE.search(s)
    if m:
        try:
            return float(m.group(0))
        except ValueError:
            return None
    return None


def _cell_text(table, i, j):
    try:
        return _clean(table.Cell(i, j).Range.Text)
    except Exception:  # noqa: BLE001 - 合并单元格会直接抛错，属正常情况
        return ""


def _search_neighbor(table, r, c, row_count, col_count):
    """在 (r, c) 同一行向右、同一列向下，找到第一个可解析数值"""
    for j in range(c + 1, col_count + 1):
        v = parse_number(_cell_text(table, r, j))
        if v is not None:
            return v
    for i in range(r + 1, row_count + 1):
        v = parse_number(_cell_text(table, i, c))
        if v is not None:
            return v
    return None


def _is_header(text):
    """粗略判断是否为表头单元格"""
    return any(h in text for h in _HEADER_HINTS)


# ---------- 角度提取 ----------

def _priority_of(text, kw):
    """
    候选单元格优先级（越小越可信）：
      0: 文本精确等于 "平均角度"
      1: 文本精确等于 "平均接触角"
      2: 文本包含关键词，且不像表头
      3: 文本包含关键词，且像表头（如 "平均接触角(°)"）
    """
    if text == "平均角度":
        return 0
    if text == "平均接触角":
        return 1
    if _is_header(text):
        return 3
    return 2


def extract_angle_from_tables(doc, keywords=("平均角度", "平均接触角")):
    """
    从 Word 文档的所有表格里定位汇总角度值。

    处理策略：
      1. 遍历所有单元格，命中关键词者参与候选
      2. 候选打分：精确 "平均角度" > 精确 "平均接触角" > 含关键词非表头 > 含关键词表头
      3. 单元格内直接解析数字（如 "平均角度：77.336"）；否则向右、向下邻近搜索
      4. 优先级相同时保留后出现的（汇总行通常在表格底部）
    """
    best = None  # (priority, value)

    for table in doc.Tables:
        try:
            row_count = table.Rows.Count
            col_count = table.Columns.Count
        except Exception:  # noqa: BLE001 - 个别表格无 Rows/Columns，跳过
            logger.debug("跳过无法读取行列数的表格", exc_info=True)
            continue

        for i in range(1, row_count + 1):
            for j in range(1, col_count + 1):
                text = _cell_text(table, i, j)
                if not text:
                    continue

                for kw in keywords:
                    if kw not in text:
                        continue

                    prio = _priority_of(text, kw)

                    # ① 先在单元格内取数（把关键词剥掉再解析，避免误取关键词里的数字）
                    v = parse_number(text.replace(kw, ""))
                    # ② 再向右 / 向下寻找邻近数值
                    if v is None:
                        v = _search_neighbor(table, i, j, row_count, col_count)
                    if v is None:
                        continue

                    # 优先级更优，或同级但更靠后 → 覆盖
                    if best is None or prio <= best[0]:
                        best = (prio, v)

    return best[1] if best else None


# ---------- Word / WPS 生命周期 ----------

def _try_dispatch(prog_id):
    client = _import_win32com()
    try:
        return client.DispatchEx(prog_id)
    except Exception as e:  # noqa: BLE001 - COM 抛出的异常类型不固定
        logger.debug("DispatchEx(%s) 失败：%s", prog_id, e)
        return None


def _open_word_app():
    """依次尝试 Microsoft Word 与 WPS；都失败时抛出带排查建议的错误。"""
    app = _try_dispatch("Word.Application")
    if app is None:
        app = _try_dispatch("KWPS.Application")
    if app is None:
        raise DocParseError(
            "无法启动 Word / WPS\n"
            "请确认本机已安装 Microsoft Word 或 WPS Office，"
            "并且当前用户有权限调用其 COM 接口。"
        )

    # 这两个属性并非所有 Office/WPS 版本都支持，失败也不应中断流程
    for name, value in (("Visible", False), ("DisplayAlerts", 0)):
        try:
            setattr(app, name, value)
        except Exception:  # noqa: BLE001
            logger.debug("设置 %s 失败（不影响解析）", name, exc_info=True)
    return app


def _parse_with_word(file_paths):
    """实际执行解析，返回 (results, failures)。"""
    results = []
    failures = []

    app = _open_word_app()
    try:
        for file_path in file_paths:
            doc = None
            file_name = os.path.basename(file_path)
            try:
                doc = app.Documents.Open(os.path.abspath(file_path), ReadOnly=True)
                angle = extract_angle_from_tables(doc)
                if angle is None:
                    reason = "未在文档表格中找到“平均角度/平均接触角”字段"
                    failures.append({"filename": file_name, "reason": reason})
                    logger.warning("[MISS] %s：%s", file_name, reason)
                else:
                    results.append({"filename": file_name, "angle": angle})
                    logger.info("[OK] %s：%s", file_name, angle)
            except Exception as e:  # noqa: BLE001 - 单个文件失败不应中断整批
                failures.append({"filename": file_name, "reason": str(e)})
                logger.warning("[ERR] %s：%s", file_name, e)
            finally:
                if doc is not None:
                    try:
                        doc.Close(False)
                    except Exception:  # noqa: BLE001
                        logger.debug("关闭文档失败：%s", file_name, exc_info=True)
    finally:
        try:
            app.Quit()
        except Exception:  # noqa: BLE001
            logger.debug("退出 Word/WPS 失败", exc_info=True)

    return results, failures


def parse_doc_contact_angle(file_paths):
    """后台提取一组 Word 文档中的接触角平均值。

    返回 ``(results, failures)``：
      * results  —— ``[{"filename": str, "angle": float}, ...]``
      * failures —— ``[{"filename": str, "reason": str}, ...]``

    本函数需要在后台线程中调用；内部负责 COM 的初始化与反初始化。
    """
    if not file_paths:
        return [], []

    pythoncom = None
    try:
        import pythoncom  # noqa: PLC0415 - 随 pywin32 一起提供，惰性导入

        pythoncom.CoInitialize()
    except ImportError:
        raise ComUnavailableError(
            "缺少 pywin32（pythoncom），无法读取 Word 报告。\n"
            "请执行：pip install pywin32"
        ) from None

    try:
        return _parse_with_word(file_paths)
    finally:
        try:
            pythoncom.CoUninitialize()
        except Exception:  # noqa: BLE001
            logger.debug("CoUninitialize 失败", exc_info=True)
