"""Bloque 23: guardar la traza de decisión del agente para revisarla después.

`verbose=True` o `mostrar_traza` solo muestran la decisión en pantalla y se
pierden al cerrar la consola. Aquí cada interacción se guarda como UNA línea
JSON en un archivo (formato .jsonl), junto con la pregunta que la originó.
"""
import json
from datetime import datetime, timezone

ARCHIVO_TRAZAS = "trazas_agente.jsonl"


def _texto(salida) -> str:
    """La respuesta del agente puede venir como str o como bloques de Gemini."""
    if isinstance(salida, str):
        return salida
    return "".join(
        bloque["text"] for bloque in salida
        if isinstance(bloque, dict) and bloque.get("type") == "text"
    )


def registrar_traza(session_id: str, entrada: str, resultado: dict,
                    archivo: str = ARCHIVO_TRAZAS) -> None:
    """Agrega al archivo una línea con: cuándo, qué se preguntó, qué herramientas
    usó el agente (con qué argumentos y qué le devolvieron) y la respuesta final.
    Si `resultado` no trae 'intermediate_steps', 'acciones' queda vacía en vez de fallar."""
    registro = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "entrada": entrada,
        "acciones": [
            {
                "herramienta": accion.tool,
                "argumentos": accion.tool_input,
                "observacion": str(observacion),
            }
            for accion, observacion in resultado.get("intermediate_steps", [])
        ],
        "respuesta_final": _texto(resultado["output"]),
    }
    with open(archivo, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")


def marcar_repeticiones_sospechosas(archivo: str = ARCHIVO_TRAZAS) -> list:
    """Primera pasada automática: devuelve avisos de las sesiones donde la MISMA
    herramienta se invocó dos veces seguidas. Es un candidato a revisar a mano,
    no una conclusión: la decisión final la toma una persona."""
    try:
        with open(archivo, encoding="utf-8") as f:
            lineas = [l for l in f if l.strip()]
    except FileNotFoundError:
        return [f"No se encontró '{archivo}'. Corre registrar_traza al menos una vez."]

    avisos = []
    for n, linea in enumerate(lineas, 1):
        try:
            registro = json.loads(linea)
        except json.JSONDecodeError:
            avisos.append(f"Línea {n} ilegible (JSON roto): revisar el archivo a mano.")
            continue
        herramientas = [a["herramienta"] for a in registro.get("acciones", [])]
        for i in range(1, len(herramientas)):
            if herramientas[i] == herramientas[i - 1]:
                avisos.append(
                    f"Revisar: {registro['session_id']} usó '{herramientas[i]}' "
                    "dos veces seguidas"
                )
                break
    return avisos
