"""Pruebas SIN red: embeddings falsos y un indice temporal."""
import pytest
from langchain_core.documents import Document

import indexar_corpus as ic
import recuperacion as rc
from test_indexar_corpus import EmbeddingsFalsos


@pytest.fixture
def carpeta(tmp_path):
    destino = str(tmp_path / "vs")
    chunks = ic.partir_en_chunks(ic.construir_documentos())
    ic.indexar(chunks, EmbeddingsFalsos(), destino)
    return destino


def test_formatear_contexto_numera_y_mapea():
    docs = [
        Document(page_content="A", metadata={"fuente": "OGUC 1", "estado": "LECTURA"}),
        Document(page_content="B", metadata={"fuente": "LGUC 2", "estado": "PENDIENTE"}),
    ]
    contexto, citas = rc.formatear_contexto(docs)
    assert citas == {1: "OGUC 1", 2: "LGUC 2"}
    assert "[1] A" in contexto and "[2] B" in contexto
    assert "PENDIENTE" in contexto


def test_sin_metadata_da_desconocida_y_verificar_falla():
    contexto, citas = rc.formatear_contexto([Document(page_content="x")])
    assert citas == {1: "desconocida"}
    with pytest.raises(ValueError):
        rc.verificar_citas(citas, 1)


def test_verificar_citas_exige_claves_consecutivas():
    with pytest.raises(ValueError):
        rc.verificar_citas({1: "a", 3: "b"}, 2)
    rc.verificar_citas({1: "a", 2: "b"}, 2)  # no falla


def test_construir_prompt_cumple_lo_que_debe_cumplirse(carpeta):
    pregunta = "¿Cuándo es obligatorio el informe favorable?"
    prompt, citas = rc.construir_prompt(pregunta, carpeta, k=3, embeddings=EmbeddingsFalsos())
    assert list(citas) == [1, 2, 3]
    assert "desconocida" not in citas.values()
    assert f"Pregunta: {pregunta}" in prompt
    assert "[1]" in prompt and "[2]" in prompt and "[3]" in prompt and "[4]" not in prompt


def test_el_prompt_instruye_citar_y_derivar():
    p = rc.PROMPT_TEMPLATE
    assert "SOLO el contexto" in p and "Cita la fuente" in p
    assert "revision humana" in p and "PENDIENTE" in p


def test_construir_prompt_no_reindexa(carpeta):
    antes = ic.abrir(EmbeddingsFalsos(), carpeta)._collection.count()
    rc.construir_prompt("x", carpeta, k=2, embeddings=EmbeddingsFalsos())
    rc.construir_prompt("y", carpeta, k=2, embeddings=EmbeddingsFalsos())
    assert ic.abrir(EmbeddingsFalsos(), carpeta)._collection.count() == antes


def test_texto_acepta_bloques():
    assert rc._texto("hola") == "hola"
    assert rc._texto([{"type": "text", "text": "a"}, {"text": "b"}]) == "ab"
