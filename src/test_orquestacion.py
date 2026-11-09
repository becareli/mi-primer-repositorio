from unittest.mock import MagicMock

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from enrutamiento import (
    RESPUESTA_DERIVAR,
    construir_cadena_con_enrutamiento,
    construir_paso_clasificacion,
    construir_ruta_proyecto,
    construir_ruta_segura,
    procesar_mensaje_seguro,
)


def _clasificacion(categoria):
    falsa = MagicMock()
    falsa.return_value = categoria  # .return_value, NO .invoke.return_value
    return falsa


# ---------- Clasificación ----------
def test_clasificacion_normaliza_antes_de_comparar():
    modelo_falso = MagicMock()
    modelo_falso.return_value = AIMessage(content=" Proyecto. \n")
    resultado = construir_paso_clasificacion(modelo_falso).invoke({"mensaje": "x"})
    assert resultado == "proyecto"


def test_clasificacion_con_respuesta_vacia_no_rompe():
    modelo_falso = MagicMock()
    modelo_falso.return_value = AIMessage(content="")
    resultado = construir_paso_clasificacion(modelo_falso).invoke({"mensaje": "x"})
    assert resultado == ""


# ---------- Bifurcación ----------
def test_enrutamiento_va_a_ruta_proyecto():
    ruta = MagicMock()
    ruta.return_value = "respuesta de proyecto"
    cadena = construir_cadena_con_enrutamiento(_clasificacion("proyecto"), ruta_proyecto=ruta)
    assert cadena.invoke({"mensaje": "oficinas 500 m2"}) == "respuesta de proyecto"
    assert ruta.called


def test_enrutamiento_va_a_ruta_normativa():
    ruta = MagicMock()
    ruta.return_value = "respuesta normativa"
    cadena = construir_cadena_con_enrutamiento(_clasificacion("normativa"), ruta_normativa=ruta)
    assert cadena.invoke({"mensaje": "¿plazo DOM?"}) == "respuesta normativa"
    assert ruta.called


def test_enrutamiento_usa_default_ante_categoria_desconocida():
    ruta = MagicMock()
    ruta.return_value = "derivado"
    cadena = construir_cadena_con_enrutamiento(
        _clasificacion("categoria inventada"), ruta_derivar=ruta
    )
    assert cadena.invoke({"mensaje": "ambiguo"}) == "derivado"
    assert ruta.called


def test_default_real_deriva_a_revision_humana_con_categoria_vacia():
    cadena = construir_cadena_con_enrutamiento(_clasificacion(""))
    assert cadena.invoke({"mensaje": "?"}) == RESPUESTA_DERIVAR


# ---------- Conexión con la chain del Bloque 18 ----------
def test_ruta_proyecto_conecta_mensaje_con_la_chain_de_tres_pasos():
    modelo_falso = MagicMock()
    modelo_falso.side_effect = [
        AIMessage(content="especial: ninguna\nsector: oficinas | 500\n"
                          "sector: estacionamientos | 816"),
        AIMessage(content="Determinación: OBLIGATORIO"),
        AIMessage(content="mensaje final"),
    ]
    resultado = construir_ruta_proyecto(modelo_falso).invoke({"mensaje": "obra nueva"})
    assert resultado == "mensaje final"
    prompt_paso_2 = modelo_falso.call_args_list[1].args[0].to_string()
    assert "101.0" in prompt_paso_2  # 50 + 51 personas, calculado en Python


# ---------- Manejo de errores ----------
def test_ruta_segura_usa_fallback_ante_fallo_del_modelo():
    def fallar(x):
        raise ConnectionError("simulado")

    ruta_rota = RunnableLambda(fallar)  # RunnableLambda real, no MagicMock
    resultado = construir_ruta_segura(ruta_rota).invoke({"mensaje": "algo"})
    assert "equipo" in resultado.lower()


def test_procesar_mensaje_seguro_no_propaga_excepciones():
    clasificacion_rota = MagicMock()
    clasificacion_rota.side_effect = ConnectionError("simulado")
    cadena = construir_cadena_con_enrutamiento(paso_clasificacion=clasificacion_rota)
    resultado = procesar_mensaje_seguro(cadena, "mensaje de prueba")
    assert "no pudimos procesar" in resultado.lower()


def test_procesar_mensaje_seguro_devuelve_resultado_normal_si_todo_va_bien():
    ruta = MagicMock()
    ruta.return_value = "ok"
    cadena = construir_cadena_con_enrutamiento(_clasificacion("proyecto"), ruta_proyecto=ruta)
    assert procesar_mensaje_seguro(cadena, "oficinas 500 m2") == "ok"