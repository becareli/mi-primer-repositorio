# Decisión de personalización: extracción de la ficha del cliente

## 1. El problema

En ArquitectoChile el cliente escribe su solicitud en texto libre (WhatsApp o correo) y el copiloto debe convertirla en una ficha JSON de 8 campos (rol, destino, comuna, superficies, estructura, entre otros). Quería saber si el modelo base mantiene un formato consistente o si hace falta personalizarlo. Probé 20 mensajes nuevos, distintos de mis 16 ejemplos. Con criterio estricto (json.loads directo), 3 de 20 respuestas fallaron, pero las tres solo traían el JSON envuelto en cercas ```json, algo que se corrige con una línea de código o pidiendo salida JSON a la API. Tras quitarlas, 0 de 20 incumplieron el formato (JSON válido, claves y valores permitidos), y el modelo acertó 155 de 160 campos (97 %).

## 2. Resultado del método de decisión

- RAG: 2 puntos
- PEFT: 1 punto
- Fine-tuning completo: 0 puntos

No hay empate; RAG sale primera. Mis respuestas fueron: la información no cambia (False), el formato no falla (False: 0 de 20 tras quitar cercas), el dataset no es grande (False: 16 de 200), presupuesto limitado o iteración rápida (True: trabajo solo y cambio el esquema seguido) y una sola variante (False). Al cambiar una respuesta a la vez, el resultado cambia en cuatro de las cinco; la más frágil es la del formato: con el criterio estricto (3 de 20, justo el umbral) ganaría PEFT.

## 3. Técnica elegida y por qué

Decido no personalizar el modelo por ahora: mi técnica es un prompt claro más validación en Python. El puntaje de RAG viene solo de la pregunta de presupuesto, y no hay un problema de información que RAG resuelva en esta función; mi caso no encaja bien en las cinco preguntas. Descarto el criterio estricto porque los 3 fallos eran solo cercas, que se arreglan sin entrenar nada, mientras que PEFT exigiría unas 15,3 horas más de etiquetado y cada intento tomaría de minutos a horas. RAG sí lo usaré en otra función del copiloto (las consultas normativas), donde la información cambia. Reevaluaré PEFT cuando tenga 200 mensajes reales etiquetados y más del 15 % de las respuestas incumplan el formato.

## 4. Qué necesitaría para ejecutarla

Para PEFT, hoy tengo 16 ejemplos etiquetados, escritos por mí a partir de mi formulario (aún no son mensajes reales). Para llegar a 200 me faltan 184 ejemplos: 15,3 horas a 5 minutos cada uno (≈ USD 383 con la tarifa referencial del curso de USD 25 la hora). La categoría menos representada ("otro") tiene 1 ejemplo y necesito al menos 10, así que faltan 9 (≈ 0,8 horas). No necesito un corpus para indexar en esta función.