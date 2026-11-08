import pytest
from metricas import calcular_metricas

def test_ejemplo_gato_calculado_a_mano():
    r = calcular_metricas(
        "El gato duerme en el sofá.", 
        "El gato duerme en el sillón todo el día.",
    )
    assert r["precision"] == pytest.approx(5 / 9)
    assert r["cobertura"] == pytest.approx(5 / 6)
    assert r["f1"] == pytest.approx(0.667, abs=0.001)  # Aproximadamente 0.667

def test_repeticiones_ya_no_dan_100_por_ciento():
    r = calcular_metricas("el gato ", "el gato el gato ")
    assert r["precision"] == pytest.approx(0.5)
    assert r["cobertura"] == pytest.approx(1.0)


def test_sinonimo_perfecto_puntua_bajo():
    r = calcular_metricas("El auto es veloz. ", "El vehículo es rápido.")
    assert r["f1"] == pytest.approx(0.5)    

def test_negacion_ausente_casi_no_baja_el_puntaje():
    r = calcular_metricas(
        "Python no es un lenguaje compilado. ", "Python es un lenguaje compilado "
    )
    assert r["f1"] == pytest.approx(0.909, abs=0.001)  # Aproximadamente 0.909    

def test_texto_vacio_devuelve_ceros_sin_error():
    r = calcular_metricas("hola", "¡¿...?!"
    )
    assert r == {"precision": 0.0, "cobertura": 0.0, "f1": 0.0}

