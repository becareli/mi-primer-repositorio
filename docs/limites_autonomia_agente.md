# Límites de autonomía: agente de pre-revisión del informe favorable

Agente descrito: `src/agente_con_herramientas.py` (Bloque 21), con el registro de trazas de `src/trazas.py` (Bloque 23).
Este documento describe lo que el agente **hace hoy**. Lo que aún no existe está marcado como *no implementado*.

## Qué es y qué no es este agente

Es un asistente de **pre-revisión**: calcula una carga de ocupación y consulta qué dicen las reglas del informe favorable. **No decide ni firma nada.** El informe favorable lo emite y firma el arquitecto revisor independiente; la salida del agente es un insumo para esa persona, no una resolución.

## 1. Herramientas y nivel de riesgo

| Herramienta | Riesgo | Por qué |
|---|---|---|
| `calcular_carga_ocupacion` | **bajo** | Solo calcula; no escribe, no envía, no guarda nada. El cálculo lo hace Python (`calcular_carga_total`), no el modelo. Ante un destino inválido devuelve un texto de error con los destinos válidos, sin romper el agente. |
| `consultar_reglas_informe` | **bajo** | Solo lee un texto fijo (`REGLAS`). Si no encuentra nada responde "Derivar a revisión humana". |

Que la acción sea de riesgo bajo no significa que el contenido sea infalible. Dos riesgos de **contenido** que hoy siguen abiertos:

- **Reglas aún no verificadas.** `REGLAS` proviene de un dictamen secundario. Los documentos de `corpus/` con estado PENDIENTE o LECTURA están pendientes de verificar contra fuente primaria (por ejemplo vivienda con local pequeño, estacionamientos y el coeficiente de ocupación). Hasta verificarlas, la respuesta sobre la norma es orientativa.
- **Un número equivocado puede llevar a una mala decisión.** Una carga mal calculada podría hacer creer que un edificio no necesita informe. Por eso el cálculo es determinista en Python y por eso toda salida pasa por revisión humana antes de llegar a un cliente.

## 2. Herramientas que requieren aprobación humana

**Hoy: ninguna.** Ninguna de las dos herramientas escribe, envía ni mueve dinero, así que no hay un paso de aprobación implementado (no existe `esperar_aprobacion` en el código; ver verificación más abajo).

Herramientas **planeadas, no implementadas**. Cuando se construyan, esta es la regla:

| Herramienta planeada | Riesgo | Aprobación humana |
|---|---|---|
| `guardar_lead` (datos de contacto) | medio: escritura reversible, pero con datos personales | No, pero solo con consentimiento registrado y guardando lo mínimo |
| `generar_presupuesto` | alto: compromete un precio ante un cliente | **Sí**, antes de enviarlo (el precio se calcula en Python, nunca lo inventa el modelo) |
| `enviar_cotizacion` / `enviar_informe_pdf` | alto: sale hacia un tercero y no se puede deshacer | **Sí**, siempre |

Reglas para cuando existan:
- Si la aprobación no llega a tiempo, el resultado por defecto es **"no aprobado"**.
- `select()` sobre `stdin` **no funciona en Windows**. La espera debe resolverse con un hilo aparte o, mejor, con un panel/endpoint de aprobaciones en la API.
- Cada decisión (aprobada o no) se registra con herramienta, argumentos, resultado y momento.

## 3. Revisión de trazas

Cada interacción se guarda en `trazas_agente.jsonl` con `registrar_traza` (pregunta, herramientas usadas con sus argumentos y observaciones, respuesta final).

- **Frecuencia.** Mientras el agente está en desarrollo: se revisa cada traza. Cuando atienda a usuarios reales: una muestra semanal pequeña (5 a 10 sesiones), más **todas** las trazas donde se haya usado una herramienta de riesgo alto (cuando existan).
- **Primera pasada automática.** `marcar_repeticiones_sospechosas()` lista las sesiones donde la misma herramienta se invocó dos veces seguidas. Solo marca candidatos: decide una persona.
- **Qué se busca, según este agente:**
  1. La misma herramienta repetida seguido, o una sesión que agota las 15 iteraciones.
  2. **Una cifra en la respuesta final que ninguna observación devolvió.** Es el patrón más grave aquí: toda carga de ocupación debe venir de `calcular_carga_ocupacion`.
  3. **Una pregunta de norma respondida sin `consultar_reglas_informe`.** Ya ocurrió en una prueba anterior: el modelo respondió de memoria con un artículo inventado. Se corrigió exigiendo responder solo con lo que devuelva la herramienta.
  4. (Cuando existan herramientas de riesgo alto) una acción sin su registro de aprobación.
- **Privacidad.** Las trazas contienen lo que escribió el usuario. `trazas_agente.jsonl` **no se sube al repositorio** (está en `.gitignore`). Antes de usar la app con personas reales hay que decidir qué datos se guardan, por cuánto tiempo y con qué consentimiento; la vigencia de la Ley 21.719 queda pendiente de verificar.

## 4. Qué hacer ante un comportamiento inesperado

1. **Contener.** No usar la salida en cuestión. Si ya llegó a alguien, avisar y derivar a revisión humana.
2. **Ubicar la traza.** Buscar en `trazas_agente.jsonl` por `session_id` y `timestamp`.
3. **Reproducir.** Repetir la misma entrada con `verbose=True` y ver qué herramienta eligió, con qué argumentos y qué le devolvió.
4. **Diagnosticar, en este orden:**
   a. ¿Eligió mal la herramienta? → mejorar el docstring de esa herramienta.
   b. ¿Argumentos mal armados? → aclarar el formato en el docstring.
   c. ¿La observación fue ambigua? → mejorar el texto que devuelve la herramienta.
   d. ¿La respuesta final dice algo que ninguna observación devolvió? → reforzar `PROMPT_SISTEMA`.
5. **Desactivar si hace falta.** Quitar la herramienta de la lista `herramientas` en `construir_agente()` (una línea). El agente seguirá funcionando sin ella.
6. **Dejar una prueba.** Agregar el caso como test con `assert herramientas_usadas(...)`, para que no vuelva a pasar sin que nadie lo note.
7. **Anotar el incidente** (fecha, causa, cambio hecho) al final de este documento.

## Límites técnicos que ya existen

- `max_iterations = 15`: valor por defecto de `AgentExecutor`. El agente no puede encadenar acciones indefinidamente.
- `return_intermediate_steps=True`: la traza queda disponible para registrarla.
- Los errores dentro de las herramientas vuelven como texto en vez de romper el ciclo.

## Límites que todavía **no** existen

- **Sin límite de tiempo** (`max_execution_time` es `None`): una llamada puede tardar sin tope.
- **Sin memoria** entre interacciones: cada `invoke()` empieza de cero (el Bloque 22 explica cómo agregarla).
- **Sin límite de costo** por sesión.
- **Sin paso de aprobación humana**, porque ninguna herramienta actual lo necesita.
- Las trazas **no están anonimizadas**.

## Cómo verificar este documento contra el código

Desde la raíz del repositorio, en Windows (CMD):

```
findstr /N "esperar_aprobacion(" src\agente_con_herramientas.py
```

Esperado hoy: **sin resultados**, coherente con "ninguna herramienta requiere aprobación". Si en el futuro aparece una herramienta de riesgo alto, este comando debe mostrar la llamada dentro de ella.

```
find /c /v "" trazas_agente.jsonl
```

Esperado: un número mayor que 0, una línea por cada interacción registrada.

## Registro de incidentes

*(vacío por ahora)*
