"""Bloque 21: primer agente del copiloto de pre-revisión.

Dos herramientas con propósitos distintos:
  - calcular_carga_ocupacion: CALCULA (Python puro, sin IA) la carga de ocupación.
  - consultar_reglas_informe: BUSCA qué dicen las reglas del informe favorable.
El agente (Gemini) decide cuál usar, en qué orden, o ninguna.
"""
import os

from dotenv import load_dotenv
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

from cadena_tres_pasos import REGLAS
from trazas import marcar_repeticiones_sospechosas, registrar_traza
from carga_ocupacion import (
    TABLA_M2_POR_PERSONA,
    UMBRAL_EDIFICIO_USO_PUBLICO,
    calcular_carga_total,
    es_edificio_uso_publico,
)


@tool
def calcular_carga_ocupacion(sectores: str) -> str:
    """Calcula la carga de ocupación (personas) de un edificio y dice si es
    edificio de uso público. Usar cuando la pregunta pide calcular cuántas
    personas ocupan un proyecto a partir de sus destinos y superficies.
    Formato de 'sectores': 'destino:m2; destino:m2', por ejemplo
    'oficinas:500; estacionamientos:816'."""
    try:
        pares = []
        for trozo in sectores.split(";"):
            if not trozo.strip():
                continue
            destino, superficie = trozo.split(":")
            pares.append((destino.strip().lower(), float(superficie)))
        if not pares:
            return "No recibí ningún sector. Usa el formato 'destino:m2; destino:m2'."
        carga = calcular_carga_total(pares)
    except KeyError as error:
        return (
            f"Destino no reconocido: {error}. Destinos válidos: "
            + ", ".join(TABLA_M2_POR_PERSONA)
        )
    except ValueError as error:
        return f"No pude calcular: {str(error).rstrip('.')}. Usa el formato 'destino:m2; destino:m2'."
    veredicto = "SÍ" if es_edificio_uso_publico(carga) else "NO"
    return (
        f"Carga de ocupación total: {round(carga, 1)} personas. "
        f"¿Edificio de uso público (más de {UMBRAL_EDIFICIO_USO_PUBLICO})? {veredicto}."
    )


# Cada regla de REGLAS (una línea que empieza con "- ") y las palabras que la activan.
_LINEAS_REGLAS = [l for l in REGLAS.split("\n") if l.startswith("- ")]
_TEMAS = {
    "obligatori": 0, "uso público": 0, "uso publico": 0, "116 bis": 0,
    "voluntari": 1, "rebaja": 1, "plazo": 1, "100 personas": 1, "beneficio": 1,
    "anteproyecto": 2,
    "vivienda social": 3, "social": 3, "exent": 3,
}


@tool
def consultar_reglas_informe(consulta: str) -> str:
    """Busca qué dicen las reglas sobre el informe favorable de revisor
    independiente: cuándo es obligatorio, cuándo es voluntario y su beneficio,
    anteproyecto y vivienda social. Usar cuando la pregunta es sobre la
    norma o los requisitos del informe, no cuando pide un cálculo."""
    texto = consulta.lower()
    indices = sorted({i for clave, i in _TEMAS.items() if clave in texto})
    if not indices:
        return "No encontré reglas sobre esa consulta. Derivar a revisión humana."
    return "\n".join(_LINEAS_REGLAS[i] for i in indices)


PROMPT_SISTEMA = (
    "Eres un asistente de pre-revisión de expedientes de arquitectura en Chile. "
    "Nunca calcules cargas de ocupación tú mismo: usa la herramienta de cálculo. "
    "Para preguntas de norma, responde SOLO con lo que devuelva la herramienta de "
    "reglas; si no hay información, dilo y indica que se deriva a revisión humana. "
    "Puedes usar más de una herramienta si la pregunta lo necesita. "
    "Si la pregunta es un saludo o no requiere herramientas, responde brevemente."
)


def construir_agente(modelo):
    herramientas = [calcular_carga_ocupacion, consultar_reglas_informe]
    prompt = ChatPromptTemplate.from_messages([
        ("system", PROMPT_SISTEMA),
        ("human", "{entrada}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])
    agente = create_tool_calling_agent(modelo, herramientas, prompt)
    return AgentExecutor(
        agent=agente,
        tools=herramientas,
        verbose=True,
        return_intermediate_steps=True,
    )


def herramientas_usadas(resultado) -> list:
    """Lee la traza: qué herramientas eligió el agente, en orden."""
    return [accion.tool for accion, _obs in resultado["intermediate_steps"]]


def texto_de(resultado) -> str:
    """Saca solo el texto de la respuesta, venga como str o como bloques de Gemini."""
    salida = resultado["output"]
    if isinstance(salida, str):
        return salida
    return "".join(
        bloque["text"] for bloque in salida
        if isinstance(bloque, dict) and bloque.get("type") == "text"
    )


def mostrar_traza(titulo, resultado):
    """Imprime la decisión del agente de forma legible, sin el texto crudo del modelo."""
    print(f"\n=== {titulo} ===")
    if not resultado["intermediate_steps"]:
        print("Herramientas usadas: ninguna")
    for n, (accion, observacion) in enumerate(resultado["intermediate_steps"], 1):
        print(f"{n}. {accion.tool}({accion.tool_input})")
        print(f"   -> {observacion}")
    print("RESPUESTA:", texto_de(resultado))


def preguntar(ejecutor, session_id, entrada):
    """Hace una pregunta al agente Y guarda su traza en trazas_agente.jsonl."""
    resultado = ejecutor.invoke({"entrada": entrada})
    registrar_traza(session_id, entrada, resultado)
    return resultado


if __name__ == "__main__":
    load_dotenv()
    modelo = ChatGoogleGenerativeAI(
        model="gemini-3.8-flash", google_api_key=os.getenv("GEMINI_API_KEY")
    )
    ejecutor = construir_agente(modelo)

    # Prueba 1: debería usar SOLO el cálculo.
    r1 = preguntar(ejecutor, "prueba_1", "Calcula la carga de ocupación de un edificio "
                   "con oficinas de 500 m2 y estacionamientos de 816 m2.")
    mostrar_traza("Prueba 1: cálculo", r1)
    assert herramientas_usadas(r1) == ["calcular_carga_ocupacion"], herramientas_usadas(r1)

    # Prueba 2: debería usar SOLO la búsqueda de reglas.
    r2 = preguntar(ejecutor, "prueba_2", "¿El informe favorable es obligatorio para "
                   "un anteproyecto?")
    mostrar_traza("Prueba 2: reglas", r2)
    assert herramientas_usadas(r2) == ["consultar_reglas_informe"], herramientas_usadas(r2)

    # Prueba 3: necesita las dos, una después de la otra (aquí solo se muestra).
    r3 = preguntar(ejecutor, "prueba_3", "Oficinas de 500 m2 y estacionamientos de "
                   "816 m2: ¿es obligatorio el informe favorable?")
    mostrar_traza("Prueba 3: cálculo + reglas", r3)

    # Prueba 4: no debería usar ninguna.
    r4 = preguntar(ejecutor, "prueba_4", "Hola, ¿en qué me puedes ayudar?")
    mostrar_traza("Prueba 4: sin herramientas", r4)
    assert herramientas_usadas(r4) == [], herramientas_usadas(r4)

    # Bloque 23: primera pasada automática sobre las trazas guardadas.
    print("\n=== Revisión de trazas ===")
    avisos = marcar_repeticiones_sospechosas()
    print("\n".join(avisos) if avisos else "Sin repeticiones sospechosas.")
