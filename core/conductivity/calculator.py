def compute_conductivity(resistance_ohm, length_cm, area_cm2):
    """
    根据电阻 + 尺寸计算电阻率和电导率。
    ρ = R·A/L   (Ω·cm)
    σ = 1/ρ     (S/cm)
    """
    if resistance_ohm <= 0 or length_cm <= 0 or area_cm2 <= 0:
        raise ValueError("所有参数必须为正数")
    rho = resistance_ohm * area_cm2 / length_cm
    sigma = 1.0 / rho
    return {"rho": rho, "sigma": sigma}