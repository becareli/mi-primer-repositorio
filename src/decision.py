"""Bloque 30 (Core) - Decision de personalizacion para MI proyecto.

Caso: funcion 1 del copiloto, "extraer la ficha del proyecto desde el mensaje
libre del cliente" (texto -> JSON de 8 campos).

Orden de uso (desde la raiz del repo, con el (.venv) activo):
    1) python src\\probar_extraccion.py     # mide 20 respuestas reales
    2) python src\\probar_extraccion.py --fewshot   # opcional, para comparar
    3) python src\\decision.py               # corre el metodo y escribe decision_personalizacion.md
"""
import json
import os

from dataset_tuning import chequear_balance, ejemplos_raw

# ---- Supuestos que TU debes confirmar o cambiar (y justificar en el documento) ----
MIN_EJEMPLOS = 200          # umbral del curso para dataset_grande_y_de_calidad
UMBRAL_FALLOS = 3           # 3 de 20 (15 %) incumplen formato -> True
MINUTOS_POR_EJEMPLO = 5     # tiempo de etiquetar un ejemplo bien
TARIFA_HORA_USD = 25        # valor de la hora de trabajo (el del curso; pon el tuyo)
MIN_POR_CATEGORIA = 10      # meta minima de ejemplos en la categoria menos frecuente
PRESUPUESTO_LIMITADO_O_ITERAR_RAPIDO = True  # supuesto: trabajo solo y cambio el esquema seguido
RUTA_ZEROSHOT = "resultados_extraccion_zeroshot.json"
RUTA_FEWSHOT = "resultados_extraccion_fewshot.json"
RUTA_DOCUMENTO = "decision_personalizacion.md"


def recomendar_estrategia(respuestas: dict) -> tuple[dict, list[str]]:
    """Metodo de la leccion: suma puntos y REPORTA los empates."""
    puntos = {"RAG": 0, "Fine-tuning completo": 0, "PEFT": 0}
    if respuestas["informacion_cambia_seguido"]:
        puntos["RAG"] += 3
    if respuestas["problema_de_formato_o_tono"]:
        puntos["PEFT"] += 2
        puntos["Fine-tuning completo"] += 1
    if respuestas["dataset_grande_y_de_calidad"]:
        puntos["Fine-tuning completo"] += 2
        puntos["PEFT"] += 1
    if respuestas["presupuesto_limitado_o_iterar_rapido"]:
        puntos["RAG"] += 2
        puntos["PEFT"] += 1
    if respuestas["necesita_multiples_variantes"]:
        puntos["PEFT"] += 2
    maximo = max(puntos.values())
    ganadoras = [tecnica for tecnica, p in puntos.items() if p == maximo]
    return puntos, ganadoras


def estimar_costo_de_etiquetar(num_ejemplos, minutos_por_ejemplo, costo_por_hora):
    horas = (num_ejemplos * minutos_por_ejemplo) / 60
    return horas, horas * costo_por_hora


def cargar_resultados(ruta: str) -> dict | None:
    if not os.path.exists(ruta):
        return None
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def construir_respuestas(resultados: dict, num_ejemplos: int) -> dict:
    return {
        # La tarea no consulta documentos externos; los 8 campos salen de mi formulario.
        "informacion_cambia_seguido": False,
        # Evidencia: respuestas reales del modelo base sin ejemplos (probar_extraccion.py).
        "problema_de_formato_o_tono": resultados["incumplimientos"] >= UMBRAL_FALLOS,
        # Evidencia: solo tengo num_ejemplos, escritos por mi (no mensajes reales).
        "dataset_grande_y_de_calidad": num_ejemplos >= MIN_EJEMPLOS,
        "presupuesto_limitado_o_iterar_rapido": PRESUPUESTO_LIMITADO_O_ITERAR_RAPIDO,
        # Un solo extractor para toda la app.
        "necesita_multiples_variantes": False,
    }


def sensibilidad(respuestas: dict, ganadoras: list[str]) -> list[str]:
    lineas = []
    for clave in respuestas:
        variante = dict(respuestas)
        variante[clave] = not variante[clave]
        _, g = recomendar_estrategia(variante)
        cambio = "CAMBIA" if set(g) != set(ganadoras) else "igual"
        lineas.append(f"{clave} -> {variante[clave]}: {g} [{cambio}]")
    return lineas


