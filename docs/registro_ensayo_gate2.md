# Registro del ensayo funcional — Gate 2

Copiloto de pre-revisión para el informe favorable del Revisor Independiente (ArquitectoChile.com).

## Ensayo 1: integración de las piezas (modo simulado)

- **Fecha:** 2026-11-23
- **Comando:** `python src\servicio_rag.py --simulado --aprobar` y `python -m pytest test_gate2.py -v`
- **Resultado:** pipeline completo sin excepciones; respuesta con fuente citada; logs sin el correo de prueba; grafo de supervisión pausa, aprueba y rechaza.

| # | Encontrado | Corregido |
|---|---|---|
| 1 | `python -m pytest` se caía en todo el repositorio: `src/prompts/test_consistencia.py` es un script que llama a la API al importarse, y pytest lo trataba como prueba. | Renombrado a `prueba_consistencia.py`. |
| 2 | Las embeddings leían `GOOGLE_API_KEY`, pero `.env.example` solo declara `GEMINI_API_KEY`: en un entorno limpio la indexación podía fallar. | `crear_embeddings()` pasa `GEMINI_API_KEY` en forma explícita. |
| 3 | `registros_latencia_costo.jsonl` guardaba el texto completo de la pregunta (riesgo de datos del cliente). | Ahora guarda `pregunta_len` y `pregunta_huella`. Las líneas antiguas solo tienen preguntas de prueba, sin datos personales. |
| 4 | El índice solo se creaba si la carpeta estaba vacía: editar un documento obligaba a reindexar todo. | `sincronizar()` agrega, reemplaza o borra solo los chunks cuya huella cambió (Bloque 25). |
| 5 | Si todo lo recuperado era sospechoso, el flujo igual habría llamado al modelo con contexto vacío. | Camino `sin_contexto_confiable`: responde que deriva a revisión humana, sin llamar al modelo. |
| 6 | Al crecer el corpus, `eup_definicion` y `funciones_revisor` se partían en 2 chunks y descuadraban las etiquetas de evaluación. | Textos ajustados a menos de 500 caracteres (1 chunk cada uno). |
| 7 | Los eventos del punto de supervisión salían con `trace_id: null`. | `supervisar_envio()` fija el trace_id de la consulta durante la aprobación. |
| 8 | El servicio no verificaba que la respuesta citara algo. | `citas_usadas()`: si el modelo no cita un `[n]` válido, el servicio deriva en vez de entregar texto sin respaldo. |

## Ensayo 2: corrida real con Gemini

- **Fecha:** 2026-11-23 (Windows, Python 3.12.10, entorno `.venv`)
- `python -m pytest test_gate2.py -v` → 7 passed; `python -m pytest -q` → 139 passed.
- `python verificar_entorno.py` → "Entorno listo para la corrida final".

| # | Encontrado | Corregido |
|---|---|---|
| 9 | Indexación incremental, primera corrida: `nuevos 4, modificados 9` (los chunks antiguos no tenían huella). Segunda corrida: `sin_cambios 13`. | Comportamiento esperado: desde ahora solo se reprocesa lo que cambia. |
| 10 | La evaluación con Gemini bajó el recall de 0,964 a 0,861: las preguntas "¿Es obligatorio el informe favorable para un EUP?" y "¿Qué pasa si falta…?" dieron 0,00. Al reescribir con el texto legal, `informe_obligatorio` empezaba con "el propietario **puede** contratar" (suena a voluntario) y `informe_voluntario` empezaba hablando de "edificios de uso público". | Se puso la idea principal al inicio de cada ficha. La reindexación incremental procesó solo esos 2 chunks (`modificados 2, sin_cambios 11`). Resultado: **precisión 0,333 y recall 0,972**. |
| 11 | Consulta real "restaurante con 150 personas": el retriever no trajo `eup_definicion-1`. | El modelo no afirmó lo que el contexto no respaldaba: citó [1] y [2] y derivó a revisión humana. Mejora para el Gate 3: que la calculadora en Python decida si es edificio de uso público. |

Corrida final del servicio: trace `trace-154d1341`, 525 + 1.620 tokens, USD 0,0065, 969 ms de recuperación y 15.497 ms de generación; pausa en el punto de supervisión, aprobada con `s`; logs sin el texto de la consulta.
