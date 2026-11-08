from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage

from cadena_tres_pasos import calcular_en_python, construir_cadena


def test_cadena_conecta_los_tres_pasos():
    modelo_falso = MagicMock()
    modelo_falso.side_effect = [
        AIMessage(content="especial: ninguna\nsector: oficinas | 1010"),
        AIMessage(content="Determinación: OBLIGATORIO\nMotivo: 101.0 personas."),
        AIMessage(content="Debes contratar al revisor independiente."),
    ]
    cadena = construir_cadena(modelo_falso)
    resultado = cadena.invoke({"descripcion": "Oficinas de 1010 m2"})
    assert modelo_falso.call_count == 3
    assert "revisor" in resultado
    # El paso 2 debe haber recibido la carga calculada por Python (101.0):
    prompt_paso_2 = str(modelo_falso.call_args_list[1].args[0])
    assert "101.0" in prompt_paso_2


def test_calcular_en_python_suma_dos_sectores():
    r = calcular_en_python(
        "especial: ninguna\nsector: oficinas | 500\nsector: estacionamientos | 816"
    )
    assert r["carga"] == pytest.approx(101.0)
    assert r["es_uso_publico"] == "SÍ"


def test_calcular_en_python_borde_de_100_personas_no_es_uso_publico():
    r = calcular_en_python("sector: oficinas | 1000")
    assert r["carga"] == pytest.approx(100.0)
    assert r["es_uso_publico"] == "NO"


def test_calcular_en_python_sin_sectores_lanza_error():
    with pytest.raises(ValueError):
        calcular_en_python("especial: ninguna")