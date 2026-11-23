"""Bloque 32 (Core) - Paso 2: punto de supervision humana para desplegar un prompt nuevo.

Idea de obra: es el VISTO BUENO DEL ARQUITECTO antes de hormigonar. El grafo se DETIENE
en supervisar() y no sigue hasta que una persona responda (aprobar o rechazar).

Uso (desde la raiz del repo, con el (.venv) activo; antes corre registro_prompts.py):
    python src\\grafo_supervision.py
"""
import json
import uuid
from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class EstadoDespliegue(TypedDict):
    huella_nueva: str
    aprobado: bool


def proponer(estado: EstadoDespliegue):
    return {}


def supervisar(estado: EstadoDespliegue):
    decision = interrupt({
        "motivo": "aprobar nueva version del prompt del copiloto de ArquitectoChile en produccion",
        "huella_propuesta": estado["huella_nueva"],
    })
    return {"aprobado": decision}


def aplicar(estado: EstadoDespliegue):
    if estado["aprobado"]:
        print("version", estado["huella_nueva"], "activada")
    else:
        print("version", estado["huella_nueva"], "rechazada, se mantiene la anterior")
    return {}


def construir_app():
    grafo = StateGraph(EstadoDespliegue)
    grafo.add_node("proponer", proponer)
    grafo.add_node("supervisar", supervisar)
    grafo.add_node("aplicar", aplicar)
    grafo.add_edge(START, "proponer")
    grafo.add_edge("proponer", "supervisar")
    grafo.add_edge("supervisar", "aplicar")
    grafo.add_edge("aplicar", END)
    return grafo.compile(checkpointer=InMemorySaver())


def nuevo_thread_id(prefijo="despliegue"):
    return f"{prefijo}-{uuid.uuid4().hex[:8]}"


def resolver(app, config, aprobar: bool):
    """Reanuda SOLO si hay una aprobacion pendiente (evita aprobar algo que nadie reviso)."""
    snapshot = app.get_state(config)
    if not snapshot.next:
        raise ValueError("este thread_id no tiene ninguna aprobacion pendiente")
    return app.invoke(Command(resume=aprobar), config=config)


def leer_huella_actual(ruta="registro_prompts.json"):
    try:
        with open(ruta, encoding="utf-8") as f:
            versiones = json.load(f)
    except FileNotFoundError:
        raise SystemExit("Falta registro_prompts.json: corre primero python src\\registro_prompts.py")
    return versiones[-1]["huella"]


def main():
    app = construir_app()
    huella = leer_huella_actual()

    config = {"configurable": {"thread_id": nuevo_thread_id()}}
    resultado = app.invoke({"huella_nueva": huella, "aprobado": False}, config=config)
    print("1) tras invocar (interrumpido):", "__interrupt__" in resultado)
    print("2) pendiente:", app.get_state(config).interrupts[0].value)
    print("3) tras aprobar:", resolver(app, config, True))

    config2 = {"configurable": {"thread_id": nuevo_thread_id()}}
    app.invoke({"huella_nueva": huella, "aprobado": False}, config=config2)
    print("4) tras rechazar:", resolver(app, config2, False))

    try:
        resolver(app, config2, True)
    except ValueError as e:
        print("5) segundo intento:", e)


if __name__ == "__main__":
    main()
