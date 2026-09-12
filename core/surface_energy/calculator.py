"""OWRK（Owens-Wendt-Rabel-Kaelble）表面能计算。

模型：
    γ_L (1 + cosθ) / 2 = √(γ_S^d · γ_L^d) + √(γ_S^p · γ_L^p)

用两种已知表面张力及其分量的探测液（水、二碘甲烷）测两个接触角，
即可解出未知固体的 √(γ_S^d) 与 √(γ_S^p) 两个未知量。

已知的物理限制：方程组的解**没有非负保证**。当接触角组合超出模型
适用范围时，解出的 √γ 为负值，此时必须报错而不是静默留空——
实测在「水 20–120° × 二碘甲烷 20–100°」区间内约有 12.6% 的组合
属于这种情况（典型为水接触角 > ~96° 且二碘甲烷角 < 40°）。
"""

import math

# ---------------- 探测液参数（mN/m） ----------------
# 水：γ=72.8，γ^d=21.8，γ^p=51.0
WATER_GAMMA = 72.8
WATER_GAMMA_D = 21.8
WATER_GAMMA_P = 51.0

# 二碘甲烷：γ=50.8，γ^d=48.5，γ^p=2.3
DIIODOMETHANE_GAMMA = 50.8
DIIODOMETHANE_GAMMA_D = 48.5
DIIODOMETHANE_GAMMA_P = 2.3

# 仅用于吸收浮点噪声的容差；超出此范围即为真正的数学域错误
_EPS = 1e-9


class OWRKError(ValueError):
    """OWRK 方程无实数解，或输入超出模型适用范围。"""


def _validate_angle(name, deg):
    try:
        value = float(deg)
    except (TypeError, ValueError) as e:
        raise OWRKError(f"{name}不是有效数值：{deg!r}") from e
    if not math.isfinite(value):
        raise OWRKError(f"{name}不是有限数值：{deg!r}")
    if not 0.0 < value < 180.0:
        raise OWRKError(f"{name}必须在 0° 与 180° 之间（不含端点），当前为 {value:g}°")
    return value


def owrk_from_template(theta_water_deg, theta_diiodo_deg):
    """由水/二碘甲烷接触角计算固体表面能分量。

    返回 ``{"gamma_d": 色散分量, "gamma_p": 极性分量, "gamma_total": 总表面能}``。
    无法求解时抛出 :class:`OWRKError`（携带可直接展示给用户的中文说明）。
    """
    theta1_deg = _validate_angle("水接触角", theta_water_deg)
    theta2_deg = _validate_angle("二碘甲烷接触角", theta_diiodo_deg)

    theta1 = math.radians(theta1_deg)
    theta2 = math.radians(theta2_deg)

    a = 0.5 * WATER_GAMMA * (1 + math.cos(theta1))
    b = 0.5 * DIIODOMETHANE_GAMMA * (1 + math.cos(theta2))

    s1d, s1p = math.sqrt(WATER_GAMMA_D), math.sqrt(WATER_GAMMA_P)
    s2d, s2p = math.sqrt(DIIODOMETHANE_GAMMA_D), math.sqrt(DIIODOMETHANE_GAMMA_P)

    det = s1d * s2p - s1p * s2d            # ≈ -42.65，非奇异
    sqrt_sd = (a * s2p - b * s1p) / det
    sqrt_sp = (a * s2d - b * s1d) / -det
    # 注：-det 即原实现的 den_p，此处直接取负，避免两处各写一遍符号

    if sqrt_sd < -_EPS or sqrt_sp < -_EPS:
        raise OWRKError(
            f"OWRK 方程无实数解（水 {theta1_deg:g}°，二碘甲烷 {theta2_deg:g}°）："
            "该角度组合超出 OWRK 模型适用范围。"
            "常见原因是水接触角偏大而二碘甲烷接触角偏小，请核对数据；"
            "也请确认两种角度没有填反。"
        )

    # 仅吸收浮点噪声（|值| < 1e-9 的极小负值理论上应为 0）
    sqrt_sd = max(sqrt_sd, 0.0)
    sqrt_sp = max(sqrt_sp, 0.0)

    gamma_d = sqrt_sd ** 2
    gamma_p = sqrt_sp ** 2
    return {
        "gamma_d": gamma_d,
        "gamma_p": gamma_p,
        "gamma_total": gamma_d + gamma_p,
    }
