import pytest
from carga_ocupacion import calcular_carga, calcular_carga_total, es_edificio_uso_publico


def test_oficinas_1000_m2_son_100_personas_y_no_es_uso_publico():
    carga = calcular_carga("oficinas", 1000)
    assert carga == pytest.approx(100.0)
    assert es_edificio_uso_publico(carga) is False


def test_oficinas_1010_m2_son_101_personas_y_si_es_uso_publico():
    carga = calcular_carga("oficinas", 1010)
    assert carga == pytest.approx(101.0)
    assert es_edificio_uso_publico(carga) is True


def test_salas_de_clase_150_m2_son_100_personas():
    assert calcular_carga("educacion_salas_de_clase", 150) == pytest.approx(100.0)


def test_vivienda_120_m2_usa_tramo_de_20_m2_por_persona():
    assert calcular_carga("vivienda_mas_de_60_hasta_140", 120) == pytest.approx(6.0)


def test_dos_destinos_se_suman_por_sector():
    # 500 m2 de oficinas = 50 personas + 800 m2 de estacionamientos = 50 personas
    assert calcular_carga_total([("oficinas", 500), ("estacionamientos", 800)]) == pytest.approx(100.0)
    # con 816 m2 de estacionamientos son 51 personas: total 101
    assert calcular_carga_total([("oficinas", 500), ("estacionamientos", 816)]) == pytest.approx(101.0)


def test_destino_inexistente_lanza_error_claro():
    with pytest.raises(ValueError) as excinfo:
        calcular_carga("heladeria", 100)
    assert "heladeria" in str(excinfo.value)


def test_superficie_cero_lanza_error():
    with pytest.raises(ValueError):
        calcular_carga("oficinas", 0)