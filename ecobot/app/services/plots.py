# app/services/plots.py
import os
from datetime import datetime
from typing import Iterable, Tuple

import matplotlib
matplotlib.use("Agg")  # Render sin ventana (ideal consola/servidor)
import matplotlib.pyplot as plt

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "out")
os.makedirs(OUT_DIR, exist_ok=True)

def _out_path(name: str) -> str:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    fname = f"{name}-{ts}.png"
    # normaliza path final
    return os.path.abspath(os.path.join(OUT_DIR, fname))

def plot_supply_demand(a_d: float = 100, b_d: float = -1.0, a_s: float = 10, b_s: float = 1.0) -> str:
    """
    Demanda: Qd = a_d + b_d * P   (b_d < 0)
    Oferta : Qs = a_s + b_s * P   (b_s > 0)
    Resuelve equilibrio y grafica.
    """
    # Evitar slopes inválidos
    if b_d >= 0 or b_s <= 0:
        raise ValueError("Usá b_d < 0 para demanda y b_s > 0 para oferta.")

    # Equilibrio: a_d + b_d*P* = a_s + b_s*P*
    p_eq = (a_d - a_s) / (b_s - b_d)
    q_eq = a_d + b_d * p_eq

    # Rango de precios para graficar
    pmin = max(0, p_eq * 0.2)
    pmax = p_eq * 1.8 if p_eq > 0 else 100
    P = [pmin + (pmax - pmin) * i / 100 for i in range(101)]
    Qd = [a_d + b_d * p for p in P]
    Qs = [a_s + b_s * p for p in P]

    plt.figure()
    plt.plot(Qd, P, label="Demanda (Qd)")
    plt.plot(Qs, P, label="Oferta (Qs)")
    plt.scatter([q_eq], [p_eq], marker="o")
    plt.annotate(f"Equilibrio\n(Q*={q_eq:.1f}, P*={p_eq:.1f})", (q_eq, p_eq),
                 xytext=(q_eq*1.05, p_eq*1.05), arrowprops=dict(arrowstyle="->", lw=1))
    plt.xlabel("Cantidad (Q)")
    plt.ylabel("Precio (P)")
    plt.title("Oferta y Demanda")
    plt.legend()
    plt.grid(True, alpha=0.3)
    path = _out_path("oferta_demanda")
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()
    return path

def plot_cost_curves(fc: float = 50, c: float = 5, d: float = 1.0, qmax: int = 100) -> str:
    """
    CT(Q) = FC + c*Q + d*Q^2  => CMg = dCT/dQ = c + 2dQ
    Grafica CMg y CMe (= CT/Q).
    """
    Q = [q for q in range(1, qmax + 1)]
    CT = [fc + c*q + d*(q**2) for q in Q]
    CMg = [c + 2*d*q for q in Q]
    CMe = [CT[i]/Q[i] for i in range(len(Q))]

    plt.figure()
    plt.plot(Q, CMg, label="CMg")
    plt.plot(Q, CMe, label="CMe")
    plt.xlabel("Cantidad (Q)")
    plt.ylabel("Costo")
    plt.title("Curvas de costo: CMg y CMe")
    plt.legend()
    plt.grid(True, alpha=0.3)
    path = _out_path("costos")
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()
    return path

def plot_series(y: Iterable[float], title: str = "Serie", ylabel: str = "", xlabel: str = "Índice") -> str:
    y = list(y)
    x = list(range(1, len(y) + 1))
    plt.figure()
    plt.plot(x, y, marker="o")
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True, alpha=0.3)
    path = _out_path("serie")
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()
    return path

def plot_demand_curve(a_d: float = 100, b_d: float = -1.0) -> str:
    """
    Demanda: Qd = a_d + b_d * P   (b_d < 0)
    Grafica solo la curva de demanda.
    """
    if b_d >= 0:
        raise ValueError("Para demanda usá b_d < 0.")
    # rango de P
    pmin, pmax = 0, max(100, a_d / max(1e-6, -b_d) * 1.2)
    P = [pmin + (pmax - pmin) * i / 100 for i in range(101)]
    Qd = [a_d + b_d * p for p in P]

    plt.figure()
    plt.plot(Qd, P, label="Demanda (Qd)")
    plt.xlabel("Cantidad (Q)")
    plt.ylabel("Precio (P)")
    plt.title("Curva de Demanda")
    plt.legend()
    plt.grid(True, alpha=0.3)
    path = _out_path("demanda")
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()
    return path

def plot_supply_curve(a_s: float = 10, b_s: float = 1.0) -> str:
    """
    Oferta: Qs = a_s + b_s * P   (b_s > 0)
    Grafica solo la curva de oferta.
    """
    if b_s <= 0:
        raise ValueError("Para oferta usá b_s > 0.")
    # rango de P
    pmin, pmax = 0, 100
    P = [pmin + (pmax - pmin) * i / 100 for i in range(101)]
    Qs = [a_s + b_s * p for p in P]

    plt.figure()
    plt.plot(Qs, P, label="Oferta (Qs)")
    plt.xlabel("Cantidad (Q)")
    plt.ylabel("Precio (P)")
    plt.title("Curva de Oferta")
    plt.legend()
    plt.grid(True, alpha=0.3)
    path = _out_path("oferta")
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()
    return path
