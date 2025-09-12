from typing import Optional
import re

# Base de conocimiento ampliable
CONCEPTS: dict[str, str] = {
    "elasticidad precio": "La elasticidad precio de la demanda mide el % de cambio en la cantidad demandada ante un % de cambio en el precio.",
    "elasticidad": "La elasticidad precio de la demanda mide cómo varía la cantidad demandada cuando cambia el precio.",
    "costo marginal": "El costo marginal es el incremento en el costo total por producir una unidad adicional.",
    "ingreso marginal": "El ingreso marginal es el incremento en el ingreso total por vender una unidad adicional.",
    "política fiscal": "La política fiscal usa impuestos y gasto público para influir en la economía.",
    "política monetaria": "La política monetaria la realiza el banco central ajustando tasa de interés y liquidez.",
    "tipo de cambio": "El tipo de cambio es el precio de una moneda en términos de otra.",
    "balanza comercial": "La balanza comercial es la diferencia entre exportaciones e importaciones de bienes.",
    "inflación": "La inflación es el aumento sostenido y generalizado de los precios en la economía.",
    "oferta": "La oferta es la cantidad de un bien o servicio que los productores están dispuestos a vender a cada precio.",
    "demanda": "La demanda es la cantidad que los consumidores están dispuestos a comprar a cada precio.",
    "pib": "El PIB (o PBI) es el valor monetario de los bienes y servicios finales producidos en un país en un período.",
    "pbi": "El PBI (o PIB) es el valor monetario de los bienes y servicios finales producidos en un país en un período."
}

# Precompilar patrones con límites de palabra. Orden por longitud desc. para priorizar frases.
_PATTERNS = [
    (key, re.compile(rf"\b{re.escape(key)}\b", flags=re.IGNORECASE))
    for key in sorted(CONCEPTS.keys(), key=len, reverse=True)
]

def answer_from_kb(question: str) -> Optional[str]:
    for key, pat in _PATTERNS:
        if pat.search(question):
            return CONCEPTS[key]
    return None
