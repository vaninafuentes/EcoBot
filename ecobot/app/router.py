# ecobot/app/router.py
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
# Helpers: números / parseo
# ----------------------------
def _is_num_token(tok: str) -> bool:
    """Acepta enteros/decimales con . o , y signo - opcional."""
    if not tok:
        return False
    t = tok.strip().replace(",", ".")
    if t.startswith("-"):
        t = t[1:]
    if t.count(".") > 1:
        return False
    return t.replace(".", "", 1).isdigit()

def _parse_floats(text: str):
    """Extrae todos los números del texto (soporta coma o punto)."""
    toks = re.split(r"[\s,;]+", (text or "").strip())
    vals = []
    for t in toks:
        tt = t.replace(",", ".")
        if _is_num_token(tt):
            vals.append(float(tt))
    return vals

# ----------------------------
# Formateo de KB (str o dict)
# ----------------------------
def _format_kb(kb) -> str:
    """
    Devuelve texto con:
      • Definición
      • Intuición (si existe)
      • Mini-check
    Acepta str o dict con claves comunes.
    """
    if isinstance(kb, str):
        defin = kb.strip()
        intu  = None
    elif isinstance(kb, dict):
        defin = (
            kb.get("definicion")
            or kb.get("definición")
            or kb.get("definition")
            or kb.get("answer")
            or ""
        )
        intu = kb.get("intuicion") or kb.get("intuición") or kb.get("intuition")
    else:
        defin = str(kb)
        intu = None

    parts = []
    if defin:
        parts.append("• Definición: " + str(defin).strip())
    if intu:
        parts.append("• Intuición: " + str(intu).strip())
    # vuelve el mini-check
    parts.append("• Mini-check: ¿Querés que lo bajemos a un numerito rápido?")
    return "\n".join(parts)

# ----------------------------
# Router principal
# ----------------------------
def route_question(question: str, history=None) -> str:
    q_raw = (question or "").strip()
    q = q_raw.lower()

    # ======================
    #  GRÁFICOS (con explicación)
    # ======================
    if ("grafico" in q) or ("gráfico" in q):
        try:
            # tolerancia básica a typos
            pide_demanda = any(w in q for w in ("demanda", "demna", "dema", "demada"))
            pide_oferta  = any(w in q for w in ("oferta", "ofrta", "ofe"))
            pide_costos  = any(w in q for w in ("costo", "costos", "coste", "costes"))
            pide_serie   = "serie" in q

            nums = _parse_floats(q)

            # Serie: "grafico serie 10,12,11,15"
            if pide_serie:
                # Tomar números después de la palabra "serie" si existen
                if "serie" in q:
                    after = q.split("serie", 1)[1]
                    vals = _parse_floats(after)
                else:
                    vals = nums
                if len(vals) < 2:
                    return "Decime valores así: `grafico serie 10,12,11,15`"
                path = plot_series(vals, title="Serie", ylabel="", xlabel="Índice")
                return (
                    f"✅ Gráfico de SERIE guardado en:\n{path}\n\n"
                    "📘 Explicación: El gráfico de serie muestra la evolución de tus valores en orden. "
                    "Sirve para ver subas, bajas y tendencias simples."
                )

            # Costos
            if pide_costos:
                path = plot_cost_curves()
                return (
                    f"✅ Gráfico de COSTOS guardado en:\n{path}\n\n"
                    "📘 Explicación: Se muestran curvas típicas (Costo Medio y Costo Marginal). "
                    "En muchos casos el CMg corta al CMe en su punto mínimo."
                )

            # Oferta y demanda juntos
            if pide_demanda and pide_oferta:
                # Parámetros opcionales: a_d, b_d, a_s, b_s
                if len(nums) >= 4:
                    path = plot_supply_demand(nums[0], nums[1], nums[2], nums[3])
                else:
                    path = plot_supply_demand()
                return (
                    f"✅ Gráfico de OFERTA Y DEMANDA guardado en:\n{path}\n\n"
                    "📘 Explicación: El punto donde se cruzan oferta y demanda es el equilibrio de mercado. "
                    "Allí, la cantidad demandada coincide con la ofrecida al precio de equilibrio."
                )

            # Demanda sola
            if pide_demanda and not pide_oferta:
                # Parámetros opcionales: a_d, b_d
                if len(nums) >= 2:
                    path = plot_demand_curve(nums[0], nums[1])
                else:
                    path = plot_demand_curve()
                return (
                    f"✅ Gráfico de DEMANDA guardado en:\n{path}\n\n"
                    "📘 Explicación: La curva de demanda tiene pendiente negativa: "
                    "cuando el precio sube, la cantidad demandada baja (y viceversa)."
                )

            # Oferta sola
            if pide_oferta and not pide_demanda:
                # Parámetros opcionales: a_s, b_s
                if len(nums) >= 2:
                    path = plot_supply_curve(nums[0], nums[1])
                else:
                    path = plot_supply_curve()
                return (
                    f"✅ Gráfico de OFERTA guardado en:\n{path}\n\n"
                    "📘 Explicación: La curva de oferta es creciente: "
                    "a precios más altos, los productores están dispuestos a ofrecer más cantidad."
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
    #  KB (definición + intuición + mini-check)
    # ======================
    kb = answer_from_kb(q_raw) or answer_from_kb(q)
    if not kb:
        # búsqueda rápida por palabra clave si no hubo match
        for key in ("demanda","oferta","elasticidad","pbi","pib","inflacion","is-lm","tir","vpn","costos","costo"):
            if key in q:
                kb = answer_from_kb(key)
                if kb:
                    break

    if kb:
        try:
            return _format_kb(kb)
        except Exception as e:
            # nunca romper por formato de KB
            return f"• Definición: {str(kb)}\n• Mini-check: ¿Querés que lo bajemos a un numerito rápido?\n(Nota técnica: {e})"

    # ======================
    #  LLM (fallback)
    # ======================
    try:
        msgs = build_messages(q_raw, history=history)
        return chat_teacher(msgs, temperature=0.55, max_tokens=380)
    except Exception as e:
        # red de seguridad para consola
        return (
            "⚠️ No pude consultar al modelo ahora.\n"
            "• Definición: La demanda es la cantidad que los consumidores desean comprar a cada precio; "
            "la oferta, la cantidad que los productores desean vender.\n"
            "• Mini-check: ¿Querés que lo bajemos a un numerito rápido?\n"
            f"(Detalle técnico: {e})"
        )