def generar_documento(res0: dict, res1: dict | None, puntos: dict, ganadoras: list[str],
                      balance: dict, num_ejemplos: int) -> str:
    n = res0["n"]
    fallos = res0["incumplimientos"]
    pct = round(100 * fallos / n)
    formato_falla = fallos >= UMBRAL_FALLOS
    empate = len(ganadoras) > 1
    faltan = max(MIN_EJEMPLOS - num_ejemplos, 0)
    h_falta, usd_falta = estimar_costo_de_etiquetar(faltan, MINUTOS_POR_EJEMPLO, TARIFA_HORA_USD)
    h_total, usd_total = estimar_costo_de_etiquetar(MIN_EJEMPLOS, MINUTOS_POR_EJEMPLO, TARIFA_HORA_USD)
    menor_cat, menor_n = min(balance.items(), key=lambda kv: kv[1])
    faltan_cat = max(MIN_POR_CATEGORIA - menor_n, 0)
    h_cat, _ = estimar_costo_de_etiquetar(faltan_cat, MINUTOS_POR_EJEMPLO, TARIFA_HORA_USD)
    comparacion = ""
    if res1:
        comparacion = (f" Con los {num_ejemplos} ejemplos dentro del prompt (few-shot), los incumplimientos "
                       f"fueron {res1['incumplimientos']} de {res1['n']}.")

    L = ["# Decisión de personalización: extracción de la ficha del cliente", "", "## 1. El problema", ""]
    if formato_falla:
        L.append(f"El cliente escribe en texto libre (WhatsApp o correo) y el copiloto debe convertirlo en una ficha JSON de 8 campos. "
                 f"De {n} respuestas del modelo base sin ejemplos, {fallos} ({pct} %) incumplieron el formato esperado (JSON válido, claves y valores permitidos). "
                 f"El modelo entiende el mensaje; lo que falla es la consistencia de la salida.{comparacion}")
    else:
        L.append(f"El cliente escribe en texto libre (WhatsApp o correo) y el copiloto debe convertirlo en una ficha JSON de 8 campos. "
                 f"De {n} respuestas del modelo base sin ejemplos, solo {fallos} ({pct} %) incumplieron el formato esperado, por debajo del umbral de {UMBRAL_FALLOS} de 20. "
                 f"El modelo acertó {res0['aciertos_campos']} de {res0['total_campos']} campos.{comparacion}")
    L += ["", "## 2. Resultado del método de decisión", ""]
    for tecnica, p in sorted(puntos.items(), key=lambda x: -x[1]):
        L.append(f"- {tecnica}: {p} puntos")
    L.append("")
    L.append(f"**Empate entre: {', '.join(ganadoras)}**" if empate else f"Mejor puntuada: **{ganadoras[0]}**.")
    L += ["", "## 3. Técnica elegida y por qué", ""]
    if formato_falla and ganadoras == ["PEFT"]:
        L.append(f"Elijo PEFT como técnica objetivo, pero no lo ejecuto todavía. El método lo puntúa primero porque el problema es de comportamiento (formato), no de información que falte: descarto RAG porque al modelo no le falta conocimiento, y descarto el fine-tuning completo porque necesita más datos que PEFT para no sobreajustar. "
                 f"Hoy tengo {num_ejemplos} ejemplos y el umbral es {MIN_EJEMPLOS}; etiquetar los que faltan cuesta unas {h_falta:.1f} horas (≈ USD {usd_falta:.0f}) y cada intento de entrenamiento toma de minutos a horas. Mientras tanto mitigo con prompt con ejemplos y validación en Python, y vuelvo a medir. [REVISAR con tus palabras]")
    elif not formato_falla:
        L.append(f"El método da {', '.join(ganadoras)} solo por la pregunta de presupuesto e iteración rápida; no hay un problema de formato que justifique personalizar (la pregunta de formato dio False con evidencia). "
                 "Mi caso no encaja bien en las cinco preguntas: no necesita ninguna de las tres técnicas ahora. Decido NO personalizar todavía: un prompt con instrucciones claras (y ejemplos si hace falta) más la validación en Python ya cumple. "
                 f"Reevaluaré cuando tenga {MIN_EJEMPLOS} mensajes reales etiquetados y la tasa de incumplimiento supere el 15 %. [REVISAR con tus palabras]")
    else:
        L.append("[COMPLETAR: el puntaje no resolvió el empate solo; justifica aquí con tu criterio, apoyado en los costos de datos, cómputo y tiempo]")
    L += ["", "## 4. Qué necesitaría para ejecutarla", ""]
    L.append(f"Hoy tengo {num_ejemplos} ejemplos etiquetados, escritos por mí a partir de mi formulario (no son aún mensajes reales). "
             f"Para llegar a {MIN_EJEMPLOS} me faltan {faltan} ejemplos: {h_falta:.1f} horas a {MINUTOS_POR_EJEMPLO} minutos cada uno (≈ USD {usd_falta:.0f} a USD {TARIFA_HORA_USD} la hora; el dataset completo equivale a {h_total:.1f} horas, ≈ USD {usd_total:.0f}). "
             f"La categoría menos representada (\"{menor_cat}\") tiene {menor_n} ejemplo(s) y quiero al menos {MIN_POR_CATEGORIA}: me faltan {faltan_cat} (≈ {h_cat:.1f} horas). "
             "No necesito un corpus para indexar en esta función; la norma se resuelve con RAG en otra función de la app.")
    return "\n".join(L) + "\n"


def main() -> None:
    res0 = cargar_resultados(RUTA_ZEROSHOT)
    if res0 is None:
        raise SystemExit("Falta resultados_extraccion_zeroshot.json: corre primero python src\\probar_extraccion.py")
    res1 = cargar_resultados(RUTA_FEWSHOT)
    num = len(ejemplos_raw)
    respuestas = construir_respuestas(res0, num)
    puntos, ganadoras = recomendar_estrategia(respuestas)
    print("respuestas:", respuestas)
    print("puntos:", puntos)
    print("candidatas:", ganadoras)
    print("\nSensibilidad (cambio una respuesta a la vez):")
    for linea in sensibilidad(respuestas, ganadoras):
        print(" ", linea)
    doc = generar_documento(res0, res1, puntos, ganadoras, dict(chequear_balance(ejemplos_raw, "destino")), num)
    with open(RUTA_DOCUMENTO, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"\nEscrito {RUTA_DOCUMENTO}:\n")
    print(doc)


if __name__ == "__main__":
    main()
