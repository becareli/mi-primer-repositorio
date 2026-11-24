"""Pruebas SIN red del registro de latencia y costo."""
import json
import time

import pytest

import indexar_corpus as ic
import registro_rag as rr
from test_indexar_corpus import EmbeddingsFalsos


class Respuesta:
    def __init__(self, usage):
        self.content = "ok"
        self.usage_metadata = usage


class ModeloFalso:
    """Imita al modelo: la entrada de tokens crece con el largo del prompt."""

    def __init__(self, usage=True):
        self.usage = usage

    def invoke(self, prompt):
        time.sleep(0.01)  # la generación "tarda" más que la búsqueda local
        if not self.usage:
            return Respuesta(None)
        n = len(prompt) // 4
        return Respuesta({"input_tokens": n, "output_tokens": 40, "total_tokens": n + 40})


@pytest.fixture
def almacen(tmp_path):
    carpeta = str(tmp_path / "vs")
    ic.indexar(ic.partir_en_chunks(ic.construir_documentos()), EmbeddingsFalsos(), carpeta)
    return ic.abrir(EmbeddingsFalsos(), carpeta)


def test_medir_guarda_segundos():
    t = {}
    with rr.medir(t, "x"):
        time.sleep(0.01)
    assert t["x"] >= 0.01


def test_registro_tiene_las_claves_y_tres_etapas(almacen):
    reg = rr.registrar_consulta("pregunta", 3, EmbeddingsFalsos(), almacen, ModeloFalso())
    for clave in ("timestamp", "pregunta_len", "pregunta_huella", "k", "tiempos_ms", "tiempo_total_ms", "tokens"):
        assert clave in reg
    assert "pregunta" not in reg  # gobernanza: el texto de la consulta no se guarda
    assert list(reg["tiempos_ms"]) == ["embed_query", "busqueda_vectorial", "generacion"]
    assert reg["tiempo_total_ms"] == pytest.approx(sum(reg["tiempos_ms"].values()), abs=0.05)
    assert reg["tiempos_ms"]["generacion"] > reg["tiempos_ms"]["busqueda_vectorial"]


def test_subir_k_sube_los_tokens_de_entrada(almacen):
    a = rr.registrar_consulta("pregunta", 3, EmbeddingsFalsos(), almacen, ModeloFalso())
    b = rr.registrar_consulta("pregunta", 6, EmbeddingsFalsos(), almacen, ModeloFalso())
    assert b["tokens"]["input_tokens"] > a["tokens"]["input_tokens"]


def test_sin_usage_metadata_guarda_null(almacen):
    reg = rr.registrar_consulta("p", 3, EmbeddingsFalsos(), almacen, ModeloFalso(usage=False))
    assert reg["tokens"] is None and reg["costo_usd"] is None


def test_estimar_costo():
    t = {"input_tokens": 1000, "output_tokens": 500}
    assert rr.estimar_costo(t, 2.0, 10.0) == pytest.approx(0.002 + 0.005)
    assert rr.estimar_costo(t, None, 10.0) is None
    assert rr.estimar_costo(None, 2.0, 10.0) is None


def test_guardar_agrega_una_linea_por_corrida(tmp_path, almacen):
    f = str(tmp_path / "r.jsonl")
    for _ in range(3):
        rr.guardar_registro(rr.registrar_consulta("p", 3, EmbeddingsFalsos(), almacen, ModeloFalso()), f)
    lineas = open(f, encoding="utf-8").read().splitlines()
    assert len(lineas) == 3
    assert all(json.loads(x)["k"] == 3 for x in lineas)
