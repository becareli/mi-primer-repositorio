"""Bloque 26: recuperación semántica + prompt dinámico con fuente citada.

Idea de obra: en el Bloque 24 construimos la BIBLIOTECA (indexar_corpus.py).
Ahora armamos la VENTANILLA de consulta, que hace tres cosas:
  1) RECUPERAR  -> dada una pregunta, traer los k trozos más cercanos en significado
  2) NUMERAR    -> [1], [2], [3] + un mapa número -> fuente, para poder citar
  3) INSTRUIR   -> un prompt que obliga al modelo a usar SOLO ese contexto y a citarlo

Regla de oro: esta ventanilla NUNCA reindexa. Solo reabre lo que ya está en disco.

Uso (desde la raíz del repositorio, con el entorno activado):
    python src\\recuperacion.py             # corre 3 preguntas y muestra las respuestas
    python src\\recuperacion.py --prompt    # además imprime el prompt completo
"""
import os
import sys

from dotenv import load_dotenv

from indexar_corpus import (
    DIRECTORIO_VECTORES,
    abrir,
    crear_embeddings,
    explicar_error_red,
)

MODELO_CHAT = "gemini-3.8-flash"  # el mismo que usa tu agente
K_POR_DEFECTO = 3  # el curso recomienda empezar con k=3 o k=4

PROMPT_TEMPLATE = """Eres el asistente de pre-revisión de un arquitecto revisor independiente.
No decides ni firmas nada: tu respuesta es un insumo para el arquitecto.

Responde la pregunta usando SOLO el contexto de abajo. Cita la fuente de cada
afirmacion con su numero entre corchetes, como [1].
Si el contexto marca una regla como PENDIENTE o LECTURA, di que es orientativa y
que esta por verificar. No calcules cargas de ocupacion tu mismo: el calculo lo
hace la calculadora del sistema.
Si el contexto no alcanza para responder, dilo explicitamente y deriva a
un Arquitecto Revisor Independiente, en vez de inventar.

Contexto:
{contexto}

Pregunta: {pregunta}

Respuesta:"""


def formatear_contexto(chunks_recuperados):
    """Arma el bloque numerado para el prompt y el mapa numero -> fuente."""
    lineas = []
    citas = {}
    for i, doc in enumerate(chunks_recuperados, start=1):
        fuente = doc.metadata.get("fuente", "desconocida")
        estado = doc.metadata.get("estado", "sin estado")
        lineas.append(f"[{i}] {doc.page_content} (estado de verificacion: {estado})")
        citas[i] = fuente
    return "\n\n".join(lineas), citas


def verificar_citas(citas, k):
    """Los controles de 'qué debe cumplirse siempre'. Falla con un mensaje claro."""
    if list(citas) != list(range(1, k + 1)):
        raise ValueError(f"citas debe tener las claves 1..{k}, tiene {list(citas)}")
    sin_fuente = [n for n, f in citas.items() if f == "desconocida"]
    if sin_fuente:
        raise ValueError(
            f"Los chunks {sin_fuente} no tienen 'fuente': hay que reindexar con metadata."
        )


def construir_prompt(
    pregunta, persist_directory=DIRECTORIO_VECTORES, k=K_POR_DEFECTO, embeddings=None
):
    """Reabre el indice, recupera los k chunks mas cercanos y arma el prompt."""
    if embeddings is None:
        embeddings = crear_embeddings()
    almacen = abrir(embeddings, persist_directory)  # reconecta: NO from_documents
    recuperador = almacen.as_retriever(search_kwargs={"k": k})
    chunks_recuperados = recuperador.invoke(pregunta)
    contexto, citas = formatear_contexto(chunks_recuperados)
    prompt = PROMPT_TEMPLATE.format(contexto=contexto, pregunta=pregunta)
    return prompt, citas


def _texto(contenido):
    """Gemini a veces devuelve una lista de bloques en vez de un str."""
    if isinstance(contenido, str):
        return contenido
    return "".join(
        b.get("text", "") if isinstance(b, dict) else str(b) for b in contenido
    )


def responder(pregunta, persist_directory=DIRECTORIO_VECTORES, k=K_POR_DEFECTO):
    """Prompt con citas -> modelo -> (respuesta, citas)."""
    from langchain_google_genai import ChatGoogleGenerativeAI

    prompt, citas = construir_prompt(pregunta, persist_directory, k)
    verificar_citas(citas, k)
    modelo = ChatGoogleGenerativeAI(
        model=MODELO_CHAT, google_api_key=os.getenv("GEMINI_API_KEY"), temperature=0
    )
    respuesta = _texto(modelo.invoke(prompt).content)
    return respuesta, citas


PREGUNTAS_DE_PRUEBA = [
    # 1 y 2: preguntas distintas, el contexto recuperado debe CAMBIAR entre una y otra
    "¿Cuándo es obligatorio el informe favorable?",
    "¿Cuántos metros cuadrados por persona se cuentan en un restaurante?",
    # 3: el corpus NO la puede responder; el modelo debe decirlo y derivar
    "¿Qué ancho mínimo debe tener una escalera de evacuación?",
]


def main(argumentos):
    load_dotenv()
    if not os.environ.get("GEMINI_API_KEY"):
        raise SystemExit('Falta GEMINI_API_KEY. Defínela en tu archivo ".env".')
    try:
        for pregunta in PREGUNTAS_DE_PRUEBA:
            print("=" * 70)
            print("Pregunta:", pregunta)
            if "--prompt" in argumentos:
                prompt, _ = construir_prompt(pregunta)
                print("\n--- PROMPT ---\n" + prompt + "\n--------------")
            respuesta, citas = responder(pregunta)
            print("Citas:", citas)
            print("Respuesta:", respuesta)
    except Exception as error:
        print("\nNo se pudo consultar:", explicar_error_red(error))
        raise SystemExit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
