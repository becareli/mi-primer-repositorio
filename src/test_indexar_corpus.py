"""Pruebas SIN red: usan embeddings falsos pero deterministas."""
import hashlib

import pytest
from langchain_core.embeddings import Embeddings

import indexar_corpus as ic


class EmbeddingsFalsos(Embeddings):
    """Vector de 16 números sacado de un hash: mismo texto -> mismo vector."""

    def _vec(self, texto):
        h = hashlib.sha256(texto.encode("utf-8")).digest()
        return [b / 255 for b in h[:16]]

    def embed_documents(self, textos):
        return [self._vec(t) for t in textos]

    def embed_query(self, texto):
        return self._vec(texto)


def test_cada_documento_tiene_metadatos():
    for d in ic.construir_documentos():
        assert d.metadata["fuente"] and d.metadata["estado"] and d.metadata["doc_id"]


def test_estados_validos():
    validos = {"VERIFICADO", "LECTURA", "PENDIENTE", "CRITERIO"}
    assert {c["estado"] for c in ic.CORPUS} <= validos


def test_chunking_parte_el_documento_largo():
    chunks = ic.partir_en_chunks(ic.construir_documentos())
    tabla = [c for c in chunks if c.metadata["doc_id"] == "tabla_ocupacion"]
    assert len(tabla) > 1
    assert all(len(c.page_content) <= ic.CHUNK_SIZE for c in chunks)


def test_chunk_ids_unicos():
    ids = [c.metadata["chunk_id"] for c in ic.partir_en_chunks(ic.construir_documentos())]
    assert len(ids) == len(set(ids))


def test_overlap_invalido_falla():
    with pytest.raises(ValueError):
        ic.partir_en_chunks(ic.construir_documentos(), chunk_size=100, chunk_overlap=150)


def test_persiste_y_reabre(tmp_path):
    carpeta = str(tmp_path / "vs")
    chunks = ic.partir_en_chunks(ic.construir_documentos())
    ic.indexar(chunks, EmbeddingsFalsos(), carpeta)
    assert ic.hay_indice(carpeta)
    reabierto = ic.abrir(EmbeddingsFalsos(), carpeta)
    assert reabierto._collection.count() == len(chunks)


def test_reindexar_dos_veces_no_duplica(tmp_path):
    carpeta = str(tmp_path / "vs")
    chunks = ic.partir_en_chunks(ic.construir_documentos())
    ic.indexar(chunks, EmbeddingsFalsos(), carpeta)
    ic.indexar(chunks, EmbeddingsFalsos(), carpeta)
    assert ic.abrir(EmbeddingsFalsos(), carpeta)._collection.count() == len(chunks)


def test_busqueda_devuelve_metadatos(tmp_path):
    carpeta = str(tmp_path / "vs")
    chunks = ic.partir_en_chunks(ic.construir_documentos())
    ic.indexar(chunks, EmbeddingsFalsos(), carpeta)
    r = ic.abrir(EmbeddingsFalsos(), carpeta).similarity_search("x", k=2)
    assert len(r) == 2 and "fuente" in r[0].metadata


def test_explicar_error():
    assert "espera" in ic.explicar_error_red(Exception("429 RESOURCE_EXHAUSTED"))
    assert "clave" in ic.explicar_error_red(Exception("API key not valid"))
