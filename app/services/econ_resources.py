# app/services/econ_resources.py
"""
Base de conocimiento (KB) para EcoBot.

Contiene conceptos de:
- Microeconomía
- Macroeconomía
- Cálculo financiero

Cada entrada puede tener:
- "keywords"   (lista de palabras clave que activan la entrada)
- "definicion" (obligatoria)
- "intuicion"  (opcional)
- "mini_check" (opcional)
- "formula"    (opcional)

La función principal `answer_from_kb(question)` busca en la base
y devuelve un dict solo con los campos presentes, o None si no hay match.
"""

from typing import Optional, Dict, List
import unicodedata


# -----------------------
# Utilidades de texto
# -----------------------

def _normalize_text(text: str) -> str:
    """
    Normaliza texto para comparación:
      - Maneja None / cadena vacía.
      - Quita acentos.
      - Pasa a minúsculas y recorta espacios.
    """
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKD", text)
    # Quita caracteres de acento (tildes, etc.)
    without_accents = "".join(
        ch for ch in normalized if not unicodedata.combining(ch)
    )
    return without_accents.lower().strip()


def _matches_any_keyword(keywords: List[str], query: str) -> bool:
    """
    Devuelve True si la consulta coincide con al menos una palabra clave.

    Reglas:
    - Keywords cortas (<= 3 caracteres) sólo matchean si aparecen como
      palabra completa (token) en la consulta. Esto evita falsos
      positivos del estilo "ac" dentro de "inflacion" o "hacer".
    - Keywords más largas pueden matchear como subcadena normal.
    """
    normalized_query = _normalize_text(query)
    if not normalized_query:
        return False

    query_tokens = normalized_query.split()

    for keyword in keywords:
        normalized_keyword = _normalize_text(keyword)
        if not normalized_keyword:
            continue

        # Keywords muy cortas: solo matchean como token completo
        if len(normalized_keyword) <= 3:
            if normalized_keyword in query_tokens:
                return True
        else:
            # Palabras más largas: permitimos substring
            if normalized_keyword in normalized_query:
                return True

    return False


# -----------------------
# Base de conocimiento
# -----------------------

