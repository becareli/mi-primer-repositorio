"""Bloque 27: evaluar la recuperación del copiloto con precisión y recall.

Idea de obra: hasta ahora mirabas "a ojo" si el bibliotecario traía las fichas
correctas. Esto es el CONTROL DE CALIDAD con números: 13 preguntas, cada una con
la ficha correcta marcada de antemano, y una nota para el bibliotecario.

   precisión = de las fichas que trajo, ¿cuántas servían?
   recall    = de las fichas que servían, ¿cuántas trajo?

REGLA DE ORO: las etiquetas (ids_relevantes) se escriben leyendo el CORPUS, antes de
ver qué devuelve el retriever. Si las ajustas después hasta que "dé bien", no mides nada.

Uso (desde la raíz del repositorio, con el entorno activado):
    python src\\evaluacion_recuperacion.py          # k=3, guarda resultados_evaluacion.txt
    python src\\evaluacion_recuperacion.py --k 5    # guarda resultados_evaluacion_k5.txt
"""
import sys
from datetime import date

from dotenv import load_dotenv

from indexar_corpus import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DIRECTORIO_VECTORES,
    abrir,
    crear_embeddings,
    explicar_error_red,
)

K_POR_DEFECTO = 3

# ---------------------------------------------------------------------------
# PASO 1. Conjunto de evaluación. Ids = los chunk_id de indexar_corpus.py
# (eup_definicion-1, informe_obligatorio-1, informe_voluntario-1, anteproyecto-1,
#  vivienda_social-1, tabla_ocupacion-1, tabla_ocupacion-2, alcance_copiloto-1).
# Etiquetado leyendo el texto del corpus, no el retriever. set() = sin respuesta.
# ---------------------------------------------------------------------------
CASOS_EVALUACION = [
    {"pregunta": "¿Qué es un edificio de uso público?",
     "ids_relevantes": {"eup_definicion-1"}},
    {"pregunta": "¿Qué dos condiciones debe cumplir un edificio para ser de uso público?",
     "ids_relevantes": {"eup_definicion-1"}},
    {"pregunta": "¿Es obligatorio el informe favorable para un edificio de uso público?",
     "ids_relevantes": {"informe_obligatorio-1"}},
    {"pregunta": "¿Qué pasa si falta el informe favorable en un edificio de uso público?",
     "ids_relevantes": {"informe_obligatorio-1"}},
    {"pregunta": "¿Qué rebaja en los derechos municipales da el informe favorable?",
     "ids_relevantes": {"beneficios_informe-1"}},
    {"pregunta": "¿En cuántos días hábiles revisa la Dirección de Obras con informe favorable del Revisor Independiente?",
     "ids_relevantes": {"beneficios_informe-1"}},
    {"pregunta": "¿Puedo pedir la revisión de un anteproyecto a un revisor independiente?",
     "ids_relevantes": {"anteproyecto-1"}},
    {"pregunta": "¿La vivienda social necesita informe favorable?",
     "ids_relevantes": {"vivienda_social-1"}},
    {"pregunta": "¿Cuántos metros cuadrados por persona se cuentan en una oficina?",
     "ids_relevantes": {"tabla_ocupacion-1"}},
    {"pregunta": "¿Cómo se calcula la carga de ocupación total de un edificio?",
     "ids_relevantes": {"eup_definicion-1"}},
    {"pregunta": "¿Quién firma el informe favorable?",
     "ids_relevantes": {"alcance_copiloto-1"}},
    {"pregunta": "¿El copiloto calcula la carga de ocupación con el modelo de lenguaje?",
     "ids_relevantes": {"tabla_ocupacion-2"}},
    # Dos chunks relevantes: la regla de las 100 personas vive en dos documentos.
    {"pregunta": "¿Un edificio con carga de ocupación de 80 personas necesita informe favorable?",
     "ids_relevantes": {"informe_voluntario-1", "eup_definicion-1"}},
    # Descuento en Derechos Municipales del 30%
    {"pregunta": "¿La rebaja del 30% aplica también si el Informe es Obligatorio?",
     "ids_relevantes": {"beneficios_informe-1"}},
    # Sin respuesta en el corpus: recall = None, se ignora en el promedio de recall.
    {"pregunta": "¿Qué ancho mínimo debe tener una escalera de evacuación?",
     "ids_relevantes": set()},
]


