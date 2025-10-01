FEWSHOTS = [
    {
        "role": "user",
        "content": "¿Qué es la elasticidad precio de la demanda?"
    },
    {
        "role": "assistant",
        "content": (
            "• Definición: Mide cuánto cambia la cantidad demandada cuando cambia el precio.\n"
            "• Intuición: Si un pequeño aumento de precio baja mucho la cantidad, la demanda es elástica.\n"
            "• Fórmula: E_d = (%ΔQd) / (%ΔP). E_d<0 por la pendiente negativa; se reporta como valor absoluto.\n"
            "• Ejemplo: Si P sube 10% y Qd cae 25% ⇒ |E_d|=2.5 ⇒ demanda elástica.\n"
            "• (Opcional) Gráfico:\n"
            "  Q |\\   (más plana = más elástica)\n"
            "    | \\\n"
            "    |  \\\n"
            "    +----\\--- P\n"
            "• Mini-check: Si el precio baja 5% y la cantidad sube 2%, ¿la demanda es elástica o inelástica?"
        )
    },
    {
        "role": "user",
        "content": "Explicá el costo marginal."
    },
    {
        "role": "assistant",
        "content": (
            "• Definición: Incremento del costo total por producir una unidad adicional.\n"
            "• Intuición: Qué te cuesta ‘la próxima’ unidad.\n"
            "• Fórmula: CMg = ΔCT/ΔQ; en continuo, CMg = dCT/dQ.\n"
            "• Ejemplo: CT(Q)=100+5Q+Q² ⇒ CMg=5+2Q. Si Q=10 ⇒ CMg=25.\n"
            "• (Opcional) Gráfico:\n"
            "  CMg\n"
            "   |    /\n"
            "   |   /\n"
            "   |__/_______ Q\n"
            "• Mini-check: Si CMg < CMe, ¿el CMe sube o baja al producir una unidad más?"
        )
    }
]
