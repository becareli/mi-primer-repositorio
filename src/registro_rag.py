"""Bloque 28 (Core): registrar la latencia y el costo del flujo RAG del copiloto.

Idea de obra: es el CRONÓMETRO Y EL MEDIDOR DE CONSUMO de la ventanilla de consulta.
Cada consulta pasa por tres etapas y se mide cada una por separado:
   1) embed_query        -> convertir la pregunta en vector        (red)
   2) busqueda_vectorial -> buscar los k trozos más cercanos       (local, tu PC)
   3) generacion         -> el modelo lee el prompt y responde     (red)
Además se guardan los tokens REALES que reporta la API (no una aproximación por
caracteres). Cada corrida queda como UNA línea en registros_latencia_costo.jsonl.

Uso (desde la raíz del repositorio, con el entorno activado):
    python src\\registro_rag.py        # 3 preguntas con k=3 y 1 pregunta repetida con k=6
"""
import hashlib
import json
import os
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone

from dotenv import load_dotenv

from indexar_corpus import DIRECTORIO_VECTORES, abrir, crear_embeddings, explicar_error_red
from recuperacion import MODELO_CHAT, PROMPT_TEMPLATE, formatear_contexto

ARCHIVO_REGISTROS = "registros_latencia_costo.jsonl"

# Tarifa introductoria de gemini-3.8-flash, USD por 1.000.000 de tokens.
# Vigente hasta el 31-dic-2026; desde el 1-ene-2027 sube a 1.50 y 7.50.
# Fuente: ai.google.dev/gemini-api/docs/whats-new-gemini-3.8 (consultada 17-nov-2026)
TARIFA_ENTRADA_POR_MILLON = 0.75
TARIFA_SALIDA_POR_MILLON = 3.75


@contextmanager
def medir(tiempos, etapa):
    """Cronómetro: guarda en tiempos[etapa] cuántos segundos duró el bloque 'with'."""
    inicio = time.perf_counter()
    try:
        yield
    finally:
        tiempos[etapa] = time.perf_counter() - inicio


def estimar_costo(tokens, tarifa_entrada, tarifa_salida):
    """Costo = entrada x tarifa_entrada + salida x tarifa_salida (None si faltan datos)."""
    if not tokens or tarifa_entrada is None or tarifa_salida is None:
        return None
    entrada = tokens.get("input_tokens", 0)
    salida = tokens.get("output_tokens", 0)
    return round(entrada / 1e6 * tarifa_entrada + salida / 1e6 * tarifa_salida, 8)


def registrar_consulta(pregunta, k, embeddings, almacen, modelo):
    """Corre UNA consulta RAG real midiendo cada etapa. Devuelve el registro (dict)."""
    tiempos = {}
    with medir(tiempos, "embed_query"):
        vector = embeddings.embed_query(pregunta)
    with medir(tiempos, "busqueda_vectorial"):
        chunks = almacen.similarity_search_by_vector(vector, k=k)
    contexto, _citas = formatear_contexto(chunks)
    prompt = PROMPT_TEMPLATE.format(contexto=contexto, pregunta=pregunta)
    with medir(tiempos, "generacion"):
        respuesta = modelo.invoke(prompt)

    tokens = dict(respuesta.usage_metadata) if getattr(respuesta, "usage_metadata", None) else None
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        # Gobernanza (Gate 2): se guarda el largo y una huella, nunca el texto de la consulta.
        "pregunta_len": len(pregunta),
        "pregunta_huella": hashlib.sha256(pregunta.encode("utf-8")).hexdigest()[:12],
        "k": k,
        "modelo": MODELO_CHAT,
        "tiempos_ms": {etapa: round(s * 1000, 2) for etapa, s in tiempos.items()},
        "tiempo_total_ms": round(sum(tiempos.values()) * 1000, 2),
        "tokens": tokens,
        "costo_usd": estimar_costo(tokens, TARIFA_ENTRADA_POR_MILLON, TARIFA_SALIDA_POR_MILLON),
    }


def guardar_registro(registro, archivo=ARCHIVO_REGISTROS):
    """Agrega UNA línea JSON (JSON Lines). 'a' = append: nunca borra lo anterior."""
    with open(archivo, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")


# 3 preguntas de largo y zona distintos (del conjunto de evaluación del Bloque 27)
PREGUNTAS = [
    "¿Qué es un edificio de uso público?",
    "¿Cuántos metros cuadrados por persona se cuentan en una oficina?",
    "¿Un edificio con carga de ocupación de 80 personas necesita informe favorable?",
]
CORRIDAS = [(p, 3) for p in PREGUNTAS] + [(PREGUNTAS[2], 6)]  # la última prueba k=6


def main():
    load_dotenv()
    if not os.environ.get("GEMINI_API_KEY"):
        raise SystemExit('Falta GEMINI_API_KEY. Defínela en tu archivo ".env".')
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI

        embeddings = crear_embeddings()
        almacen = abrir(embeddings, DIRECTORIO_VECTORES)
        modelo = ChatGoogleGenerativeAI(
            model=MODELO_CHAT, google_api_key=os.getenv("GEMINI_API_KEY"), temperature=0
        )
        for pregunta, k in CORRIDAS:
            registro = registrar_consulta(pregunta, k, embeddings, almacen, modelo)
            guardar_registro(registro)
            print(json.dumps(registro, indent=2, ensure_ascii=False))
    except Exception as error:
        print("\nNo se pudo registrar:", explicar_error_red(error))
        raise SystemExit(1)
    print(f"\nRegistros agregados a {ARCHIVO_REGISTROS}")


if __name__ == "__main__":
    main()
