# app/router.py
"""
Router principal de EcoBot.

Dado un texto de pregunta:
  1. Si pide un gráfico (palabra 'grafico' o 'gráfico'), llama a las funciones
     de app.services.plots (demanda, oferta, costos, serie, etc.) y devuelve
     un mensaje con la ruta del PNG generado + una explicación corta.

  2. Si no es un gráfico, intenta responder usando la base de conocimiento
     económica (app.services.econ_resources.answer_from_kb).

  3. Si la base de conocimiento no alcanza, usa el LLM a través de
     app.services.llm_client.chat_teacher, construyendo los mensajes con
     app.services.didactica.build_messages.
"""

from __future__ import annotations

import re
from typing import List, Dict, Any

from app.services.econ_resources import answer_from_kb
from app.services.didactica import build_messages
from app.services.llm_client import chat_teacher
from app.services.plots import (
    plot_supply_demand,
    plot_cost_curves,
    plot_series,
    plot_demand_curve,
    plot_supply_curve,
)

# Parámetros por defecto del LLM (podrías moverlos a app/config.py si querés)
DEFAULT_LLM_TEMPERATURE: float = 0.55
DEFAULT_LLM_MAX_TOKENS: int = 380


# ----------------------------
# Helpers: números / parseo
# ----------------------------

def _is_numeric_token(token: str) -> bool:
    """
    Devuelve True si 'token' representa un número válido.
    Acepta:
      - enteros
      - decimales con . o ,
      - signo negativo opcional.
    """
    if not token:
        return False

    cleaned = token.strip().replace(",", ".")  # cambiamos coma por punto

    if cleaned.startswith("-"):
        cleaned = cleaned[1:]  # quitamos el signo para analizar solo dígitos

    # Más de un punto decimal → inválido
    if cleaned.count(".") > 1:
        return False

    # Permitimos a lo sumo un punto; el resto deben ser dígitos
    return cleaned.replace(".", "", 1).isdigit()


def _extract_floats_from_text(text: str) -> List[float]:
    """
    Extrae todos los números (como float) que aparezcan en un texto.
    Soporta separadores por espacio, coma o punto y coma.
    """
    tokens = re.split(r"[\s,;]+", (text or "").strip())
    values: List[float] = []

    for token in tokens:
        normalized = token.replace(",", ".")
        if _is_numeric_token(normalized):
            values.append(float(normalized))

    return values


# ----------------------------
# Formateo de KB (str o dict)
# ----------------------------

def _format_kb_entry(kb_entry: object) -> str:
    """
    Recibe una entrada de la base de conocimiento y la convierte
    en un texto amigable con:
      • Definición
      • Intuición (si existe)
      • Mini-check (siempre se agrega)
    """
    if isinstance(kb_entry, str):
        definition = kb_entry.strip()
        intuition = None
    elif isinstance(kb_entry, dict):
        # Buscamos posibles claves de "definición"
        definition = (
            kb_entry.get("definicion")
            or kb_entry.get("definición")
            or kb_entry.get("definition")
            or kb_entry.get("answer")
            or ""
        )
        # Distintas formas de escribir "intuición"
        intuition = (
            kb_entry.get("intuicion")
            or kb_entry.get("intuición")
            or kb_entry.get("intuition")
        )
    else:
        # fallback: lo convertimos a string sin romper
        definition = str(kb_entry)
        intuition = None

    parts: List[str] = []

    if definition:
        parts.append("• Definición: " + str(definition).strip())
    if intuition:
        parts.append("• Intuición: " + str(intuition).strip())

    # Línea de mini-check estándar
    parts.append("• Mini-check: ¿Querés que lo bajemos a un numerito rápido?")

    return "\n".join(parts)


# ----------------------------
# Router principal
# ----------------------------

