"""导电性计算与展示常量。

ρ = R · A / L   (Ω·cm)
σ = 1 / ρ       (S/cm)
"""

# 界面表格与导出的列（单一来源）
HEADERS = ["样品名称", "电阻 (Ω)", "长度 (cm)", "横截面积 (cm²)",
           "电阻率 (Ω·cm)", "电导率 (S/cm)"]

# 输入/输出保留位数。界面与导出共用同一套格式，避免「看到的」和
# 「导出的」精度不一致。
INPUT_PRECISION = 4
DISPLAY_PRECISION = 6


def fmt(value):
    """统一格式化数值：输入量用定点，结果量用科学计数法。"""
    if value is None:
        return ""
    if value == 0:
        return "0"
    if abs(value) < 1e-3 or abs(value) >= 1e5:
        return f"{value:.{DISPLAY_PRECISION}e}"
    return f"{value:.{INPUT_PRECISION}f}"


def compute_conductivity(resistance_ohm, length_cm, area_cm2):
    """
    根据电阻 + 尺寸计算电阻率和电导率。
    ρ = R·A/L   (Ω·cm)
    σ = 1/ρ     (S/cm)

    参数非法时抛出 ValueError（消息可直接展示给用户）。
    """
    try:
        r = float(resistance_ohm)
        length = float(length_cm)
        area = float(area_cm2)
    except (TypeError, ValueError) as e:
        raise ValueError("电阻、长度、横截面积必须是有效数值") from e

    labels = (("电阻 R", r), ("长度 L", length), ("横截面积 A", area))
    for name, value in labels:
        if value != value or value in (float("inf"), float("-inf")):
            raise ValueError(f"{name} 不是有限数值")
        if value <= 0:
            raise ValueError(f"{name} 必须大于 0（当前为 {value:g}）")

    rho = r * area / length
    sigma = 1.0 / rho
    return {"rho": rho, "sigma": sigma}
