"""Bloques 19 y 20: enrutamiento condicional + manejo de errores.

Recibe un mensaje de un arquitecto y decide por qué camino va:
  - "proyecto"  -> describe un proyecto con destinos y superficies:
                   corre la chain de tres pasos del Bloque 18 (carga de ocupación).
  - "normativa" -> es una pregunta sobre norma (OGUC/LGUC).
  - cualquier otra cosa -> ruta por defecto: se deriva a revisión humana.
"""
import logging
import os

from dotenv import load_dotenv
from cadena_tres_pasos import REGLAS, construir_cadena
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import (
    RunnableBranch,
    RunnableLambda,
    RunnablePassthrough,
)
from langchain_google_genai import ChatGoogleGenerativeAI

from cadena_tres_pasos import construir_cadena

logger = logging.getLogger(__name__)

RESPUESTA_DERIVAR = (
    "No pude clasificar esta consulta con seguridad. La derivo a revisión humana "
    "del equipo para no darte una respuesta incorrecta."
)
RESPUESTA_RESPALDO = (
    "No pude procesar esta consulta automáticamente. Un revisor del equipo la "
    "revisará manualmente."
)
RESPUESTA_ERROR_GENERAL = (
    "No pudimos procesar tu mensaje en este momento. Intenta de nuevo más tarde."
)

plantilla_clasificacion = PromptTemplate.from_template(
    "Clasifica el siguiente mensaje de un arquitecto en una sola palabra:\n"
    "- proyecto: describe un proyecto con destinos y superficies (m2).\n"
    "- normativa: pregunta sobre una norma (OGUC, LGUC, plazos, requisitos).\n"
    "- otro: cualquier otra cosa.\n"
    "Responde solo con esa palabra.\n\nMensaje: {mensaje}"
)

plantilla_normativa = PromptTemplate.from_template(
    "Eres un revisor de arquitectura en Chile. Responde SOLO con base en estas "
    "reglas:\n{reglas}\n\n"
    "Máximo 4 líneas. No cites artículos que no estén en las reglas. Si la "
    "consulta no se puede responder con ellas, responde exactamente: "
    "'No tengo base verificada para responder; se deriva a revisión humana.'\n\n"
    "Consulta: {mensaje}"
).partial(reglas=REGLAS)


def _normalizar(texto: str) -> str:
    """El modelo puede devolver 'Proyecto.', ' proyecto\\n', etc. Lo dejamos limpio."""
    return texto.strip().lower().strip(".,;:!¡¿?\"'* ")


def construir_paso_clasificacion(modelo):
    return plantilla_clasificacion | modelo | StrOutputParser() | RunnableLambda(_normalizar)


def construir_ruta_proyecto(modelo):
    """Adapta la entrada ({'mensaje'}) a lo que espera la chain del Bloque 18 ({'descripcion'})."""
    adaptador = RunnableLambda(lambda x: {"descripcion": x["mensaje"]})
    return adaptador | construir_cadena(modelo)


def construir_ruta_normativa(modelo):
    return plantilla_normativa | modelo | StrOutputParser()


def construir_ruta_derivar():
    return RunnableLambda(lambda x: RESPUESTA_DERIVAR)


def construir_cadena_con_enrutamiento(
    paso_clasificacion,
    ruta_proyecto=None,
    ruta_normativa=None,
    ruta_derivar=None,
):
    ruta_proyecto = ruta_proyecto or RunnablePassthrough()
    ruta_normativa = ruta_normativa or RunnablePassthrough()
    ruta_derivar = ruta_derivar or construir_ruta_derivar()

    bifurcacion = RunnableBranch(
        (lambda x: x["categoria"] == "proyecto", ruta_proyecto),
        (lambda x: x["categoria"] == "normativa", ruta_normativa),
        ruta_derivar,  # ruta por defecto: cualquier otra categoría
    )
    return RunnablePassthrough.assign(categoria=paso_clasificacion) | bifurcacion


# ---------------- Bloque 20: manejo de errores ----------------

def _respuesta_de_respaldo(x):
    logger.warning("Se activó el fallback de una ruta; entrada: %s", x)
    return RESPUESTA_RESPALDO


respuesta_de_respaldo = RunnableLambda(_respuesta_de_respaldo)


def construir_ruta_segura(ruta):
    """Si la ruta lanza cualquier excepción, responde con el respaldo en vez de caerse."""
    return ruta.with_fallbacks([respuesta_de_respaldo])


def procesar_mensaje_seguro(cadena, mensaje):
    """Red de seguridad final: ningún fallo deja al usuario sin respuesta."""
    try:
        return cadena.invoke({"mensaje": mensaje})
    except Exception:
        logger.exception("Error procesando mensaje")
        return RESPUESTA_ERROR_GENERAL


def construir_chain_completa(modelo):
    return construir_cadena_con_enrutamiento(
        paso_clasificacion=construir_paso_clasificacion(modelo),
        ruta_proyecto=construir_ruta_segura(construir_ruta_proyecto(modelo)),
        ruta_normativa=construir_ruta_segura(construir_ruta_normativa(modelo)),
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    load_dotenv()
    modelo = ChatGoogleGenerativeAI(
        model="gemini-3.8-flash", google_api_key=os.getenv("GEMINI_API_KEY")
    )
    cadena = construir_chain_completa(modelo)
    for mensaje in [
        "Obra nueva en Providencia: oficinas con 500 m2 y 816 m2 de estacionamientos de uso común.",
        "¿Cuándo es obligatorio el informe de revisor independiente?",
        "¿Qué tal el clima hoy?",
    ]:
        print("\n>>", mensaje)
        print(procesar_mensaje_seguro(cadena, mensaje))