def route_question(
    question: str,
    history: List[Dict[str, Any]] | None = None,
) -> str:
    """
    Dado el texto de una pregunta y (opcionalmente) el historial de la sesión,
    decide cómo responder:
      - gráficos → funciones de app.services.plots
      - conceptos → base de conocimiento (econ_resources)
      - resto → LLM (Groq) mediante chat_teacher
    """
    raw_question = (question or "").strip()
    normalized_question = raw_question.lower()

    # ======================
    #  GRÁFICOS (con explicación)
    # ======================
    if ("grafico" in normalized_question) or ("gráfico" in normalized_question):
        try:
            # Tolerancia básica a typos
            wants_demand_graph = any(
                word in normalized_question
                for word in ("demanda", "demna", "dema", "demada")
            )
            wants_supply_graph = any(
                word in normalized_question
                for word in ("oferta", "ofrta", "ofe")
            )
            wants_cost_graph = any(
                word in normalized_question
                for word in ("costo", "costos", "coste", "costes")
            )
            wants_series_graph = "serie" in normalized_question

            numeric_values = _extract_floats_from_text(normalized_question)

            # ----- Serie: "grafico serie 10,12,11,15"
            if wants_series_graph:
                # Tomar números después de la palabra "serie" si existen
                after_serie = normalized_question.split("serie", 1)[1]
                series_values = _extract_floats_from_text(after_serie)

                # Si no encontramos nada específico después de "serie",
                # usamos todos los números que haya en el texto.
                if len(series_values) < 2:
                    series_values = numeric_values

                if len(series_values) < 2:
                    return "Decime valores así: `grafico serie 10,12,11,15`"

                image_path = plot_series(
                    series_values,
                    title="Serie",
                    ylabel="",
                    xlabel="Índice",
                )
                return (
                    f"✅ Gráfico de SERIE guardado en:\n{image_path}\n\n"
                    "📘 Explicación: El gráfico de serie muestra la evolución de tus valores en orden. "
                    "Sirve para ver subas, bajas y tendencias simples."
                )

            # ----- Costos
            if wants_cost_graph:
                image_path = plot_cost_curves()
                return (
                    f"✅ Gráfico de COSTOS guardado en:\n{image_path}\n\n"
                    "📘 Explicación: Se muestran curvas típicas (Costo Medio y Costo Marginal). "
                    "En muchos casos el CMg corta al CMe en su punto mínimo."
                )

            # ----- Oferta y demanda juntos
            if wants_demand_graph and wants_supply_graph:
                # Parámetros opcionales: a_d, b_d, a_s, b_s
                if len(numeric_values) >= 4:
                    image_path = plot_supply_demand(
                        numeric_values[0],
                        numeric_values[1],
                        numeric_values[2],
                        numeric_values[3],
                    )
                else:
                    image_path = plot_supply_demand()

                return (
                    f"✅ Gráfico de OFERTA Y DEMANDA guardado en:\n{image_path}\n\n"
                    "📘 Explicación: El punto donde se cruzan oferta y demanda es el equilibrio de mercado. "
                    "Allí, la cantidad demandada coincide con la ofrecida al precio de equilibrio."
                )

            # ----- Demanda sola
            if wants_demand_graph and not wants_supply_graph:
                # Parámetros opcionales: a_d, b_d
                if len(numeric_values) >= 2:
                    image_path = plot_demand_curve(
                        numeric_values[0],
                        numeric_values[1],
                    )
                else:
                    image_path = plot_demand_curve()

                return (
                    f"✅ Gráfico de DEMANDA guardado en:\n{image_path}\n\n"
                    "📘 Explicación: La curva de demanda tiene pendiente negativa: "
                    "cuando el precio sube, la cantidad demandada baja (y viceversa)."
                )

            # ----- Oferta sola
            if wants_supply_graph and not wants_demand_graph:
                # Parámetros opcionales: a_s, b_s
                if len(numeric_values) >= 2:
                    image_path = plot_supply_curve(
                        numeric_values[0],
                        numeric_values[1],
                    )
                else:
                    image_path = plot_supply_curve()

                return (
                    f"✅ Gráfico de OFERTA guardado en:\n{image_path}\n\n"
                    "📘 Explicación: La curva de oferta es creciente: "
                    "a precios más altos, los productores están dispuestos a ofrecer más cantidad."
                )

            # ----- Ayuda si dijo “gráfico” pero no especificó tipo
            return (
                "Usos de `grafico`:\n"
                "• `grafico demanda [a_d b_d]`\n"
                "• `grafico oferta  [a_s b_s]`\n"
                "• `grafico oferta demanda [a_d b_d a_s b_s]`\n"
                "• `grafico costos`\n"
                "• `grafico serie 10,12,11,15`"
            )

        except Exception as exc:
            return f"⚠️ No pude generar el gráfico: {exc}"

    # ======================
    #  KB (definición + intuición + mini-check)
    # ======================
    kb_entry = answer_from_kb(raw_question) or answer_from_kb(normalized_question)

    if not kb_entry:
        # búsqueda rápida por palabra clave si no hubo match directo
        for keyword in (
            "demanda",
            "oferta",
            "elasticidad",
            "pbi",
            "pib",
            "inflacion",
            "is-lm",
            "tir",
            "vpn",
            "costos",
            "costo",
        ):
            if keyword in normalized_question:
                kb_entry = answer_from_kb(keyword)
                if kb_entry:
                    break

    if kb_entry:
        try:
            return _format_kb_entry(kb_entry)
        except Exception as exc:
            # Nunca romper por un problema de formato de KB
            return (
                f"• Definición: {str(kb_entry)}\n"
                "• Mini-check: ¿Querés que lo bajemos a un numerito rápido?\n"
                f"(Nota técnica: {exc})"
            )

    # ======================
    #  LLM (fallback)
    # ======================
    try:
        messages = build_messages(raw_question, history=history)
        return chat_teacher(
            messages,
            temperature=DEFAULT_LLM_TEMPERATURE,
            max_tokens=DEFAULT_LLM_MAX_TOKENS,
        )
    except Exception as exc:
        # Red de seguridad para consola
        return (
            "⚠️ No pude consultar al modelo ahora.\n"
            "• Definición: La demanda es la cantidad que los consumidores desean comprar a cada precio; "
            "la oferta, la cantidad que los productores desean vender.\n"
            "• Mini-check: ¿Querés que lo bajemos a un numerito rápido?\n"
            f"(Detalle técnico: {exc})"
        )
