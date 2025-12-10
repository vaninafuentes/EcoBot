# app/services/plots.py
from __future__ import annotations

"""
Módulo de generación de gráficos para EcoBot.

Produce PNGs con:
- Curva de demanda
- Curva de oferta
- Curvas de oferta y demanda juntas (con equilibrio)
- Curvas de costo (CMg y CMe)
- Serie temporal genérica

Los archivos se guardan en la carpeta 'out/' del proyecto
y se devuelve la ruta absoluta del archivo generado.
"""

import os
from datetime import datetime
from typing import Iterable, Tuple, List

import matplotlib

# Usamos backend "Agg" para renderizar sin ventana gráfica (modo servidor)
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


# === Directorio de salida: ecobot/out ===
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.join(ROOT_DIR, "out")
os.makedirs(OUT_DIR, exist_ok=True)


def _build_output_path(base_name: str) -> str:
    """
    Construye una ruta de salida única usando timestamp,
    por ejemplo: out/demanda-20251209-193000.png
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    file_name = f"{base_name}-{timestamp}.png"
    return os.path.abspath(os.path.join(OUT_DIR, file_name))


def _price_grid_from_candidates(
    candidate_prices: List[float],
    fallback_max: float = 100.0,
) -> Tuple[float, float]:
    """
    A partir de una lista de posibles precios (positivos), arma un rango [Pmin, Pmax]
    razonable para el eje de precios.

    - Ignora valores None, NaN y <= 0.
    - Si no hay valores válidos, usa [0, fallback_max].
    - Si el máximo es muy chico, asegura al menos 10 en Pmax.
    """
    positive_prices = [
        price
        for price in candidate_prices
        if price is not None and price == price and price > 0  # price == price -> evita NaN
    ]

    if not positive_prices:
        return (0.0, fallback_max)

    max_price = max(positive_prices) * 1.1  # pequeño margen hacia arriba
    if max_price < 10:
        max_price = 10.0

    return (0.0, max_price)


def _configure_common_axes(title: str) -> None:
    """
    Configura etiquetas, título y grilla para gráficos
    de precio-cantidad.
    """
    plt.xlabel("Cantidad (Q)")
    plt.ylabel("Precio (P)")
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()


# ============================
#   DEMANDA y OFERTA SIMPLES
# ============================

def plot_demand_curve(a_d: float = 100.0, b_d: float = -1.0) -> str:
    """
    Genera un gráfico de curva de DEMANDA lineal:

        Qd(P) = a_d + b_d * P

    Requiere pendiente negativa (b_d < 0).
    Devuelve la ruta del archivo PNG generado.
    """
    if b_d >= 0:
        raise ValueError("Para DEMANDA usá pendiente negativa: b_d < 0.")

    # Precio donde Qd = 0, si existe
    price_where_qd_zero = -a_d / b_d if b_d != 0 else None

    price_min, price_max = _price_grid_from_candidates(
        [price_where_qd_zero, a_d]
    )

    prices = [
        price_min + (price_max - price_min) * i / 300 for i in range(301)
    ]
    demand_quantities = [a_d + b_d * price for price in prices]

    plt.figure()
    plt.plot(demand_quantities, prices, label="Demanda (Qd)")
    _configure_common_axes("Curva de Demanda")
    plt.legend()

    output_path = _build_output_path("demanda")
    plt.savefig(output_path, dpi=160)
    plt.close()
    return output_path


def plot_supply_curve(a_s: float = 10.0, b_s: float = 1.0) -> str:
    """
    Genera un gráfico de curva de OFERTA lineal:

        Qs(P) = a_s + b_s * P

    Requiere pendiente positiva (b_s > 0).
    Devuelve la ruta del archivo PNG generado.
    """
    if b_s <= 0:
        raise ValueError("Para OFERTA usá pendiente positiva: b_s > 0.")

    price_where_qs_zero = -a_s / b_s if b_s != 0 else None

    price_min, price_max = _price_grid_from_candidates(
        [price_where_qs_zero, a_s]
    )

    prices = [
        price_min + (price_max - price_min) * i / 300 for i in range(301)
    ]
    supply_quantities = [a_s + b_s * price for price in prices]

    plt.figure()
    plt.plot(supply_quantities, prices, label="Oferta (Qs)")
    _configure_common_axes("Curva de Oferta")
    plt.legend()

    output_path = _build_output_path("oferta")
    plt.savefig(output_path, dpi=160)
    plt.close()
    return output_path


# ============================
#    OFERTA Y DEMANDA JUNTAS
# ============================

def plot_supply_demand(
    a_d: float = 100.0,
    b_d: float = -1.0,
    a_s: float = 10.0,
    b_s: float = 1.0,
) -> str:
    """
    Genera un gráfico con OFERTA y DEMANDA lineales:

        Qd(P) = a_d + b_d * P
        Qs(P) = a_s + b_s * P

    Calcula el punto de equilibrio (si existe) y lo marca en el gráfico.
    Devuelve la ruta del archivo PNG generado.
    """
    if b_d >= 0:
        raise ValueError("b_d debe ser < 0 para DEMANDA.")
    if b_s <= 0:
        raise ValueError("b_s debe ser > 0 para OFERTA.")

    denominator = (b_s - b_d)
    price_equilibrium = (a_d - a_s) / denominator if denominator != 0 else None
    quantity_equilibrium = (
        a_d + b_d * price_equilibrium
        if price_equilibrium is not None
        else None
    )

    price_where_qd_zero = -a_d / b_d if b_d != 0 else None
    price_where_qs_zero = -a_s / b_s if b_s != 0 else None

    price_min, price_max = _price_grid_from_candidates(
        [
            price_where_qd_zero,
            price_where_qs_zero,
            price_equilibrium,
            a_d,
            a_s,
        ]
    )

    prices = [
        price_min + (price_max - price_min) * i / 400 for i in range(401)
    ]
    demand_quantities = [a_d + b_d * price for price in prices]
    supply_quantities = [a_s + b_s * price for price in prices]

    plt.figure()
    plt.plot(demand_quantities, prices, label="Demanda (Qd)")
    plt.plot(supply_quantities, prices, label="Oferta (Qs)")

    # Marcamos el equilibrio si está dentro del rango
    if (
        price_equilibrium is not None
        and quantity_equilibrium is not None
        and price_min <= price_equilibrium <= price_max
    ):
        quantity_min = min(demand_quantities + supply_quantities)
        quantity_max = max(demand_quantities + supply_quantities)
        margin = (quantity_max - quantity_min) * 0.05

        if (quantity_min - margin) <= quantity_equilibrium <= (quantity_max + margin):
            plt.scatter(
                [quantity_equilibrium],
                [price_equilibrium],
                marker="o",
                zorder=5,
            )
            plt.annotate(
                f"Equilibrio\n(Q*={quantity_equilibrium:.1f}, P*={price_equilibrium:.1f})",
                (quantity_equilibrium, price_equilibrium),
                xytext=(
                    quantity_equilibrium * 1.05
                    if quantity_equilibrium >= 0
                    else quantity_equilibrium - 1.0,
                    price_equilibrium * 1.05
                    if price_equilibrium >= 0
                    else price_equilibrium + 1.0,
                ),
                arrowprops={"arrowstyle": "->", "lw": 1},
            )

    _configure_common_axes("Oferta y Demanda")
    plt.legend()

    output_path = _build_output_path("oferta_demanda")
    plt.savefig(output_path, dpi=160)
    plt.close()
    return output_path


# ============================
#        COSTOS y SERIES
# ============================

def plot_cost_curves(
    fixed_cost: float = 50.0,
    linear_cost: float = 5.0,
    quadratic_cost: float = 1.0,
    max_quantity: int = 100,
) -> str:
    """
    Genera un gráfico con:
      - Costo Marginal (CMg)
      - Costo Medio (CMe)

    Asume una función de costo total:

        CT(Q) = fixed_cost + linear_cost * Q + quadratic_cost * Q^2

    Devuelve la ruta del archivo PNG generado.
    """
    if max_quantity < 1:
        max_quantity = 50

    quantities = list(range(1, max_quantity + 1))
    total_costs = [
        fixed_cost + linear_cost * q + quadratic_cost * (q ** 2)
        for q in quantities
    ]
    marginal_costs = [linear_cost + 2 * quadratic_cost * q for q in quantities]
    average_costs = [
        total_costs[i] / quantities[i] for i in range(len(quantities))
    ]

    plt.figure()
    plt.plot(quantities, marginal_costs, label="CMg")
    plt.plot(quantities, average_costs, label="CMe")
    _configure_common_axes("Curvas de costo: CMg y CMe")
    plt.legend()

    output_path = _build_output_path("costos")
    plt.savefig(output_path, dpi=160)
    plt.close()
    return output_path


def plot_series(
    values: Iterable[float],
    title: str = "Serie",
    ylabel: str = "",
    xlabel: str = "Índice",
) -> str:
    """
    Genera un gráfico de línea simple a partir de una serie de valores.

    - 'values' debe tener al menos 2 puntos.
    - Devuelve la ruta del archivo PNG generado.
    """
    series = list(values)
    if len(series) < 2:
        raise ValueError("Necesito al menos 2 puntos para graficar la serie.")

    indices = list(range(1, len(series) + 1))

    plt.figure()
    plt.plot(indices, series, marker="o")
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    output_path = _build_output_path("serie")
    plt.savefig(output_path, dpi=160)
    plt.close()
    return output_path
