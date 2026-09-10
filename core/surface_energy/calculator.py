import math


def owrk_from_template(theta_water_deg, theta_diiodo_deg):
    gamma_1, gamma_1_d, gamma_1_p = 72.8, 21.8, 51.0
    gamma_2, gamma_2_d, gamma_2_p = 50.8, 48.5, 2.3

    theta1 = math.radians(theta_water_deg)
    theta2 = math.radians(theta_diiodo_deg)

    A = 0.5 * gamma_1 * (1 + math.cos(theta1))
    B = 0.5 * gamma_2 * (1 + math.cos(theta2))

    s1d, s1p = math.sqrt(gamma_1_d), math.sqrt(gamma_1_p)
    s2d, s2p = math.sqrt(gamma_2_d), math.sqrt(gamma_2_p)

    den_d = s1d * s2p - s1p * s2d
    den_p = s1p * s2d - s1d * s2p

    sqrt_sd = (A * s2p - B * s1p) / den_d
    sqrt_sp = (A * s2d - B * s1d) / den_p

    if -1e-9 < sqrt_sd < 0:
        sqrt_sd = 0.0
    if -1e-9 < sqrt_sp < 0:
        sqrt_sp = 0.0

    gd = sqrt_sd ** 2
    gp = sqrt_sp ** 2
    return {"gamma_d": gd, "gamma_p": gp, "gamma_total": gd + gp}