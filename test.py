import math

# 液体表面能参数 (mN/m, 20°C)
LIQUIDS = {
    "water": {
        "gamma": 72.8,   # 总表面张力
        "d": 21.8,       # 色散分量
        "p": 51.0        # 极性分量
    },
    "diiodomethane": {
        "gamma": 50.8,
        "d": 48.5,
        "p": 2.3         # 非极性液体
    }
}

def owrk_two_liquid(theta_water_deg, theta_diiodo_deg):
    """
    使用 OWRK 二液法计算固体表面能。

    参数:
        theta_water_deg (float): 水在固体上的接触角 (度)
        theta_diiodo_deg (float): 二碘甲烷在固体上的接触角 (度)

    返回:
        dict: 包含 'gamma_d' (色散), 'gamma_p' (极性), 'gamma_total' (总表面能) 的字典
    """
    # 角度转弧度
    theta_w = math.radians(theta_water_deg)
    theta_d = math.radians(theta_diiodo_deg)

    # 提取液体参数
    w = LIQUIDS["water"]
    d = LIQUIDS["diiodomethane"]

    # 1. 由二碘甲烷 (非极性, p=0) 直接计算固体色散分量 γ_d
    # 公式: (1 + cosθ_d) * γ_L_d = 2 * sqrt(γ_S_d * γ_L_d_d)
    # 其中 γ_L_d 是二碘甲烷总表面张力，γ_L_d_d 是其色散分量 (等于总表面张力)
    gamma_L_d = d["gamma"]
    gamma_L_d_d = d["d"]  # 非极性液体，色散=总表面张力
    cos_d = math.cos(theta_d)
    # 解方程: sqrt(γ_S_d) = (1 + cosθ_d) * γ_L_d / (2 * sqrt(γ_L_d_d))
    sqrt_gamma_S_d = (1 + cos_d) * gamma_L_d / (2 * math.sqrt(gamma_L_d_d))
    gamma_S_d = sqrt_gamma_S_d ** 2

    # 2. 由水方程计算极性分量 γ_p
    # 公式: (1 + cosθ_w) * γ_L_w = 2 * ( sqrt(γ_S_d * γ_L_w_d) + sqrt(γ_S_p * γ_L_w_p) )
    gamma_L_w = w["gamma"]
    gamma_L_w_d = w["d"]
    gamma_L_w_p = w["p"]

    cos_w = math.cos(theta_w)
    # 左侧值
    left = (1 + cos_w) * gamma_L_w
    # 已知项 (色散贡献)
    known = 2 * math.sqrt(gamma_S_d * gamma_L_w_d)
    # 剩余部分 = 2 * sqrt(γ_S_p * γ_L_w_p)
    remaining = left - known
    # 若剩余为负（可能因测量误差），置为0
    if remaining < 0:
        gamma_S_p = 0.0
    else:
        # sqrt(γ_S_p) = remaining / (2 * sqrt(γ_L_w_p))
        gamma_S_p = (remaining / (2 * math.sqrt(gamma_L_w_p))) ** 2

    # 总表面能
    gamma_total = gamma_S_d + gamma_S_p

    return {
        "gamma_d": gamma_S_d,
        "gamma_p": gamma_S_p,
        "gamma_total": gamma_total
    }

# ================== 示例使用 ==================
if __name__ == "__main__":
    # 用户提供的示例数据
    theta_water = 63.126      # 度
    theta_diiodo = 49.307     # 度

    result = owrk_two_liquid(theta_water, theta_diiodo)
    print(f"水接触角: {theta_water}°")
    print(f"二碘甲烷接触角: {theta_diiodo}°")
    print(f"色散分量 γᵈ: {result['gamma_d']:.3f} mN/m")
    print(f"极性分量 γᵖ: {result['gamma_p']:.3f} mN/m")
    print(f"总表面能 γ: {result['gamma_total']:.3f} mN/m")