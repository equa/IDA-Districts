#half-space image-source solution from Carslaw & Jaeger
#Für den Halbraum (Erdreich mit Oberfläche bei kannst du die Methode der Spiegelquellen (method of images) verwenden, um den Einfluss der Oberfläche zu berücksichtigen:

#Für konstante Oberflächentemperatur (Dirichlet) spiegelt man mit umgekehrtem Vorzeichen.

#Durch Überlagerung der realen Quelle und ihrer Spiegelquelle(n) erhältst du einen Korrekturterm, der die Tiefen explizit berücksichtigt. Für einfache Randbedingungen (adiabatisch, Dirichlet) gibt es geschlossene Ausdrücke in Lehrbüchern (Greensche Funktionen für Linienquellen im Halbraum).

#literature:
#Conduction of Heat in Solids: H. S. Carslaw & J. C. Jaeger (Oxford, 2nd ed. 1959)
#Methods of Heat Transfer Analysis of Buried Pipes in District Heating and Cooling Systems	Jianguang Yi, Applied Engineering (2018) 

# Bsp: 4 Rohre mit variablen Rohrinnendurchmessern, Wandstärken und Isolierungen (nur Halbraum, T_fluid)

import numpy as np
import pandas as pd
from math import pi

# -------------------- Eingangsparameter --------------------
T_fluid = 80.0        # °C
T_surface = 10.0      # °C (Luft/Oberfläche, Dirichlet)
# Rohrpositionen (vier Rohre in einer Reihe)
dx = 0.30
x_positions = np.array([0.0, dx, 2*dx, 3*dx])
# Fluid / Konvektion
velocity = 1.0
rho = 971.8
mu = 3.55e-4
k_fluid = 0.667
cp = 4182

# -------------------- Variationen (benutzerdefiniert) --------------------
# Rohrinnendurchmesser [m]
r_inner_arr = np.array([0.018, 0.02, 0.022, 0.02])  # verschiedene Innendurchmesser
# Rohrwandstärken [m]
wall_thicknesses = np.array([0.004, 0.005, 0.006, 0.005])
# Isolierstärken [m]
ins_thicknesses  = np.array([0.02, 0.025, 0.03, 0.02])
# Materialeigenschaften
k_pipe = 45.0
k_ins = 0.035
k_soil = 1.5

# Berechne Außenradien
r_outer_arr = r_inner_arr + wall_thicknesses
r_ins_arr = r_outer_arr + ins_thicknesses
D_h_arr = 2 * r_inner_arr

# Fälle (Tiefen)
cases = {
    "caseA": [1.0, 1.0, 1.0, 1.0],
    "caseB": [0.8, 1.0, 1.2, 1.0]
}

def compute_G_halfspace_positions(x_pos, z_vals, r_eff_arr, k_soil):
    n = len(z_vals)
    G = np.zeros((n,n))
    for i in range(n):
        for j in range(n):
            if i == j:
                G[i,i] = (1.0 / (2*pi*k_soil)) * np.log(2.0 * z_vals[i] / r_eff_arr[i])
            else:
                dxij = x_pos[i] - x_pos[j]
                s_ij = np.sqrt(dxij**2 + (z_vals[i] - z_vals[j])**2) #distance mirror space
                s_ij_prime = np.sqrt(dxij**2 + (z_vals[i] + z_vals[j])**2) #direct distance
                G[i,j] = (1.0 / (2*pi*k_soil)) * np.log(s_ij_prime / s_ij)
    return G

def inner_convective_h(velocity, D_h, rho, mu, k_fluid, cp):
    Re = rho * velocity * D_h / mu
    Pr = cp * mu / k_fluid
    n = 0.4
    Nu = 0.023 * Re**0.8 * Pr**n
    h = Nu * k_fluid / D_h
    return Re, Pr, Nu, h

rows = []

for case_name, z_vals in cases.items():
    z_vals = np.array(z_vals)
    # heat transfer coefficient water/pipe
    h_arr = np.zeros_like(D_h_arr)
    for i in range(len(D_h_arr)):
        _, _, _, h_arr[i] = inner_convective_h(velocity, D_h_arr[i], rho, mu, k_fluid, cp)
    R_conv_in_arr = 1.0 / (h_arr * (2 * pi * r_inner_arr))
    R_wall_arr = np.log(r_outer_arr / r_inner_arr) / (2 * pi * k_pipe)
    R_ins_arr = np.log(r_ins_arr / r_outer_arr) / (2 * pi * k_ins)
    R_series_internal_arr = R_conv_in_arr + R_wall_arr + R_ins_arr
    print(R_series_internal_arr)
    print(np.diag(R_series_internal_arr))

    # G-Matrix Halbraum
    G_half = compute_G_halfspace_positions(x_positions, z_vals, r_ins_arr, k_soil)
    deltaT_vec = np.ones(len(z_vals)) * (T_fluid - T_surface)
    A = G_half + np.diag(R_series_internal_arr)
    print(A)
    print(deltaT_vec)
    q = np.linalg.solve(A, deltaT_vec)
    print(q)
    ödflgk

    T_surface_pipe = T_fluid - q * R_series_internal_arr
    T_pipewall_after_conv = T_fluid - q * R_conv_in_arr

    for i in range(len(z_vals)):
        rows.append({
            "case": case_name,
            "pipe": i+1,
            "x [m]": x_positions[i],
            "z [m]": z_vals[i],
            "r_inner [m]": r_inner_arr[i],
            "wall_thickness [m]": wall_thicknesses[i],
            "ins_thickness [m]": ins_thicknesses[i],
            "r_outer [m]": r_outer_arr[i],
            "r_ins [m]": r_ins_arr[i],
            "G_half_self [K·m/W]": G_half[i,i],
            "G_half_other_sum [K·m/W]": G_half[i,:].sum() - G_half[i,i],
            "R_conv_in [K·m/W]": R_conv_in_arr[i],
            "R_wall [K·m/W]": R_wall_arr[i],
            "R_ins [K·m/W]": R_ins_arr[i],
            "R_series_internal [K·m/W]": R_series_internal_arr[i],
            "q_half_total [W/m]": q[i],
            "T_surface_pipe [°C]": T_surface_pipe[i],
            "T_pipewall_after_conv [°C]": T_pipewall_after_conv[i]
        })
    #print(rows)


