import os
import re
import win32com.client


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
    except Exception:
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
        except Exception:
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


# ---------- 对外主入口 ----------

def parse_doc_contact_angle(file_paths):
    """静默后台提取一组 Word 文档中的接触角平均值"""
    results = []
    if not file_paths:
        return results

    word = None
    try:
        try:
            word = win32com.client.DispatchEx("Word.Application")
        except Exception:
            word = win32com.client.DispatchEx("KWPS.Application")
        word.Visible = False
        word.DisplayAlerts = 0
    except Exception as e:
        raise RuntimeError(f"无法启动 Word/WPS 后台进程：{e}")

    try:
        for file_path in file_paths:
            doc = None
            file_name = os.path.basename(file_path)
            try:
                doc = word.Documents.Open(os.path.abspath(file_path), ReadOnly=True)
                angle = extract_angle_from_tables(doc)
                if angle is not None:
                    results.append({'filename': file_name, 'angle': angle})
                    print(f"[OK] {file_name}: {angle}")
                else:
                    print(f"[MISS] {file_name}: 未找到平均角度")
            except Exception as e:
                print(f"[ERR] {file_name}: {e}")
            finally:
                if doc is not None:
                    try:
                        doc.Close(False)
                    except Exception:
                        pass
    finally:
        if word is not None:
            try:
                word.Quit()
            except Exception:
                pass

    return results