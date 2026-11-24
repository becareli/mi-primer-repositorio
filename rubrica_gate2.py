"""Gate 2: autoevaluación honesta contra la rúbrica (promedio ponderado + no compensables).

    python rubrica_gate2.py
"""


def promedio_ponderado(puntajes, pesos):
    return sum(puntajes[d] * pesos[d] for d in pesos)


pesos = {
    "pipeline_funcional": 0.25, "recuperacion_citacion": 0.15,
    "costo_latencia": 0.10, "personalizacion": 0.15,
    "observabilidad": 0.15, "seguridad_gobernanza": 0.20,
}

# Estimación propia, 0-100, con la razón de cada nota (ver README, sección Gate 2)
mi_puntaje = {
    "pipeline_funcional": 90,     # servicio_rag.py corre de punta a punta; índice persistido e incremental
    "recuperacion_citacion": 80,  # recall alto; precisión@3 limitada a ~0.33 (1 ficha correcta por pregunta)
    "costo_latencia": 85,         # costo y latencia por consulta y por etapa; corridas reales en registros_latencia_costo.jsonl
    "personalizacion": 90,        # decision_personalizacion.md con mediciones propias (155/160 campos)
    "observabilidad": 90,         # logs JSON con trace_id en cada etapa, incluida la aprobación
    "seguridad_gobernanza": 88,   # filtro + roles + <contexto>, prompts versionados, interrupt() real, matriz
}

no_compensables = {
    "pipeline_corre_de_punta_a_punta": True,  # test_gate2.py::test_1 y corrida real del README
    "respuestas_citan_fuente": True,          # test_2: sin cita válida, el servicio deriva en vez de responder
    "logs_sin_contenido_crudo": True,         # test_3 + búsqueda del correo de prueba en logs/
    "supervision_humana_funciona": True,      # test_4 y test_6: pausa, aprueba o rechaza
}

if __name__ == "__main__":
    print("suma de pesos:", round(sum(pesos.values()), 2))
    promedio = promedio_ponderado(mi_puntaje, pesos)
    ok = all(no_compensables.values())
    print(f"promedio: {promedio:.1f}, no compensables OK? {ok}")
    print("APRUEBA" if promedio >= 80 and ok else "NO APRUEBA: revisar antes de entregar")
