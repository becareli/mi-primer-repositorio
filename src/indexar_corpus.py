"""Bloque 24: indexar el corpus del copiloto del informe favorable.

Idea de obra: esto es la BIBLIOTECA del copiloto. Se arma una sola vez:
  1) corpus  -> los documentos de normas y criterios (con su fuente)
  2) chunking -> se cortan en trozos del tamaño de una ficha
  3) embeddings -> cada trozo se convierte en un vector (coordenadas de "significado")
  4) Chroma -> los vectores se guardan en disco (carpeta vectorstore/)
Después, cada pregunta solo CONSULTA la biblioteca; no la vuelve a construir.

Uso (desde la raíz del repositorio, con el entorno activado):
    python src\\indexar_corpus.py              # indexa si no existe; si existe, actualiza solo lo que cambió
    python src\\indexar_corpus.py --reindexar  # borra vectorstore/ y reconstruye
"""
import hashlib
import os
import shutil
import sys

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

load_dotenv()  # lee el archivo .env y deja GEMINI_API_KEY disponible


DIRECTORIO_VECTORES = "vectorstore"
MODELO_EMBEDDINGS = "models/gemini-embedding-001"
CHUNK_SIZE = 500      # caracteres por trozo
CHUNK_OVERLAP = 75    # 15% de CHUNK_SIZE: solapa un poco entre trozos vecinos

# ---------------------------------------------------------------------------
# 1) CORPUS. Vive en la carpeta corpus/: un archivo .md por documento, con su
#    fuente y su estado de verificación en la cabecera. Para agregar o corregir
#    un documento se edita esa carpeta, no el código.
#    Estados: VERIFICADO (contrastado con el texto legal vigente) / LECTURA /
#    PENDIENTE / CRITERIO (criterio propio de ArquitectoChile).
# ---------------------------------------------------------------------------
CARPETA_CORPUS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "corpus")


def leer_documento_md(ruta):
    """Lee un .md con cabecera '---' (id, fuente, estado) y devuelve un dict."""
    with open(ruta, encoding="utf-8") as f:
        _, cabecera, texto = f.read().split("---", 2)
    datos = {}
    for linea in cabecera.strip().splitlines():
        clave, valor = linea.split(":", 1)
        datos[clave.strip()] = valor.strip()
    datos["texto"] = texto.strip()
    return datos


def cargar_corpus(carpeta=CARPETA_CORPUS):
    """Todos los .md de la carpeta, en orden alfabético (orden estable)."""
    return [
        leer_documento_md(os.path.join(carpeta, nombre))
        for nombre in sorted(os.listdir(carpeta))
        if nombre.endswith(".md")
    ]


CORPUS = cargar_corpus()


# ---------------------------------------------------------------------------
# 2) Funciones pequeñas, una por etapa (así cada una se puede probar sola).
# ---------------------------------------------------------------------------
def construir_documentos(corpus=None):
    """Convierte cada entrada del corpus en un Document: texto + metadatos."""
    corpus = CORPUS if corpus is None else corpus
    return [
        Document(
            page_content=c["texto"],
            metadata={"doc_id": c["id"], "fuente": c["fuente"], "estado": c["estado"]},
        )
        for c in corpus
    ]


def partir_en_chunks(documentos, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
    """Corta los documentos en trozos. Recursivo: prefiere cortar en párrafos."""
    cortador = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    chunks = cortador.split_documents(documentos)  # conserva los metadatos
    contador = {}
    for chunk in chunks:
        doc_id = chunk.metadata["doc_id"]
        contador[doc_id] = contador.get(doc_id, 0) + 1
        chunk.metadata["chunk_id"] = f"{doc_id}-{contador[doc_id]}"
        chunk.metadata["huella"] = huella_chunk(chunk)
    return chunks


def huella_chunk(chunk):
    """Huella del texto + fuente + estado: si cambia cualquiera, el chunk cambió."""
    base = chunk.page_content + chunk.metadata["fuente"] + chunk.metadata["estado"]
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:12]


