# app/router.py
from app.services.econ_resources import answer_from_kb
from app.services.didactica import build_messages
from app.services.llm_client import chat_teacher
from app.services.plots import plot_supply_demand, plot_cost_curves, plot_series, plot_demand_curve, plot_supply_curve

def route_question(question: str, history=None) -> str:
    q_raw = (question or "").strip()
    q = q_raw.lower()

# === DETECCIÓN FLEXIBLE DE GRÁFICOS ===
    # Dispara si la frase contiene "grafico" o "gráfico" en cualquier parte
    if "grafico" in q or "gráfico" in q:
        try:
            # Tokenizar simple
            parts = q.replace(",", " ").split()

            # ¿Qué pidió el/la usuaria?
            pide_demanda = any(tok in ("demanda", "demna", "dema") for tok in parts) or "demanda" in q
            pide_oferta  = any(tok in ("oferta", "ofrta", "ofe") for tok in parts) or "oferta" in q
            pide_costos  = "costo" in q or "costos" in q
            pide_serie   = "serie" in q

            # Extraer números escritos (para parámetros opcionales)
            def _is_num(t: str) -> bool:
                t2 = t.replace("-", "", 1).replace(".", "", 1)
                return t2.isdigit()
            nums = [float(t) for t in parts if _is_num(t)]

            # Serie: "grafico serie 10,12,11" o con espacios
            if pide_serie:
                # Recolectar valores después de 'serie'
                after = q.split("serie", 1)[1]
                tokens = [t.strip() for t in after.replace(",", " ").split()]
                vals = [float(t) for t in tokens if _is_num(t)]
                if not vals:
                    return "Decime los valores: ej. `grafico serie 10,12,11,15`"
                path = plot_series(vals, title="Serie", ylabel="", xlabel="Índice")
                return f"✅ Gráfico de serie guardado en:\n{path}"

            # Costos
            if pide_costos:
                path = plot_cost_curves()
                return f"✅ Gráfico de costos (CMg y CMe) guardado en:\n{path}"

            # Demanda sola
            if pide_demanda and not pide_oferta:
                # Permitir parámetros opcionales: a_d b_d
                if len(nums) >= 2:
                    path = plot_demand_curve(nums[0], nums[1])
                else:
                    path = plot_demand_curve()
                return f"✅ Gráfico de DEMANDA guardado en:\n{path}"

            # Oferta sola
            if pide_oferta and not pide_demanda:
                # Permitir parámetros opcionales: a_s b_s
                if len(nums) >= 2:
                    path = plot_supply_curve(nums[0], nums[1])
                else:
                    path = plot_supply_curve()
                return f"✅ Gráfico de OFERTA guardado en:\n{path}"

            # Ambos (oferta y demanda juntos)
            if pide_demanda and pide_oferta:
                # Permitir parámetros opcionales: a_d b_d a_s b_s
                if len(nums) == 4:
                    path = plot_supply_demand(nums[0], nums[1], nums[2], nums[3])
                else:
                    path = plot_supply_demand()
                return f"✅ Gráfico de OFERTA Y DEMANDA guardado en:\n{path}"

            # Si dijo "grafico" pero no reconocimos tipo:
            return ("Usos de `grafico`:\n"
                    "• `grafico demanda [a_d b_d]`\n"
                    "• `grafico oferta  [a_s b_s]`\n"
                    "• `grafico oferta demanda [a_d b_d a_s b_s]`\n"
                    "• `grafico costos`\n"
                    "• `grafico serie 10,12,11,15`")
        except Exception as e:
            return f"⚠️ No pude generar el gráfico: {e}"

    # === Flujo normal (KB -> IA didáctica) ===
    kb = answer_from_kb(question)
    if kb:
        return (
            "• Definición: " + kb +
            "\n• Intuición: Es la idea central del concepto."
            "\n• Mini-check: ¿Querés que lo veamos con un numerito rápido?"
        )

    msgs = build_messages(question, history=history)
    return chat_teacher(msgs, temperature=0.55, max_tokens=380)