# Copiloto de pre-revisión — Informe favorable del Revisor Independiente

**ArquitectoChile.com** · Especialización en Desarrollo con IA Generativa (Skillnest / Accenture) · Entrega **Gate 2**

Servicio RAG que responde consultas sobre el informe favorable del Revisor Independiente de Arquitectura (LGUC art. 116 bis) **citando la norma** que respalda cada afirmación. Es un asistente interno: **ninguna respuesta llega a un cliente sin la aprobación del arquitecto revisor**.

```
Consulta → Recuperar (Chroma) → Filtro anti-inyección → Gemini (prompt v3 con citas)
        → Borrador con fuentes → [PAUSA: aprobación de Patricio] → Cliente
                 Logs JSON con trace_id: solo largos, huellas, tokens y costo
```

Reglas de diseño: las decisiones y los cálculos (carga de ocupación, precios) viven en Python; el modelo solo lee documentos y redacta. Si el contexto no alcanza o no se puede citar, el servicio **deriva a revisión humana** en vez de inventar.

---

## 1. Instalación limpia

```bash
git clone https://github.com/becareli/mi-primer-repositorio.git
cd mi-primer-repositorio
python -m venv .venv
.venv\Scripts\activate            # Windows (CMD)
# source .venv/bin/activate       # macOS / Linux
pip install -r requirements.txt
copy .env.example .env            # Windows  (cp .env.example .env en macOS/Linux)
```

Abre `.env` y escribe tu clave: `GEMINI_API_KEY="..."`. El `.env` está en `.gitignore` (compruébalo con `git check-ignore .env`).

## 2. Indexar el corpus

```bash
python src\indexar_corpus.py               # crea vectorstore/ o actualiza SOLO lo que cambió
python src\indexar_corpus.py --reindexar   # borra y reconstruye desde cero
```

El corpus vive en `corpus/`, un archivo `.md` por documento con cabecera `id`, `fuente` y `estado`. Para agregar o corregir un documento se edita esa carpeta y se vuelve a correr el comando: la actualización es **incremental** (compara una huella por chunk y agrega, reemplaza o borra solo lo necesario).

## 3. Verificar el entorno y consultar de punta a punta

```bash
python verificar_entorno.py                                    # versiones, clave (sin mostrarla) e índice
python src\servicio_rag.py "¿Cuándo es obligatorio el informe favorable?"
python src\servicio_rag.py "..." --aprobar     # o --rechazar: decisión sin preguntar
python src\servicio_rag.py --simulado          # sin API ni costo: embeddings y modelo simulados
```

Sin `--aprobar` / `--rechazar`, el servicio **se detiene** en el punto de supervisión, muestra lo pendiente y pregunta `¿Aprobar el envío al cliente? (s/n)`. Si se aprueba, el borrador queda en `bandeja_salida/` (no se sube a Git); si se rechaza, no se envía nada.

## 4. Pruebas

```bash
python -m pytest test_gate2.py -v   # los 4 criterios no compensables (+3 caminos de falla)
python -m pytest -q                 # todas las pruebas del proyecto
python rubrica_gate2.py             # autoevaluación ponderada
```

`test_gate2.py` usa el servicio real en modo simulado, así corre sin clave de API.

---

## 5. Evidencia por dimensión de la rúbrica

| Dimensión (peso) | Dónde está |
|---|---|
| Pipeline RAG funcional (25 %) | `src/servicio_rag.py`; índice persistido e incremental en `src/indexar_corpus.py` (`sincronizar`) |
| Recuperación y citación (15 %) | Citas `[n]` verificadas en `citas_usadas()`; métricas en `src/evaluacion_recuperacion.py` → `resultados_evaluacion.txt` |
| Costo, latencia y checklist operativo (10 %) | Evento `consumo_llm` (tokens, USD, ms por etapa); corridas reales en `registros_latencia_costo.jsonl` (`src/registro_rag.py`); `verificar_entorno.py` |
| Personalización justificada (15 %) | `decision_personalizacion.md` (RAG + prompt, sin fine-tuning por ahora, con mediciones propias) |
| Observabilidad y trazabilidad (15 %) | Logs JSON en pantalla y en `logs/servicio_rag.log`, un `trace_id` por consulta en todas las etapas, incluida la aprobación |
| Seguridad, versionado y gobernanza (20 %) | Filtro anti-inyección + roles system/human + `<contexto>`; `src/registro_prompts.py` (v1→v3); supervisión con `interrupt()` en `servicio_rag.py` y `src/grafo_supervision.py`; `src/matriz_riesgos.py` + `docs/matriz_riesgos.png` |

