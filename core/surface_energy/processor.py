import os

from core.surface_energy.calculator import owrk_from_template


HEADERS = ["样品", "水接触角", "二碘甲烷接触角", "极性分量", "色散分量", "估值方法", "表面能"]


def _strip_ext(filename):
    """去掉扩展名，作为样品标识"""
    return os.path.splitext(filename)[0]


def build_sample_rows(water_data, diiodo_data):
    """
    按“去扩展名后的完整文件名”配对：
      - 文件名一致（去扩展名后）→ 同一样品，合并为一行
      - 否则各自独立成行
    返回 list[dict]，每行含 7 个字段；未计算时后 4 列留空。
    """
    samples = {}
    order = []

    def _ensure(key):
        if key not in samples:
            samples[key] = {
                "样品": key,
                "水接触角": None,
                "二碘甲烷接触角": None,
            }
            order.append(key)
        return samples[key]

    for w in water_data:
        _ensure(_strip_ext(w['filename']))['水接触角'] = w['angle']

    for d in diiodo_data:
        _ensure(_strip_ext(d['filename']))['二碘甲烷接触角'] = d['angle']

    rows = []
    for key in order:
        s = samples[key]
        rows.append({
            "样品": s["样品"],
            "水接触角": round(s["水接触角"], 3) if s["水接触角"] is not None else "",
            "二碘甲烷接触角": round(s["二碘甲烷接触角"], 3) if s["二碘甲烷接触角"] is not None else "",
            "极性分量": "",
            "色散分量": "",
            "估值方法": "",
            "表面能": "",
        })
    return rows


def calculate_surface_energies(water_data, diiodo_data):
    """
    在 build_sample_rows 的基础上，对同时具备两个角度的样品计算 OWRK 表面能。
    无法计算的样品仍保留在结果中，相关列留空。
    返回 list[dict]。
    """
    rows = build_sample_rows(water_data, diiodo_data)
    for row in rows:
        theta_w = row["水接触角"]
        theta_d = row["二碘甲烷接触角"]
        if theta_w == "" or theta_d == "":
            continue
        try:
            res = owrk_from_template(theta_w, theta_d)
            row["极性分量"] = round(res["gamma_p"], 3)
            row["色散分量"] = round(res["gamma_d"], 3)
            row["估值方法"] = "OWRK"
            row["表面能"] = round(res["gamma_total"], 3)
        except Exception as e:
            print(f"[ERR] 计算 {row['样品']} 失败: {e}")
    return rows