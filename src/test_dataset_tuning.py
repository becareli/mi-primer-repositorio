import copy
import json

import dataset_tuning as d


def test_hay_al_menos_10_ejemplos_y_varias_categorias():
    assert len(d.examples) >= 10
    assert len(d.chequear_balance(d.ejemplos_raw, "destino")) > 1


def test_balance_sin_categoria_dominante():
    cuentas = d.chequear_balance(d.ejemplos_raw, "destino").values()
    assert max(cuentas) <= 3 * min(cuentas)


def test_todos_los_destinos_permitidos_estan_cubiertos():
    destinos = set(d.chequear_balance(d.ejemplos_raw, "destino"))
    assert destinos == d.VALORES_PERMITIDOS["destino"]


def test_dataset_valido_devuelve_lista_vacia():
    assert d.validar_dataset(d.examples, d.CLAVES, d.VALORES_PERMITIDOS) == []


def test_detecta_json_invalido():
    rotos = copy.deepcopy(d.examples)
    rotos[2].output = rotos[2].output.replace('"', "'")
    assert any("no es JSON valido" in p for p in d.validar_dataset(rotos, d.CLAVES))


def test_detecta_clave_faltante():
    rotos = copy.deepcopy(d.examples)
    salida = json.loads(rotos[0].output)
    del salida["comuna"]
    rotos[0].output = json.dumps(salida)
    assert any('clave "comuna"' in p for p in d.validar_dataset(rotos, d.CLAVES))


def test_detecta_texto_duplicado():
    rotos = copy.deepcopy(d.examples)
    rotos[1].text_input = rotos[0].text_input
    assert any("duplicado" in p for p in d.validar_dataset(rotos, d.CLAVES))


def test_detecta_valor_fuera_de_vocabulario():
    rotos = copy.deepcopy(d.examples)
    salida = json.loads(rotos[0].output)
    salida["destino"] = "casino"
    rotos[0].output = json.dumps(salida)
    assert any("no permitido" in p for p in d.validar_dataset(rotos, d.CLAVES, d.VALORES_PERMITIDOS))


def test_detecta_output_vacio():
    rotos = copy.deepcopy(d.examples)
    rotos[0].output = ""
    assert any("output vacio" in p for p in d.validar_dataset(rotos, d.CLAVES))


def test_sin_datos_personales_en_los_textos():
    for ej in d.examples:
        assert "@" not in ej.text_input


def test_destino_declarado_es_texto_libre_y_no_se_rechaza():
    copia = copy.deepcopy(d.examples)
    for ej in copia:
        salida = json.loads(ej.output)
        salida["destino_declarado"] = "palabra-que-nunca-vi"
        ej.output = json.dumps(salida)
    assert d.validar_dataset(copia, d.CLAVES, d.VALORES_PERMITIDOS) == []


def test_casino_y_motel_estan_en_el_dataset():
    declarados = {json.loads(e.output)["destino_declarado"]: json.loads(e.output)["destino"] for e in d.examples}
    assert declarados["casino"] == "otro"
    assert declarados["motel"] == "habitacional"


def test_hormigon_es_categoria_propia():
    estructuras = {json.loads(e.output)["estructura"] for e in d.examples}
    assert "hormigon" in estructuras