**Criterios no compensables:** `test_gate2.py` (tests 1 a 4) y el registro de `docs/registro_ensayo_gate2.md`.

## 6. Corpus y estados de verificación

12 documentos en `corpus/`. Cada respuesta muestra la fuente y el estado del documento citado:

| Estado | Significado | Documentos |
|---|---|---|
| VERIFICADO | Contrastado con el texto legal vigente (consulta del 2026-11-23) | Definición de EUP, informe obligatorio y voluntario, beneficios, plazos DOM (art. 118), funciones del revisor |
| LECTURA | Leído de una versión no confirmada como vigente | Tabla de carga de ocupación |
| PENDIENTE | Fuente secundaria: la respuesta advierte que es orientativa | Anteproyecto, vivienda social |
| CRITERIO | Condiciones propias de ArquitectoChile | Alcance del copiloto, cotización, proceso del servicio |

## 7. Métricas de recuperación

19 preguntas etiquetadas leyendo el corpus **antes** de ver lo recuperado (incluye una sin respuesta). Con k=3: **precisión 0,333 y recall 0,972**. El recall es alto y la precisión@3 queda cerca de 0,33 por diseño: casi todas las preguntas tienen 1 sola ficha correcta, así que al traer 3 fichas el máximo posible es 1/3. Resultados en `resultados_evaluacion.txt`.

## 8. Gobernanza de datos

- Los logs y registros guardan **largo y huella** (sha256, 12 caracteres) de la consulta, nunca su texto ni datos del cliente.
- `logs/`, `bandeja_salida/`, `vectorstore*/` y `.env` están en `.gitignore`.
- Matriz de riesgos: `python src\matriz_riesgos.py`. Todo riesgo ALTO o CRÍTICO tiene un punto de supervisión humana.

## 9. Estructura

```
corpus/            documentos del RAG (.md con fuente y estado)
src/               código: servicio_rag.py, indexar_corpus.py, recuperacion.py, logging_rag.py,
                   registro_rag.py, evaluacion_recuperacion.py, registro_prompts.py,
                   grafo_supervision.py, matriz_riesgos.py, carga_ocupacion.py y sus pruebas
docs/              decisiones, límites, matriz de riesgos, registro del ensayo Gate 2
test_gate2.py      criterios no compensables del Gate 2
verificar_entorno.py, rubrica_gate2.py
```

## 10. Corrida real

Corrida con Gemini real, 2026-11-23 (Windows, Python 3.12.10):

```
python src\servicio_rag.py "¿Necesito informe favorable para un restaurante con 150 personas?"
```

| Etapa | Resultado |
|---|---|
| Índice | reutilizado, 13 chunks sin cambios (no se recalculan embeddings) |
| Recuperación | 3 chunks: `informe_voluntario-1`, `informe_obligatorio-1`, `tabla_ocupacion-1` (969 ms) |
| Generación | gemini-3.8-flash, 525 tokens de entrada y 1.620 de salida (15.497 ms) |
| Costo | USD 0,0065 por consulta (tarifa vigente hasta el 31-12-2026) |
| Respuesta | cita `[1]` LGUC art. 116 bis / DDU 514 y `[2]` LGUC art. 116 bis; como el contexto no traía la definición completa de edificio de uso público, **no lo afirmó y derivó la consulta a revisión del arquitecto** |
| Supervisión | el grafo se detuvo; se aprobó con `s` y el borrador quedó en `bandeja_salida/`; todos los eventos con el mismo `trace_id` |
| Logs | solo `pregunta_len` y `pregunta_huella`, nunca el texto de la consulta |

Evaluación de recuperación con Gemini (19 preguntas, k=3): **precisión 0,333 y recall 0,972** (antes de ampliar el corpus: 0,311 y 0,964).

## Reglas del programa

Ningún secreto va en el código ni en el repositorio; cada proyecto tiene su propio entorno virtual; todo el trabajo vive en GitHub.
