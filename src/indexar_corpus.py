"""Bloque 24: indexar el corpus del copiloto del informe favorable.

Idea de obra: esto es la BIBLIOTECA del copiloto. Se arma una sola vez:
  1) corpus  -> los documentos de normas y criterios (con su fuente)
  2) chunking -> se cortan en trozos del tamaño de una ficha
  3) embeddings -> cada trozo se convierte en un vector (coordenadas de "significado")
  4) Chroma -> los vectores se guardan en disco (carpeta vectorstore/)
Después, cada pregunta solo CONSULTA la biblioteca; no la vuelve a construir.

Uso (desde la raíz del repositorio, con el entorno activado):
    python src\\indexar_corpus.py              # indexa si no existe; si existe, solo verifica
    python src\\indexar_corpus.py --reindexar  # borra vectorstore/ y reconstruye
"""
import os
import shutil
import sys

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

load_dotenv()  # lee el archivo .env y deja GOOGLE_API_KEY disponible


DIRECTORIO_VECTORES = "vectorstore"
MODELO_EMBEDDINGS = "models/gemini-embedding-001"
CHUNK_SIZE = 500      # caracteres por trozo
CHUNK_OVERLAP = 75    # 15% de CHUNK_SIZE: solapa un poco entre trozos vecinos

# ---------------------------------------------------------------------------
# 1) CORPUS. Cada documento lleva su fuente y su estado de verificación, para
#    que el copiloto pueda citar y para no presentar como firme lo que no lo es.
#    Estados (los mismos de docs/tabla_supuestos.md): VERIFICADO / LECTURA /
#    PENDIENTE / CRITERIO. Mientras una regla no esté VERIFICADA contra la
#    fuente primaria, la respuesta debe decir que es orientativa.
# ---------------------------------------------------------------------------
CORPUS = [
    {
        "id": "eup_definicion",
        "fuente": "OGUC art. 1.1.2",
        "estado": "LECTURA",
        "texto": (
            "Edificio de uso público (EUP): edificio destinado a equipamiento "
            "cuya carga de ocupación total es mayor a 100 personas. Las dos "
            "condiciones deben cumplirse a la vez: que el destino sea de "
            "equipamiento y que la carga de ocupación total supere 100. "
            "La carga de ocupación se calcula sumando, por cada destino, la "
            "superficie dividida por los metros cuadrados por persona de la "
            "tabla de carga de ocupación."
        ),
    },
    {
        "id": "informe_obligatorio",
        "fuente": "LGUC art. 116 bis (lectura secundaria)",
        "estado": "PENDIENTE",
        "texto": (
            "El informe favorable de un revisor independiente de arquitectura "
            "es obligatorio para los edificios de uso público. Sin el informe "
            "favorable la Dirección de Obras Municipales no puede otorgar el "
            "permiso de edificación de esos edificios."
        ),
    },
    {
        "id": "informe_voluntario",
        "fuente": "Dictamen secundario (verificar fuente primaria)",
        "estado": "PENDIENTE",
        "texto": (
            "Cuando la carga de ocupación es de 100 personas o menos, el informe "
            "del revisor independiente es voluntario: el propietario puede "
            "optar por solicitarlo."
        ),
    },
        {
        "id": "beneficios_informe",
        "fuente": "Dictamen secundario (verificar fuente primaria)",
        "estado": "PENDIENTE",
        "texto": (
            "Beneficios de contar con informe favorable de un revisor "
            "independiente, tanto cuando es obligatorio como cuando es "
            "voluntario: rebaja de 30% en los derechos municipales y plazo "
            "de revisión de la Dirección de Obras Municipales de 15 días hábiles."
        ),
    },
    {
        "id": "anteproyecto",
        "fuente": "OGUC art. 5.1.5 (lectura secundaria)",
        "estado": "PENDIENTE",
        "texto": (
            "La revisión de un anteproyecto por un revisor independiente es "
            "voluntaria. Permite validar la normativa urbanística antes de "
            "desarrollar el proyecto completo y reduce el riesgo de observaciones "
            "tardías."
        ),
    },
    {
        "id": "vivienda_social",
        "fuente": "LGUC art. 116 bis A (lectura secundaria)",
        "estado": "PENDIENTE",
        "texto": (
            "La vivienda social tiene un régimen especial: está exenta del "
            "informe favorable del revisor independiente o se rige por un "
            "procedimiento particular. Antes de aplicar esta excepción hay que "
            "confirmar que el proyecto califica como vivienda social."
        ),
    },
    {
        "id": "tabla_ocupacion",
        "fuente": "OGUC art. 4.2.4 (tabla; versión impresa marzo 2016, verificar vigencia)",
        "estado": "LECTURA",
        "texto": (
            "Tabla de carga de ocupación: metros cuadrados por persona según el "
            "destino.\n\n"
            "Oficinas: 10 m2 por persona. Gimnasios: 4 m2 por persona. "
            "Restaurantes: 1,5 m2 por persona. Bares: 1 m2 por persona. "
            "Salones de reuniones: 0,8 m2 por persona.\n\n"
            "Hoteles: 18 m2 por persona. Estacionamientos: 16 m2 por persona. "
            "Bodegas: 40 m2 por persona. Hogares de ancianos: 6 m2 por persona.\n\n"
            "Estos valores son de ejemplo para el corpus. La fuente de verdad "
            "para el cálculo es src/carga_ocupacion.py: el cálculo lo hace "
            "Python, nunca el modelo."
        ),
    },
    {
        "id": "alcance_copiloto",
        "fuente": "docs/limites_autonomia_agente.md",
        "estado": "CRITERIO",
        "texto": (
            "El copiloto es un asistente de pre-revisión. No decide ni firma "
            "nada: el informe favorable lo emite y firma el arquitecto revisor "
            "independiente. Toda salida del copiloto pasa por revisión humana "
            "antes de llegar a un cliente. Si la información disponible no "
            "alcanza para responder, se debe contactar a un Arquitecto Revisor Independiente en vez de "
            "inventar una respuesta."
        ),
    },
]


# ---------------------------------------------------------------------------
# 2) Funciones pequeñas, una por etapa (así cada una se puede probar sola).
# ---------------------------------------------------------------------------
def construir_documentos(corpus=CORPUS):
    """Convierte cada entrada del corpus en un Document: texto + metadatos."""
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
    return chunks


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

    return GoogleGenerativeAIEmbeddings(model=MODELO_EMBEDDINGS)


def explicar_error_red(error):
    """Distingue 'esperar' (cuota) de 'corregir' (clave u otro problema)."""
    texto = str(error)
    if "429" in texto or "RESOURCE_EXHAUSTED" in texto:
        return "Se agotó la cuota por minuto/día. No es un error tuyo: espera un rato y reintenta."
    if "API key" in texto or "API_KEY" in texto or "403" in texto or "401" in texto:
        return "La clave de API falta o es inválida. Revisa GOOGLE_API_KEY."
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
            print(f"\n{DIRECTORIO_VECTORES}/ ya existe: no se vuelve a indexar.")
            almacen = abrir(embeddings)
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
