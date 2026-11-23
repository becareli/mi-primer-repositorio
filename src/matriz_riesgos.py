"""Bloque 32 (Core) - Paso 3: matriz de riesgos del copiloto de ArquitectoChile.

Idea de obra: es la TABLA DE RIESGOS DE LA OBRA. Cada riesgo se puntua por separado
(probabilidad x impacto) y los ALTO/CRITICO exigen una persona que lo supervise.

Uso (desde la raiz del repo, con el (.venv) activo):
    python src\\matriz_riesgos.py
"""


def puntaje_riesgo(probabilidad, impacto):
    return probabilidad * impacto


def categoria_riesgo(puntaje):
    if puntaje >= 15:
        return "CRITICO"
    if puntaje >= 9:
        return "ALTO"
    if puntaje >= 4:
        return "MEDIO"
    return "BAJO"


def esta_en_el_limite(probabilidad, impacto):
    categoria_actual = categoria_riesgo(puntaje_riesgo(probabilidad, impacto))
    vecinos = [
        (probabilidad + 1, impacto), (probabilidad - 1, impacto),
        (probabilidad, impacto + 1), (probabilidad, impacto - 1),
    ]
    for p2, i2 in vecinos:
        if not (1 <= p2 <= 5 and 1 <= i2 <= 5):
            continue
        if categoria_riesgo(puntaje_riesgo(p2, i2)) != categoria_actual:
            return True
    return False


# Estimaciones con la informacion de HOY. "supervision" = quien revisa y cuando (solo ALTO/CRITICO).
mis_riesgos = [
    {"riesgo": "Norma desactualizada o mal citada, presentada como vigente",
     "probabilidad": 4, "impacto": 5,
     "mitigacion": "Estado de verificacion en cada chunk y prompt que marca PENDIENTE/LECTURA como orientativo (Bloques 24 y 26)",
     "supervision": "Patricio verifica la norma en fuente primaria (BCN/MINVU) antes de usarla en un informe"},
    {"riesgo": "Filtracion de datos de clientes (nombre, email, WhatsApp) en logs o registros",
     "probabilidad": 3, "impacto": 5,
     "mitigacion": "Logs con largo y huella en vez del texto (Bloque 31, logging_rag.py); pendiente: registro_rag.py (Bloque 28) aun guarda la pregunta completa",
     "supervision": "Solo Patricio accede a logs y registros; se revisa que no haya texto de clientes antes de cada git push"},
    {"riesgo": "Inyeccion de prompt via Acta de Observaciones PDF o mensaje del cliente",
     "probabilidad": 3, "impacto": 4,
     "mitigacion": "Filtro de patrones sobre el texto recuperado y descarte registrado en el log (Bloque 31, logging_rag.py)",
     "supervision": "Un documento marcado como sospechoso frena la respuesta automatica y pasa a revision de Patricio"},
    {"riesgo": "Carga de ocupacion mal calculada por el modelo",
     "probabilidad": 2, "impacto": 5,
     "mitigacion": "El prompt prohibe calcular y el calculo lo hace Python, no el LLM (Bloque 26)",
     "supervision": "Patricio revisa el calculo antes de emitir cotizacion o informe"},
    {"riesgo": "Ficha del cliente con un campo incorrecto o inventado (extraccion)",
     "probabilidad": 2, "impacto": 3,
     "mitigacion": "Validador de formato y null para datos faltantes; medido en 20 mensajes: 155 de 160 campos correctos (Bloques 29 y 30)",
     "supervision": ""},
    {"riesgo": "Indice desactualizado: corpus editado y vectorstore sin reindexar",
     "probabilidad": 3, "impacto": 2,
     "mitigacion": "Comando --reindexar y evaluacion de recuperacion tras cada cambio (Bloques 24 y 27)",
     "supervision": ""},
    {"riesgo": "Sube el costo por consulta (tarifa se duplica el 2027-01-01)",
     "probabilidad": 5, "impacto": 1,
     "mitigacion": "Registro de tokens y costo por consulta, unos 3,3 USD por 1.000 consultas hoy (Bloques 28 y 31)",
     "supervision": ""},
]


def calcular(riesgos):
    for r in riesgos:
        r["puntaje"] = puntaje_riesgo(r["probabilidad"], r["impacto"])
        r["categoria"] = categoria_riesgo(r["puntaje"])
        r["al_limite"] = esta_en_el_limite(r["probabilidad"], r["impacto"])
    return riesgos


def validar_matriz(riesgos):
    """Las condiciones que la actividad dice que SIEMPRE deben cumplirse. Lista vacia = ok."""
    problemas = []
    if len(riesgos) < 5:
        problemas.append("hay menos de 5 riesgos")
    if not any(r["categoria"] in ("ALTO", "CRITICO") for r in riesgos):
        problemas.append("no hay ningun riesgo ALTO o CRITICO (revisa si subestimas)")
    for r in riesgos:
        if r["categoria"] in ("ALTO", "CRITICO") and not r["supervision"].strip():
            problemas.append(f"sin punto de supervision: {r['riesgo']}")
    if sum("Bloque" in r["mitigacion"] for r in riesgos) < 2:
        problemas.append("menos de 2 mitigaciones apuntan a un bloque ya construido")
    if len({r["categoria"] for r in riesgos}) == 1:
        problemas.append("todos los riesgos tienen la misma categoria")
    return problemas


def main():
    riesgos = calcular(mis_riesgos)
    for r in sorted(riesgos, key=lambda x: -x["puntaje"]):
        marca = " [AL LIMITE]" if r["al_limite"] else ""
        print(f"{r['categoria']:8} ({r['puntaje']:2}) - {r['riesgo']}{marca}")
    print()
    for r in riesgos:
        if r["al_limite"]:
            print("revisar con otra persona:", r["riesgo"])
    problemas = validar_matriz(riesgos)
    print(f"\n{len(riesgos)} riesgos, {len(problemas)} problemas encontrados")
    for p in problemas:
        print(" -", p)


if __name__ == "__main__":
    main()
