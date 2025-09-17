# app/router.py
import re
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

# ----------------------------
# Helpers para números / parse
# ----------------------------
def _is_num(tok: str) -> bool:
    t = tok.strip().replace(",", ".")
    if t.startswith("-"):
        t = t[1:]
    if t.count(".") > 1:
        return False
    return t.replace(".", "", 1).isdigit()

def _parse_floats(text: str):
    # acepta "120 -1.2" y también "120,-1.2"
    toks = re.split(r"[\s,;]+", text.strip())
    vals = []
    for t in toks:
        tt = t.replace(",", ".")
        if _is_num(tt):
            vals.append(float(tt))
    return vals

# ----------------------------
# Router principal
# ----------------------------
def route_question(question: str, history=None) -> str:
    q_raw = (question or "").strip()
    q = q_raw.lower()

    # ======================
    #  BLOQUE DE GRÁFICOS
    # ======================
    if ("grafico" in q) or ("gráfico" in q):
        try:
            # tolerancia a typos y variantes
            pide_demanda = ("demanda" in q or "demna" in q or "dema" in q or "demada" in q)
            pide_oferta  = ("oferta" in q or "ofrta" in q or "ofe" in q)
            pide_costos  = ("costo" in q or "costos" in q or "coste" in q or "costes" in q)
            pide_serie   = ("serie" in q)

            nums = _parse_floats(q)

            # SERIE
            if pide_serie:
                after = re.split(r"serie", q, maxsplit=1)[-1]
                vals = _parse_floats(after)
                if len(vals) < 2:
                    return "Pasame valores: ej. `grafico serie 10,12,11,15`"
                path = plot_series(vals, title="Serie", ylabel="", xlabel="Índice")
                return (
                    f"✅ Gráfico de SERIE guardado en:\n{path}\n\n"
                    "📘 Explicación: El gráfico de serie muestra la evolución de tus valores en orden. "
                    "Sirve para ver subas, bajas y posibles tendencias."
                )

            # OFERTA Y DEMANDA (juntos)
            if pide_demanda and pide_oferta:
                if len(nums) >= 4:
                    path = plot_supply_demand(nums[0], nums[1], nums[2], nums[3])
                else:
                    path = plot_supply_demand()  # valores por defecto
                return (
                    f"✅ Gráfico de OFERTA Y DEMANDA guardado en:\n{path}\n\n"
                    "📘 Explicación: El punto donde se cruzan oferta y demanda es el equilibrio de mercado. "
                    "Allí, la cantidad demandada coincide con la ofrecida al precio de equilibrio."
                )

            # DEMANDA (sola)
            if pide_demanda and not pide_oferta:
                if len(nums) >= 2:
                    path = plot_demand_curve(nums[0], nums[1])
                else:
                    path = plot_demand_curve()  # valores por defecto
                return (
                    f"✅ Gráfico de DEMANDA guardado en:\n{path}\n\n"
                    "📘 Explicación: La curva de demanda tiene pendiente negativa: "
                    "cuando el precio sube, la cantidad demandada baja (y viceversa)."
                )

            # OFERTA (sola)
            if pide_oferta and not pide_demanda:
                if len(nums) >= 2:
                    path = plot_supply_curve(nums[0], nums[1])
                else:
                    path = plot_supply_curve()  # valores por defecto
                return (
                    f"✅ Gráfico de OFERTA guardado en:\n{path}\n\n"
                    "📘 Explicación: La curva de oferta es creciente: "
                    "a precios más altos, los productores están dispuestos a ofrecer más cantidad."
                )

            # COSTOS
            if pide_costos:
                path = plot_cost_curves()
                return (
                    f"✅ Gráfico de COSTOS guardado en:\n{path}\n\n"
                    "📘 Explicación: El costo medio (CMe) suele tener forma de U y el costo marginal (CMg) "
                    "corta al CMe en su punto mínimo."
                )

            # Ayuda si dijo “gráfico” pero no especificó tipo
            return (
                "Usos de `grafico`:\n"
                "• `grafico demanda [a_d b_d]`\n"
                "• `grafico oferta  [a_s b_s]`\n"
                "• `grafico oferta demanda [a_d b_d a_s b_s]`\n"
                "• `grafico costos`\n"
                "• `grafico serie 10,12,11,15`"
            )

        except Exception as e:
            return f"⚠️ No pude generar el gráfico: {e}"

    # ======================
    #  FLUJO NORMAL (KB/LLM)
    # ======================
    kb = answer_from_kb(question)
    if kb:
        return (
            "• Definición: " + kb +
            "\n• Intuición: Es la idea central del concepto."
            "\n• Mini-check: ¿Querés que lo veamos con un numerito rápido?"
        )

    msgs = build_messages(question, history=history)
    return chat_teacher(msgs, temperature=0.55, max_tokens=380)
