# app/services/plots.py
from __future__ import annotations
import os
from datetime import datetime
from typing import Iterable, Tuple

import matplotlib
matplotlib.use("Agg")  # Render sin ventana
import matplotlib.pyplot as plt

# === Salida: ecobot/out ===
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.join(ROOT_DIR, "out")
os.makedirs(OUT_DIR, exist_ok=True)

def _out_path(name: str) -> str:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    return os.path.abspath(os.path.join(OUT_DIR, f"{name}-{ts}.png"))

def _price_grid_from_candidates(cands: list[float], fallback_max: float = 100.0) -> Tuple[float, float]:
    pos = [x for x in cands if x is not None and x == x and x > 0]
    if not pos:
        return (0.0, fallback_max)
    pmax = max(pos) * 1.1
    if pmax < 10:
        pmax = 10.0
    return (0.0, pmax)

def _plot_axes_common(title: str):
    plt.xlabel("Cantidad (Q)")
    plt.ylabel("Precio (P)")
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

# ============================
#   DEMANDA y OFERTA SIMPLES
# ============================

def plot_demand_curve(a_d: float = 100.0, b_d: float = -1.0) -> str:
    if b_d >= 0:
        raise ValueError("Para DEMANDA usá pendiente negativa: b_d < 0.")

    p_qd0 = -a_d / b_d if b_d != 0 else None
    Pmin, Pmax = _price_grid_from_candidates([p_qd0, a_d])
    P = [Pmin + (Pmax - Pmin) * i / 300 for i in range(301)]
    Qd = [a_d + b_d * p for p in P]

    plt.figure()
    plt.plot(Qd, P, label="Demanda (Qd)")
    _plot_axes_common("Curva de Demanda")
    plt.legend()

    path = _out_path("demanda")
    plt.savefig(path, dpi=160)
    plt.close()
    return path

def plot_supply_curve(a_s: float = 10.0, b_s: float = 1.0) -> str:
    if b_s <= 0:
        raise ValueError("Para OFERTA usá pendiente positiva: b_s > 0.")

    p_qs0 = -a_s / b_s if b_s != 0 else None
    Pmin, Pmax = _price_grid_from_candidates([p_qs0, a_s])
    P = [Pmin + (Pmax - Pmin) * i / 300 for i in range(301)]
    Qs = [a_s + b_s * p for p in P]

    plt.figure()
    plt.plot(Qs, P, label="Oferta (Qs)")
    _plot_axes_common("Curva de Oferta")
    plt.legend()

    path = _out_path("oferta")
    plt.savefig(path, dpi=160)
    plt.close()
    return path

# ============================
#    OFERTA Y DEMANDA JUNTAS
# ============================

def plot_supply_demand(a_d: float = 100.0, b_d: float = -1.0,
                       a_s: float = 10.0, b_s: float = 1.0) -> str:
    if b_d >= 0:
        raise ValueError("b_d debe ser < 0 para DEMANDA.")
    if b_s <= 0:
        raise ValueError("b_s debe ser > 0 para OFERTA.")

    denom = (b_s - b_d)
    p_eq = (a_d - a_s) / denom if denom != 0 else None
    q_eq = (a_d + b_d * p_eq) if p_eq is not None else None

    p_qd0 = -a_d / b_d if b_d != 0 else None
    p_qs0 = -a_s / b_s if b_s != 0 else None

    Pmin, Pmax = _price_grid_from_candidates([p_qd0, p_qs0, p_eq, a_d, a_s])
    P = [Pmin + (Pmax - Pmin) * i / 400 for i in range(401)]
    Qd = [a_d + b_d * p for p in P]
    Qs = [a_s + b_s * p for p in P]

    plt.figure()
    plt.plot(Qd, P, label="Demanda (Qd)")
    plt.plot(Qs, P, label="Oferta (Qs)")

    if (p_eq is not None and q_eq is not None and Pmin <= p_eq <= Pmax):
        q_min, q_max = min(Qd + Qs), max(Qd + Qs)
        margin = (q_max - q_min) * 0.05
        if (q_min - margin) <= q_eq <= (q_max + margin):
            plt.scatter([q_eq], [p_eq], marker="o", zorder=5)
            plt.annotate(f"Equilibrio\n(Q*={q_eq:.1f}, P*={p_eq:.1f})",
                         (q_eq, p_eq),
                         xytext=(q_eq * 1.05 if q_eq >= 0 else q_eq - 1.0,
                                 p_eq * 1.05 if p_eq >= 0 else p_eq + 1.0),
                         arrowprops=dict(arrowstyle="->", lw=1))

    _plot_axes_common("Oferta y Demanda")
    plt.legend()

    path = _out_path("oferta_demanda")
    plt.savefig(path, dpi=160)
    plt.close()
    return path

# ============================
#        COSTOS y SERIES
# ============================

def plot_cost_curves(fc: float = 50.0, c: float = 5.0, d: float = 1.0, qmax: int = 100) -> str:
    if qmax < 1:
        qmax = 50
    Q = list(range(1, qmax + 1))
    CT = [fc + c*q + d*(q**2) for q in Q]
    CMg = [c + 2*d*q for q in Q]
    CMe = [CT[i] / Q[i] for i in range(len(Q))]

    plt.figure()
    plt.plot(Q, CMg, label="CMg")
    plt.plot(Q, CMe, label="CMe")
    _plot_axes_common("Curvas de costo: CMg y CMe")
    plt.legend()

    path = _out_path("costos")
    plt.savefig(path, dpi=160)
    plt.close()
    return path

def plot_series(y: Iterable[float], title: str = "Serie", ylabel: str = "", xlabel: str = "Índice") -> str:
    y = list(y)
    if len(y) < 2:
        raise ValueError("Necesito al menos 2 puntos para graficar la serie.")
    x = list(range(1, len(y) + 1))
    plt.figure()
    plt.plot(x, y, marker="o")
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    path = _out_path("serie")
    plt.savefig(path, dpi=160)
    plt.close()
    return path