# ---------------------------------------------------------------------------
# PASO 2. Métricas (con validaciones para casos borde)
# ---------------------------------------------------------------------------
def precision_at_k(ids_recuperados, ids_relevantes):
    """Fracción de los ids recuperados que son relevantes (0.0 si no hay ninguno)."""
    if not ids_recuperados:
        return 0.0
    acertados = [i for i in ids_recuperados if i in ids_relevantes]
    return len(acertados) / len(ids_recuperados)


def recall_at_k(ids_recuperados, ids_relevantes):
    """Fracción de los ids relevantes que se recuperaron (None si no hay relevantes)."""
    if not ids_relevantes:
        return None
    acertados = [i for i in ids_recuperados if i in ids_relevantes]
    return len(acertados) / len(ids_relevantes)


def promediar(valores):
    """Promedio que ignora los None y evita dividir por cero."""
    validos = [v for v in valores if v is not None]
    return sum(validos) / len(validos) if validos else 0.0


def evaluar_recuperacion(retriever, casos, k=K_POR_DEFECTO):
    """Corre cada caso contra el retriever real y promedia precisión y recall."""
    resultados = []
    for caso in casos:
        chunks = retriever.invoke(caso["pregunta"])
        ids_recuperados = [c.id for c in chunks][:k]
        if any(i is None for i in ids_recuperados):
            raise ValueError("Hay chunks sin id: reindexa con ids explícitos.")
        resultados.append({
            "pregunta": caso["pregunta"],
            "ids_recuperados": ids_recuperados,
            "precision": precision_at_k(ids_recuperados, caso["ids_relevantes"]),
            "recall": recall_at_k(ids_recuperados, caso["ids_relevantes"]),
        })
    p_prom = promediar(r["precision"] for r in resultados)
    r_prom = promediar(r["recall"] for r in resultados)
    return resultados, p_prom, r_prom


def _recall_txt(recall):
    return "n/a" if recall is None else f"{recall:.2f}"


# ---------------------------------------------------------------------------
# PASO 3. Guardar el registro de la corrida (para comparar la próxima vez)
# ---------------------------------------------------------------------------
def guardar_resultados(resultados, p_prom, r_prom, k, archivo):
    with open(archivo, "w", encoding="utf-8") as f:
        f.write(f"Fecha: {date.today()}\n")
        f.write(f"Configuracion: k={k}, chunk_size={CHUNK_SIZE}, chunk_overlap={CHUNK_OVERLAP}\n\n")
        for r in resultados:
            f.write(f"{r['precision']:.2f} {_recall_txt(r['recall'])} {r['pregunta']}\n")
        f.write(f"\npromedio -> precision: {p_prom:.3f} recall: {r_prom:.3f}\n")


def main(argumentos):
    load_dotenv()
    k = int(argumentos[argumentos.index("--k") + 1]) if "--k" in argumentos else K_POR_DEFECTO
    archivo = "resultados_evaluacion.txt" if k == K_POR_DEFECTO else f"resultados_evaluacion_k{k}.txt"
    try:
        almacen = abrir(crear_embeddings(), DIRECTORIO_VECTORES)
        total = almacen._collection.count()
        if total == 0:
            raise SystemExit(f"{DIRECTORIO_VECTORES}/ está vacío: corre indexar_corpus.py primero.")
        print(f"Índice: {total} chunks. Evaluando {len(CASOS_EVALUACION)} casos con k={k}\n")
        retriever = almacen.as_retriever(search_kwargs={"k": k})
        resultados, p_prom, r_prom = evaluar_recuperacion(retriever, CASOS_EVALUACION, k=k)
    except SystemExit:
        raise
    except Exception as error:
        print("No se pudo evaluar:", explicar_error_red(error))
        raise SystemExit(1)

    for r in resultados:
        print(f"{r['precision']:.2f} {_recall_txt(r['recall']):>4}  {r['pregunta']}")
        print(f"            trajo: {r['ids_recuperados']}")
    print(f"\npromedio -> precision: {p_prom:.3f} recall: {r_prom:.3f}")
    guardar_resultados(resultados, p_prom, r_prom, k, archivo)
    print(f"Resultados guardados en {archivo}")


if __name__ == "__main__":
    main(sys.argv[1:])
