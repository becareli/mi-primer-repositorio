"""Tests de trazas.py: no usan el modelo real, solo resultados armados a mano."""
import json

from langchain_core.agents import AgentAction

from trazas import marcar_repeticiones_sospechosas, registrar_traza


def accion(herramienta, argumentos):
    return AgentAction(tool=herramienta, tool_input=argumentos, log="")


def leer(archivo):
    with open(archivo, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def test_guarda_herramienta_argumentos_observacion_y_respuesta(tmp_path):
    archivo = str(tmp_path / "t.jsonl")
    resultado = {
        "output": "Es edificio de uso público.",
        "intermediate_steps": [
            (accion("calcular_carga_ocupacion", {"sectores": "oficinas:500"}), "Carga: 55 personas."),
        ],
    }
    registrar_traza("s1", "¿Cuánta carga?", resultado, archivo)
    [reg] = leer(archivo)
    assert reg["session_id"] == "s1"
    assert reg["entrada"] == "¿Cuánta carga?"
    assert reg["acciones"] == [{
        "herramienta": "calcular_carga_ocupacion",
        "argumentos": {"sectores": "oficinas:500"},
        "observacion": "Carga: 55 personas.",
    }]
    assert reg["respuesta_final"] == "Es edificio de uso público."
    assert "timestamp" in reg


def test_sin_intermediate_steps_acciones_queda_vacia(tmp_path):
    archivo = str(tmp_path / "t.jsonl")
    registrar_traza("s1", "Hola", {"output": "Hola."}, archivo)
    assert leer(archivo)[0]["acciones"] == []


def test_respuesta_en_bloques_de_gemini_se_guarda_como_texto(tmp_path):
    archivo = str(tmp_path / "t.jsonl")
    salida = [{"type": "text", "text": "Sí, es obligatorio.", "extras": {"signature": "x"}}]
    registrar_traza("s1", "¿Es obligatorio?", {"output": salida, "intermediate_steps": []}, archivo)
    assert leer(archivo)[0]["respuesta_final"] == "Sí, es obligatorio."


def test_acentos_se_guardan_legibles_y_cada_llamada_agrega_una_linea(tmp_path):
    archivo = tmp_path / "t.jsonl"
    registrar_traza("s1", "¿Qué es un edificio público?", {"output": "Ocupación > 100."}, str(archivo))
    registrar_traza("s2", "Otra pregunta", {"output": "Otra respuesta."}, str(archivo))
    texto = archivo.read_text(encoding="utf-8")
    assert "público" in texto            # no quedó como ú
    assert len(texto.strip().split("\n")) == 2


def _traza_con(tmp_path, sesiones):
    archivo = str(tmp_path / "t.jsonl")
    for sid, herramientas in sesiones.items():
        pasos = [(accion(h, {"x": i}), "obs") for i, h in enumerate(herramientas)]
        registrar_traza(sid, "q", {"output": "r", "intermediate_steps": pasos}, archivo)
    return archivo


def test_marca_la_misma_herramienta_dos_veces_seguidas(tmp_path):
    archivo = _traza_con(tmp_path, {
        "cliente_123": ["calcular_carga_ocupacion"],
        "cliente_456": ["consultar_reglas_informe", "consultar_reglas_informe"],
    })
    avisos = marcar_repeticiones_sospechosas(archivo)
    assert len(avisos) == 1
    assert "cliente_456" in avisos[0] and "consultar_reglas_informe" in avisos[0]


def test_no_marca_la_misma_herramienta_si_no_es_consecutiva(tmp_path):
    archivo = _traza_con(tmp_path, {
        "s1": ["calcular_carga_ocupacion", "consultar_reglas_informe", "calcular_carga_ocupacion"],
    })
    assert marcar_repeticiones_sospechosas(archivo) == []


def test_archivo_inexistente_da_aviso_claro(tmp_path):
    avisos = marcar_repeticiones_sospechosas(str(tmp_path / "no_existe.jsonl"))
    assert len(avisos) == 1 and "No se encontró" in avisos[0]


def test_linea_corrupta_se_avisa_y_no_rompe_el_resto(tmp_path):
    archivo = tmp_path / "t.jsonl"
    archivo.write_text('{"roto": \n', encoding="utf-8")
    registrar_traza("s9", "q", {"output": "r", "intermediate_steps": [
        (accion("calcular_carga_ocupacion", {}), "o"), (accion("calcular_carga_ocupacion", {}), "o")]}, str(archivo))
    avisos = marcar_repeticiones_sospechosas(str(archivo))
    assert any("Línea 1 ilegible" in a for a in avisos)
    assert any("s9" in a for a in avisos)
