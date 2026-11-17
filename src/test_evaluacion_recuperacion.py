"""Pruebas SIN red de la evaluación de recuperación."""
import pytest
from langchain_core.documents import Document

import evaluacion_recuperacion as ev
import indexar_corpus as ic
from test_indexar_corpus import EmbeddingsFalsos


def test_metricas_caso_del_curso():
    assert ev.precision_at_k(["doc2", "doc0", "doc4"], {"doc0"}) == pytest.approx(1 / 3)
    assert ev.recall_at_k(["doc2", "doc0", "doc4"], {"doc0"}) == 1.0


def test_casos_borde():
    assert ev.precision_at_k([], {"a"}) == 0.0
    assert ev.recall_at_k(["a"], set()) is None
    assert ev.promediar([None, None]) == 0.0
    assert ev.promediar([1.0, None, 0.0]) == 0.5


def test_conjunto_tiene_entre_8_y_15_casos():
    assert 8 <= len(ev.CASOS_EVALUACION) <= 15


def test_ids_relevantes_son_sets_y_existen_en_el_corpus():
    """Atrapa errores de tipeo en las etiquetas ANTES de gastar una llamada."""
    existentes = {c.metadata["chunk_id"] for c in ic.partir_en_chunks(ic.construir_documentos())}
    for caso in ev.CASOS_EVALUACION:
        assert isinstance(caso["ids_relevantes"], set)
        assert caso["ids_relevantes"] <= existentes, caso["pregunta"]


def test_hay_casos_sin_respuesta_y_con_dos_relevantes():
    tamanos = {len(c["ids_relevantes"]) for c in ev.CASOS_EVALUACION}
    assert 0 in tamanos and 2 in tamanos


class RetrieverFijo:
    def __init__(self, ids):
        self.ids = ids

    def invoke(self, pregunta):
        return [Document(page_content="x", id=i) for i in self.ids]


def test_evaluar_con_retriever_fijo():
    casos = [
        {"pregunta": "a", "ids_relevantes": {"x1"}},
        {"pregunta": "b", "ids_relevantes": set()},
    ]
    res, p, r = ev.evaluar_recuperacion(RetrieverFijo(["x1", "x2", "x3"]), casos, k=3)
    assert res[0]["recall"] == 1.0 and res[1]["recall"] is None
    assert r == 1.0 and p == pytest.approx((1 / 3 + 0) / 2)


def test_evaluar_es_determinista_y_en_rango(tmp_path):
    carpeta = str(tmp_path / "vs")
    ic.indexar(ic.partir_en_chunks(ic.construir_documentos()), EmbeddingsFalsos(), carpeta)
    ret = ic.abrir(EmbeddingsFalsos(), carpeta).as_retriever(search_kwargs={"k": 3})
    a = ev.evaluar_recuperacion(ret, ev.CASOS_EVALUACION, k=3)
    b = ev.evaluar_recuperacion(ret, ev.CASOS_EVALUACION, k=3)
    assert a == b
    for r in a[0]:
        assert 0.0 <= r["precision"] <= 1.0
        assert r["recall"] is None or 0.0 <= r["recall"] <= 1.0


def test_subir_k_no_baja_recall_ni_sube_precision(tmp_path):
    carpeta = str(tmp_path / "vs")
    ic.indexar(ic.partir_en_chunks(ic.construir_documentos()), EmbeddingsFalsos(), carpeta)
    almacen = ic.abrir(EmbeddingsFalsos(), carpeta)
    _, p3, r3 = ev.evaluar_recuperacion(almacen.as_retriever(search_kwargs={"k": 3}), ev.CASOS_EVALUACION, 3)
    _, p5, r5 = ev.evaluar_recuperacion(almacen.as_retriever(search_kwargs={"k": 5}), ev.CASOS_EVALUACION, 5)
    assert r5 >= r3 and p5 <= p3


def test_guardar_resultados_formato(tmp_path):
    res = [{"pregunta": "q", "ids_recuperados": ["a"], "precision": 0.5, "recall": None}]
    f = tmp_path / "r.txt"
    ev.guardar_resultados(res, 0.5, 0.0, 3, str(f))
    txt = f.read_text(encoding="utf-8")
    assert "Fecha:" in txt and "k=3" in txt and "0.50 n/a q" in txt and "promedio ->" in txt
