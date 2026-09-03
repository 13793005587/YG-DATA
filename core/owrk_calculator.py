import math

def owrk_from_template(theta_water_deg, theta_diiodo_deg):
    """
    依据 Excel 模板 “Owens-Wendt表面自由能计算模板.xlsx” 的公式与参数，
    计算固体表面能的色散分量、极性分量和总表面能。

    参数：
        theta_water_deg (float): 水在固体上的接触角（度）
        theta_diiodo_deg (float): 二碘甲烷在固体上的接触角（度）

    返回：
        dict: 包含 'gamma_d' (色散), 'gamma_p' (极性), 'gamma_total' (总表面能) 的字典
    """
    # ---------- 模板中固定的液体参数 (20°C) ----------
    # 水 (下标1)
    gamma_1 = 72.8      # 总表面张力
    gamma_1_d = 21.8    # 色散分量
    gamma_1_p = 51.0    # 极性分量

    # 二碘甲烷 (下标2)
    gamma_2 = 50.8      # 总表面张力
    gamma_2_d = 48.5    # 色散分量 (模板中非50.8)
    gamma_2_p = 2.3     # 极性分量 (模板中非0)

    # ---------- 角度转弧度 ----------
    theta1 = math.radians(theta_water_deg)
    theta2 = math.radians(theta_diiodo_deg)

    # ---------- 中间变量 A, B ----------
    # A = γ₁(1+cosθ₁)/2
    A = 0.5 * gamma_1 * (1 + math.cos(theta1))
    # B = γ₂(1+cosθ₂)/2
    B = 0.5 * gamma_2 * (1 + math.cos(theta2))

    # ---------- 计算 √γₛᵈ 和 √γₛᵖ (按照模板公式) ----------
    # 模板公式：
    # √γₛᵈ = (A·√γ₂ᵖ − B·√γ₁ᵖ) / (√γ₁ᵈ·√γ₂ᵖ − √γ₁ᵖ·√γ₂ᵈ)
    # √γₛᵖ = (A·√γ₂ᵈ − B·√γ₁ᵈ) / (√γ₁ᵖ·√γ₂ᵈ − √γ₁ᵈ·√γ₂ᵖ)

    sqrt_gamma_1_d = math.sqrt(gamma_1_d)
    sqrt_gamma_1_p = math.sqrt(gamma_1_p)
    sqrt_gamma_2_d = math.sqrt(gamma_2_d)
    sqrt_gamma_2_p = math.sqrt(gamma_2_p)

    denominator_d = sqrt_gamma_1_d * sqrt_gamma_2_p - sqrt_gamma_1_p * sqrt_gamma_2_d
    denominator_p = sqrt_gamma_1_p * sqrt_gamma_2_d - sqrt_gamma_1_d * sqrt_gamma_2_p

    sqrt_gamma_s_d = (A * sqrt_gamma_2_p - B * sqrt_gamma_1_p) / denominator_d
    sqrt_gamma_s_p = (A * sqrt_gamma_2_d - B * sqrt_gamma_1_d) / denominator_p

    # 由于数值原因可能为微小负数，取绝对值或置0
    if sqrt_gamma_s_d < 0 and sqrt_gamma_s_d > -1e-9:
        sqrt_gamma_s_d = 0.0
    if sqrt_gamma_s_p < 0 and sqrt_gamma_s_p > -1e-9:
        sqrt_gamma_s_p = 0.0

    gamma_s_d = sqrt_gamma_s_d ** 2
    gamma_s_p = sqrt_gamma_s_p ** 2
    gamma_total = gamma_s_d + gamma_s_p

    return {
        "gamma_d": gamma_s_d,
        "gamma_p": gamma_s_p,
        "gamma_total": gamma_total
    }

# ================== 使用示例 ==================
if __name__ == "__main__":
    # 你的实测角度
    theta_w = 63.430
    theta_d = 50.889

    result = owrk_from_template(theta_w, theta_d)
    print(f"水接触角: {theta_w}°")
    print(f"二碘甲烷接触角: {theta_d}°")
    print(f"色散分量 γᵈ: {result['gamma_d']:.3f} mN/m")
    print(f"极性分量 γᵖ: {result['gamma_p']:.3f} mN/m")
    print(f"总表面能 γ: {result['gamma_total']:.3f} mN/m")