ECONOMY_KNOWLEDGE_BASE: List[Dict[str, str]] = [
    # ========== MICROECONOMÍA ==========
    {
        "keywords": ["demanda", "curva de demanda"],
        "definicion": "La demanda es la cantidad de un bien o servicio que los consumidores están dispuestos a comprar a cada precio.",
        "intuicion": "A mayor precio, menor cantidad demandada (relación inversa).",
        "mini_check": "Si el precio aumenta, ¿qué pasa con la cantidad demandada ceteris paribus?"
    },
    {
        "keywords": ["oferta", "curva de oferta"],
        "definicion": "La oferta es la cantidad de un bien o servicio que los productores están dispuestos a vender a cada precio.",
        "intuicion": "A mayor precio, mayor cantidad ofrecida (relación directa).",
        "mini_check": "Si el precio esperado sube, ¿cómo se desplaza la oferta actual?"
    },
    {
        "keywords": ["equilibrio de mercado", "equilibrio", "precio de equilibrio", "cantidad de equilibrio"],
        "definicion": "Es el punto donde la cantidad demandada es igual a la cantidad ofrecida; determina el precio y la cantidad de equilibrio.",
        "intuicion": "En equilibrio, no hay presiones para cambiar el precio si no cambian las condiciones.",
        "mini_check": "Si la demanda aumenta, ¿qué pasa con el precio y la cantidad de equilibrio?"
    },
    {
        "keywords": ["excedente del consumidor"],
        "definicion": "Es la diferencia entre lo que el consumidor está dispuesto a pagar y lo que efectivamente paga por una unidad.",
        "intuicion": "Mide el 'beneficio' por pagar menos que la máxima disposición a pagar.",
    },
    {
        "keywords": ["excedente del productor"],
        "definicion": "Es la diferencia entre el precio que recibe el productor y su costo marginal de producir una unidad.",
        "intuicion": "Mide el 'beneficio' de vender por encima del costo marginal.",
    },
    {
        "keywords": ["elasticidad precio de la demanda", "elasticidad de la demanda", "elasticidad precio"],
        "definicion": "Mide la variación porcentual de la cantidad demandada ante un cambio porcentual en el precio.",
        "intuicion": "Indica cuán sensible es el consumidor a cambios de precio.",
        "mini_check": "Si el precio sube 10% y la cantidad baja 25%, ¿la demanda es elástica o inelástica?",
        "formula": "Epd = (%ΔQd) / (%ΔP)"
    },
    {
        "keywords": ["elasticidad ingreso", "elasticidad renta"],
        "definicion": "Mide la variación porcentual de la cantidad demandada ante un cambio porcentual en el ingreso.",
        "intuicion": "Sirve para clasificar bienes en normales (Ei>0) e inferiores (Ei<0).",
        "formula": "Ei = (%ΔQ) / (%ΔY)"
    },
    {
        "keywords": ["elasticidad cruzada", "elasticidad precio cruzada"],
        "definicion": "Mide la variación porcentual de la cantidad demandada de un bien ante un cambio porcentual en el precio de otro bien.",
        "intuicion": "Si Ec>0 son sustitutos; si Ec<0 son complementarios.",
        "formula": "Ec = (%ΔQx) / (%ΔPy)"
    },
    {
        "keywords": ["impuesto especifico", "impuesto específico", "impuesto por unidad"],
        "definicion": "Un impuesto específico cobra una cantidad fija por unidad vendida, desplazando la oferta hacia arriba por el monto del impuesto.",
        "intuicion": "Genera pérdida irrecuperable de eficiencia (deadweight loss) cuando distorsiona el equilibrio.",
    },
    {
        "keywords": ["precio maximo", "precio máximo", "techo de precios"],
        "definicion": "Un precio máximo es una regulación que impide que el precio supere cierto nivel, usualmente por debajo del equilibrio.",
        "intuicion": "Suele generar escasez (exceso de demanda).",
    },
    {
        "keywords": ["precio minimo", "precio mínimo", "piso de precios"],
        "definicion": "Un precio mínimo impide que el precio baje de cierto nivel, usualmente por encima del equilibrio.",
        "intuicion": "Suele generar excedente (exceso de oferta).",
    },
    {
        "keywords": ["costo fijo", "costos fijos"],
        "definicion": "Costo que no cambia con el nivel de producción en el corto plazo.",
    },
    {
        "keywords": ["costo variable", "costos variables"],
        "definicion": "Costo que varía con el nivel de producción.",
    },
    {
        "keywords": ["costo total"],
        "definicion": "Suma de costos fijos y variables para cada nivel de producción.",
        "formula": "CT(Q) = CF + CV(Q)"
    },
    {
        "keywords": ["costo medio", "costo promedio", "cme"],
        "definicion": "Costo total dividido por la cantidad producida.",
        "formula": "CMe(Q) = CT(Q) / Q"
    },
    {
        "keywords": ["costo marginal", "cmg", "mc"],
        "definicion": "Incremento del costo total al producir una unidad adicional.",
        "intuicion": "Es el costo de la 'siguiente' unidad.",
        "mini_check": "Si CMg < CMe, ¿el CMe sube o baja al producir una unidad más?",
        "formula": "CMg(Q) = dCT/dQ"
    },
    {
        "keywords": ["producto marginal", "pmg"],
        "definicion": "Incremento del producto total al emplear una unidad adicional de insumo, manteniendo los demás constantes.",
    },
    {
        "keywords": ["producto medio", "pme"],
        "definicion": "Producto total dividido por la cantidad del insumo.",
    },
    {
        "keywords": ["competencia perfecta"],
        "definicion": "Estructura con muchos compradores y vendedores, bienes homogéneos y libre entrada/salida; las empresas son tomadoras de precios.",
    },
    {
        "keywords": ["monopolio"],
        "definicion": "Un único vendedor controla el mercado; enfrenta toda la curva de demanda y fija precio maximizando beneficios.",
        "intuicion": "Produce menos y vende a precio más alto que en competencia perfecta.",
    },
    {
        "keywords": ["oligopolio"],
        "definicion": "Pocos vendedores con interdependencia estratégica; las decisiones de una firma afectan a las demás.",
    },
    {
        "keywords": ["competencia monopolistica", "competencia monopolística"],
        "definicion": "Muchas empresas venden productos diferenciados; poder de mercado limitado y libre entrada a largo plazo.",
    },
    {
        "keywords": ["curva de indiferencia", "preferencias"],
        "definicion": "Conjunto de combinaciones de bienes que proporcionan el mismo nivel de utilidad al consumidor.",
        "intuicion": "Son decrecientes y no se cruzan si las preferencias son bien comportadas.",
    },
    {
        "keywords": ["restriccion presupuestaria", "restricción presupuestaria", "budget line"],
        "definicion": "Conjunto de combinaciones de bienes que el consumidor puede comprar dado su ingreso y precios.",
        "formula": "Px·X + Py·Y = I"
    },

    # ========== MACROECONOMÍA ==========
    {
        "keywords": ["pib", "pbi", "producto interno bruto"],
        "definicion": "Valor de mercado de todos los bienes y servicios finales producidos en un país durante un período.",
    },
    {
        "keywords": ["pib real", "pbi real"],
        "definicion": "PIB ajustado por precios constantes; elimina el efecto de la inflación.",
    },
    {
        "keywords": ["pib nominal", "pbi nominal"],
        "definicion": "PIB medido a precios corrientes del período.",
    },
    {
        "keywords": ["deflactor del pib", "deflactor del pbi"],
        "definicion": "Índice de precios que relaciona PIB nominal y PIB real.",
        "formula": "Deflactor = (PIB Nominal / PIB Real) × 100"
    },
    {
        "keywords": ["pib per capita", "pib per cápita", "pbi per capita", "pbi per cápita"],
        "definicion": "PIB dividido por la población del país.",
        "intuicion": "Aproxima el ingreso promedio por persona.",
    },
    {
        "keywords": ["inflacion", "inflación", "ipc", "indice de precios"],
        "definicion": "Aumento sostenido y generalizado del nivel de precios en una economía.",
        "intuicion": "Reduce el poder adquisitivo del dinero.",
    },
    {
        "keywords": ["desempleo", "tasa de desempleo"],
        "definicion": "Proporción de la fuerza laboral que busca empleo y no lo consigue.",
        "intuicion": "Puede ser friccional, estructural o cíclico.",
    },
    {
        "keywords": ["oferta agregada"],
        "definicion": "Relación entre el nivel de precios y la cantidad total ofrecida de bienes y servicios.",
    },
    {
        "keywords": ["demanda agregada"],
        "definicion": "Relación entre el nivel de precios y la cantidad total demandada de bienes y servicios.",
    },
    {
        "keywords": ["politica fiscal", "política fiscal"],
        "definicion": "Uso del gasto público y los impuestos para influir en la economía.",
        "intuicion": "Expansiva: más gasto o menos impuestos; contractiva: lo contrario.",
    },
    {
        "keywords": ["politica monetaria", "política monetaria", "tasa de interes", "tasa de interés"],
        "definicion": "Acciones del banco central para influir en la oferta monetaria y las tasas de interés.",
        "intuicion": "Bajar tasas suele estimular consumo e inversión; subirlas enfría la economía.",
    },
    {
        "keywords": ["balanza de pagos", "cuenta corriente", "cuenta capital"],
        "definicion": "Registro contable de todas las transacciones económicas de un país con el exterior.",
    },
    {
        "keywords": ["tipo de cambio", "tipo de cambio nominal"],
        "definicion": "Precio de una moneda en términos de otra.",
        "intuicion": "Si sube el tipo de cambio nominal (depreciación), los bienes locales se abaratan en el exterior.",
    },
    {
        "keywords": ["tipo de cambio real"],
        "definicion": "Tipo de cambio nominal ajustado por niveles de precios relativos.",
        "formula": "TCR = TCN × (P_dom / P_ext)"
    },
    {
        "keywords": ["curva de phillips"],
        "definicion": "Relación (de corto plazo) entre inflación y desempleo.",
        "intuicion": "Menos desempleo suele asociarse a más inflación en el corto plazo, con expectativas dadas.",
    },
    {
        "keywords": ["is-lm", "modelo is lm", "is lm"],
        "definicion": "Marco que combina equilibrio en el mercado de bienes (IS) y en el monetario (LM).",
        "intuicion": "IS baja con la tasa de interés; LM depende de la oferta de dinero y la demanda de dinero.",
    },

    # ========== CÁLCULO FINANCIERO ==========
    {
        "keywords": ["interes simple", "interés simple"],
        "definicion": "El interés se calcula solo sobre el capital inicial durante todo el período.",
        "formula": "I = C · i · n ;  M = C · (1 + i · n)"
    },
    {
        "keywords": ["interes compuesto", "interés compuesto"],
        "definicion": "El interés se capitaliza: cada período el capital crece con los intereses acumulados.",
        "formula": "M = C · (1 + i)^n"
    },
    {
        "keywords": ["tasa nominal", "tna", "tnv"],
        "definicion": "Tasa anual que no considera capitalización dentro del año; requiere conversión a efectiva.",
    },
    {
        "keywords": ["tasa efectiva anual", "tea"],
        "definicion": "Tasa anual que incorpora la capitalización.",
        "formula": "TEA = (1 + i_m)^m − 1  (m: períodos de capitalización al año)"
    },
    {
        "keywords": ["vpn", "van", "valor presente neto"],
        "definicion": "Suma de los flujos descontados menos la inversión inicial; si VPN>0, el proyecto crea valor.",
        "intuicion": "Trae los flujos al presente para compararlos a la misma 'base temporal'.",
        "formula": "VPN = -I0 + Σ[ Ft / (1 + r)^t ]"
    },
    {
        "keywords": ["tir", "tasa interna de retorno", "irr"],
        "definicion": "Tasa que hace que el VPN sea cero; si TIR>k exigido, el proyecto es aceptable.",
    },
    {
        "keywords": ["annuity", "renta", "anualidad", "pmt"],
        "definicion": "Serie de pagos iguales en intervalos regulares.",
        "formula": "PV = PMT · [1 - (1 + r)^(-n)] / r ;  FV = PMT · [(1 + r)^n - 1] / r"
    },
    {
        "keywords": ["amortizacion francesa", "amortización francesa", "sistema frances"],
        "definicion": "Cuota constante; al inicio predominan intereses, luego amortización de capital.",
    },
    {
        "keywords": ["bono", "bond", "precio de bono"],
        "definicion": "Título de deuda que paga cupones y/o principal; su precio es el valor presente de esos flujos.",
        "intuicion": "Si sube la tasa de descuento, baja el precio del bono (relación inversa).",
    },
    {
        "keywords": ["tasa de descuento", "costo de capital", "wacc"],
        "definicion": "Tasa usada para descontar flujos futuros; refleja el costo de oportunidad del capital.",
    },
]


# --------------------------------
# API pública: búsqueda en la KB
# --------------------------------

def answer_from_kb(question: str) -> Optional[Dict[str, str]]:
    """
    Busca una pregunta en la base de conocimiento.

    - Normaliza la pregunta (sin acentos, minúsculas).
    - Recorre todas las entradas y revisa si alguna palabra clave
      coincide con la consulta siguiendo las reglas de `_matches_any_keyword`.
    - Si encuentra match, devuelve un dict con:
        {"definicion", "intuicion"?, "mini_check"?, "formula"?"}
      Solo incluye las claves que existen en la entrada original.
    - Si no hay ningún match, devuelve None.
    """
    if not question:
        return None

    for entry in ECONOMY_KNOWLEDGE_BASE:
        keywords = entry.get("keywords", [])
        if _matches_any_keyword(keywords, question):
            result: Dict[str, str] = {
                "definicion": entry["definicion"]
            }
            if "intuicion" in entry:
                result["intuicion"] = entry["intuicion"]
            if "mini_check" in entry:
                result["mini_check"] = entry["mini_check"]
            if "formula" in entry:
                result["formula"] = entry["formula"]
            return result

    return None
