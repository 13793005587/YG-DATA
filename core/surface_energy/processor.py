"""表面能业务逻辑：样品配对、批量计算与结果统计。

UI 只负责渲染这里产出的行数据与统计结果，不再重复实现计算流程。
"""

import logging
import os

from core.surface_energy.calculator import OWRKError, owrk_from_template

logger = logging.getLogger(__name__)

# 内部行标识列。值取自导入文件名（去扩展名后），是稳定的行唯一键；
# 用户可自由修改「样品」列而不影响删除时对原始数据的定位。
ID_KEY = "序号"

HEADERS = [ID_KEY, "样品", "水接触角", "二碘甲烷接触角",
           "极性分量", "色散分量", "估值方法", "表面能"]

# 导出到 Excel 时排除内部列
EXPORT_HEADERS = [h for h in HEADERS if h != ID_KEY]

# 可手动输入的列
EDITABLE_KEYS = {"样品", "水接触角", "二碘甲烷接触角"}
# 需要按浮点数处理的列
FLOAT_KEYS = {"水接触角", "二碘甲烷接触角"}
# 计算结果列，计算前需要清空
RESULT_KEYS = ["极性分量", "色散分量", "估值方法", "表面能"]

CALC_MODEL_NAME = "OWRK"

_RESULT_PRECISION = 3


def strip_ext(filename):
    """去掉扩展名，作为样品/行的标识"""
    return os.path.splitext(filename)[0]


def to_float(value):
    """把单元格内容转成 float；空值/非数值返回 None。"""
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def empty_row(**overrides):
    """一行空白数据（含内部列）。"""
    row = {key: "" for key in HEADERS}
    row.update(overrides)
    return row


def row_has_content(row):
    """该行是否有任何用户可见内容（用于导出时过滤空行）。"""
    return any(str(row.get(key, "")).strip() for key in EXPORT_HEADERS)


def build_sample_rows(water_data, diiodo_data):
    """
    按「去扩展名后的完整文件名」配对：
      - 文件名一致（去扩展名后）→ 同一样品，合并为一行
      - 否则各自独立成行
    返回 list[dict]，未计算时后 4 列留空。
    """
    samples = {}
    order = []

    def _ensure(key):
        if key not in samples:
            samples[key] = {
                ID_KEY: key,
                "样品": key,
                "水接触角": None,
                "二碘甲烷接触角": None,
            }
            order.append(key)
        return samples[key]

    for item in water_data or []:
        _ensure(strip_ext(item['filename']))['水接触角'] = item['angle']

    for item in diiodo_data or []:
        _ensure(strip_ext(item['filename']))['二碘甲烷接触角'] = item['angle']

    rows = []
    for key in order:
        sample = samples[key]
        row = empty_row(**{ID_KEY: sample[ID_KEY], "样品": sample["样品"]})
        v = sample["水接触角"]
        row["水接触角"] = round(v, _RESULT_PRECISION) if v is not None else ""
        v = sample["二碘甲烷接触角"]
        row["二碘甲烷接触角"] = round(v, _RESULT_PRECISION) if v is not None else ""
        rows.append(row)
    return rows


def calculate_surface_energies(rows):
    """对具备两种角度的行计算 OWRK 表面能。

    就地返回新的行列表，并附带统计信息：

        (new_rows, stats)

    stats 字段：
      * ``paired``   成功计算
      * ``only_water`` / ``only_diiodo``  只填了一种角度
      * ``empty``    完全没有角度数据
      * ``failed``   ``[(样品名, 原因), ...]`` 配对完整但无法求解
    """
    stats = {
        "paired": 0,
        "only_water": 0,
        "only_diiodo": 0,
        "empty": 0,
        "failed": [],
    }

    new_rows = []
    for index, row in enumerate(rows or []):
        theta_w = to_float(row.get("水接触角"))
        theta_d = to_float(row.get("二碘甲烷接触角"))

        new_row = dict(row)

        if theta_w is None and theta_d is None:
            stats["empty"] += 1
            for key in RESULT_KEYS:
                new_row[key] = ""
        elif theta_w is None:
            stats["only_diiodo"] += 1
            for key in RESULT_KEYS:
                new_row[key] = ""
        elif theta_d is None:
            stats["only_water"] += 1
            for key in RESULT_KEYS:
                new_row[key] = ""
        else:
            label = str(new_row.get("样品") or "").strip() or f"第 {index + 1} 行"
            try:
                res = owrk_from_template(theta_w, theta_d)
            except OWRKError as e:
                stats["failed"].append((label, str(e)))
                logger.warning("计算失败：%s -> %s", label, e)
                for key in RESULT_KEYS:
                    new_row[key] = ""
            except Exception:  # noqa: BLE001 - 未预期错误必须暴露，不能静默
                logger.exception("计算 %s 时发生未预期错误", label)
                raise
            else:
                new_row["水接触角"] = round(theta_w, _RESULT_PRECISION)
                new_row["二碘甲烷接触角"] = round(theta_d, _RESULT_PRECISION)
                new_row["极性分量"] = round(res["gamma_p"], _RESULT_PRECISION)
                new_row["色散分量"] = round(res["gamma_d"], _RESULT_PRECISION)
                new_row["估值方法"] = CALC_MODEL_NAME
                new_row["表面能"] = round(res["gamma_total"], _RESULT_PRECISION)
                stats["paired"] += 1

        new_rows.append(new_row)

    return new_rows, stats


def summarize(stats):
    """把统计信息整理成可直接展示给用户的多行文本。"""
    lines = ["表面能计算完成！", "", f"成功配对并计算：{stats['paired']} 个样品"]
    if stats["only_water"]:
        lines.append(f"仅有水滴角（未计算）：{stats['only_water']} 个")
    if stats["only_diiodo"]:
        lines.append(f"仅有二碘甲烷角（未计算）：{stats['only_diiodo']} 个")
    if stats["empty"]:
        lines.append(f"空行（未计算）：{stats['empty']} 个")

    failed = stats.get("failed") or []
    if failed:
        lines.append("")
        lines.append(f"⚠ 计算失败 {len(failed)} 个（无实数解 / 数据非法）：")
        for label, reason in failed[:10]:
            lines.append(f"  · {label}：{reason}")
        if len(failed) > 10:
            lines.append(f"  …… 其余 {len(failed) - 10} 个详见日志")
    return "\n".join(lines)
