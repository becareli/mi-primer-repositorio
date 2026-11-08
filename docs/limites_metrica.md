# Límites de la métrica de evaluación

## Qué mide

Coincidencia de palabras, contando repeticiones, entre una respuesta generada por el
cliente y una referencia escrita por mí. Entrega precisión, cobertura y F1, después de
limpiar y tokenizar ambos textos. No mide significado ni si un dato es correcto.

## Modos de falla conocidos

Encontrados en mi revisión manual:

- Confunde términos del rubro con otros significados. La métrica lo detecta con F1 bajo,
  pero no dice por qué. "¿Qué es la DOM?" explicó el Document Object Model de la
  programación web (F1=0,19). "¿Qué es la línea oficial?" respondió la postura de un
  partido político (F1=0,25).
- Define en general y no según la normativa. "¿Qué es un anteproyecto de edificación?"
  describió el anteproyecto de diseño arquitectónico, con evaluación económica incluida
  (F1=0,28). "Obra menor" y "revisor independiente" sacaron F1=0,31 por lo mismo.
- Una respuesta correcta y completa puede sacar F1 bajo. "Terreno de 500 m2 con
  coeficiente de constructibilidad 1,2": respondió 600 m2, bien calculado, y sacó F1=0,47
  (precisión 0,38) por las palabras de más.
- Una paráfrasis correcta puntúa bajo. "¿Qué es el coeficiente de constructibilidad?":
  mi referencia dice "el número que multiplicado..." y el modelo dijo "índice
  urbanístico... factor", con el mismo sentido (F1=0,46).
- No distingue completa de incompleta. La Ley General de Urbanismo y Construcciones
  (F1=0,45) no menciona el DFL 458 de 1975, y el certificado de informaciones previas
  (F1=0,47) no menciona el uso de suelo. Quedan en el mismo rango que respuestas
  completas (0,46 a 0,49).
- En las 20 respuestas el F1 máximo fue 0,49 y el promedio 0,36 (precisión 0,31,
  cobertura 0,47), aunque varias respuestas eran correctas. El número absoluto no
  indica calidad.

No observado en mi muestra, pero probado en test_metricas.py:

- Una negación ausente casi no baja el puntaje. Ejemplo construido por mí, no generado
  por el modelo: referencia "El proyecto no cumple la norma" y respuesta "El proyecto
  cumple la norma" dan F1=0,909, aunque afirman lo contrario. En un copiloto de
  pre-revisión es el error más grave posible.

## Muestra revisada

10 de 20 respuestas: las 5 con menor F1 y las 5 con mayor F1. Respuestas generadas el
2026-11-07 con el modelo del cliente (gemini-3.8-flash) y revisadas el 2026-11-08 con la
rúbrica de tres preguntas (corrección factual, completitud, contradicción). Entre las 5
de mayor F1 no hubo ningún falso positivo claro. Las referencias son mías y no las ha
auditado un tercero; dos datos de ellas (vigencia de 6 meses del anteproyecto y obra
menor bajo 100 m2) están pendientes de verificar contra la norma.

## Recomendación de uso

Usar F1 solo para comparar versiones del cliente o del prompt sobre las mismas 20
consultas (por ejemplo, si el promedio sube de 0,36), y no como aprobado o reprobado.
Revisar siempre a mano las respuestas con cifras, fechas, números de norma o nombres de
leyes, las que afirman si un proyecto cumple o no cumple, y todo F1 bajo 0,3, que suele
ser una respuesta fuera de tema. Como el modelo sin contexto confunde términos del
rubro, el copiloto debe entregarle la norma antes de responder y verificar contra la
OGUC.