def sincronizar(almacen, chunks):
    """Bloque 25: actualización INCREMENTAL. Solo toca lo que cambió.

    Compara la huella de cada chunk con la que ya está en disco:
      nuevo      -> se agrega
      modificado -> se reemplaza (mismo id, nueva huella)
      eliminado  -> se borra del índice
    Devuelve un resumen con cuántos de cada tipo hubo.
    """
    guardado = almacen.get(include=["metadatas"])
    en_disco = {i: (m or {}).get("huella") for i, m in zip(guardado["ids"], guardado["metadatas"])}
    actuales = {c.metadata["chunk_id"]: c for c in chunks}

    nuevos = [c for i, c in actuales.items() if i not in en_disco]
    modificados = [c for i, c in actuales.items() if i in en_disco and en_disco[i] != c.metadata["huella"]]
    eliminados = [i for i in en_disco if i not in actuales]

    if modificados or eliminados:
        almacen.delete(ids=[c.metadata["chunk_id"] for c in modificados] + eliminados)
    if nuevos or modificados:
        por_agregar = nuevos + modificados
        almacen.add_documents(por_agregar, ids=[c.metadata["chunk_id"] for c in por_agregar])
    return {"nuevos": len(nuevos), "modificados": len(modificados),
            "eliminados": len(eliminados), "sin_cambios": len(actuales) - len(nuevos) - len(modificados)}


def indexar(chunks, embeddings, directorio=DIRECTORIO_VECTORES):
    """Calcula los embeddings y guarda todo en disco. Los ids fijos evitan duplicados."""
    return Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        ids=[c.metadata["chunk_id"] for c in chunks],
        persist_directory=directorio,
    )


def abrir(embeddings, directorio=DIRECTORIO_VECTORES):
    """Reconecta con un vector store ya guardado, SIN volver a calcular embeddings."""
    return Chroma(persist_directory=directorio, embedding_function=embeddings)


def hay_indice(directorio=DIRECTORIO_VECTORES):
    return os.path.isdir(directorio) and bool(os.listdir(directorio))


def crear_embeddings():
    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    # La clave se pasa explícita: así basta con GEMINI_API_KEY en el .env.
    return GoogleGenerativeAIEmbeddings(
        model=MODELO_EMBEDDINGS, google_api_key=os.getenv("GEMINI_API_KEY")
    )


def explicar_error_red(error):
    """Distingue 'esperar' (cuota) de 'corregir' (clave u otro problema)."""
    texto = str(error)
    if "429" in texto or "RESOURCE_EXHAUSTED" in texto:
        return "Se agotó la cuota por minuto/día. No es un error tuyo: espera un rato y reintenta."
    if "API key" in texto or "API_KEY" in texto or "403" in texto or "401" in texto:
        return "La clave de API falta o es inválida. Revisa GEMINI_API_KEY en tu .env."
    return f"Error inesperado al llamar a Gemini: {texto[:200]}"


# ---------------------------------------------------------------------------
# 3) Programa principal
# ---------------------------------------------------------------------------
def main(argumentos):
    if "--reindexar" in argumentos and os.path.isdir(DIRECTORIO_VECTORES):
        shutil.rmtree(DIRECTORIO_VECTORES)
        print(f"Se borró {DIRECTORIO_VECTORES}/ para reconstruir.")

    embeddings = crear_embeddings()

    documentos = construir_documentos()
    chunks = partir_en_chunks(documentos)
    print(f"Corpus: {len(documentos)} documentos -> {len(chunks)} chunks")
    for c in chunks:
        print(f"  {c.metadata['chunk_id']:<26} {len(c.page_content):>4} caracteres")

    try:
        if hay_indice():
            almacen = abrir(embeddings)
            resumen = sincronizar(almacen, chunks)
            print(f"\n{DIRECTORIO_VECTORES}/ ya existe: actualización incremental -> {resumen}")
        else:
            print("\nCalculando embeddings y guardando (llama a la red)...")
            almacen = indexar(chunks, embeddings)
        total = almacen._collection.count()
        print(f"Chunks guardados en disco: {total}")

        # Prueba de reconexión: abrir de nuevo desde disco, como lo hará la consulta.
        reabierto = abrir(embeddings)
        print(f"Tras reabrir desde disco: {reabierto._collection.count()} chunks")

        pregunta = "¿Cuándo es obligatorio el informe favorable?"
        print(f"\nPregunta de prueba: {pregunta}")
        for r in reabierto.similarity_search(pregunta, k=2):
            print(f"  [{r.metadata['chunk_id']}] ({r.metadata['fuente']}, {r.metadata['estado']})")
            print(f"     {r.page_content[:110]}...")
    except Exception as error:  # solo la llamada de red está protegida
        print("\nNo se pudo indexar:", explicar_error_red(error))
        raise SystemExit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
