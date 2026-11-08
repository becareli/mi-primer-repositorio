from collections import Counter
from pipeline_texto import procesar_texto

def contar_coincidencias(tokens_referencia: list[str], tokens_respuesta: list[str]) -> int:
    """
    Cuenta palabras en común, respetando cuántas veces aparece cada una. 
    """
    conteo_referencia = Counter(tokens_referencia)
    conteo_respuesta = Counter(tokens_respuesta)
    interseccion = conteo_referencia & conteo_respuesta  # Intersección de contadores Mínimo de cada palabra 
    return sum(interseccion.values())  # Suma de las cantidades de coincidencias

def calcular_precision_cobertura_f1(
    tokens_referencia: list[str], tokens_respuesta: list[str]
) -> dict[str, float]:
    """
    Calcula la precisión, cobertura y F1-score entre dos listas de tokens.
    """
    if not tokens_respuesta or not tokens_referencia:
        return {"precision": 0.0, "cobertura": 0.0, "f1": 0.0}

    coincidencias = contar_coincidencias(tokens_referencia, tokens_respuesta)
    precision = coincidencias / len(tokens_respuesta) 
    cobertura = coincidencias / len(tokens_referencia)

    if precision + cobertura == 0:
        f1 = 0.0
    else:
        f1 = 2 * (precision * cobertura) / (precision + cobertura)

    return {"precision": precision, "cobertura": cobertura, "f1": f1}

def calcular_metricas(texto_referencia: str, texto_respuesta: str) -> dict[str, float]:
    """ Camino completo: limpia, tokeniza y calcula las tres métricas.""" 
    return calcular_precision_cobertura_f1(
            procesar_texto(texto_referencia), procesar_texto(texto_respuesta)
    )

def resumir_metricas(resultados: list[dict[dict]]) -> dict[str, float]:
    """
    Calcula el Promedio de precisión, cobertura y F1-score de una lista de resultados.
    """
    if not resultados:
        return {"precision_promedio": 0.0, "cobertura_promedio": 0.0, "f1_promedio": 0.0 }

    n = len(resultados)
    return {
        "precision_promedio": sum(r["precision"] for r in resultados) / n,
        "cobertura_promedio": sum(r["cobertura"] for r in resultados) / n,
        "f1_promedio": sum(r["f1"] for r in resultados) / n,
    }


    