import json

import decision as dec
import probar_extraccion as pe


def test_metodo_caso_bot_de_atencion_de_la_leccion():
    r = {"informacion_cambia_seguido": True, "problema_de_formato_o_tono": True,
         "dataset_grande_y_de_calidad": False, "presupuesto_limitado_o_iterar_rapido": True,
         "necesita_multiples_variantes": False}
    assert dec.recomendar_estrategia(r) == ({"RAG": 5, "Fine-tuning completo": 1, "PEFT": 3}, ["RAG"])


def test_metodo_reporta_empates_caso_clasificador():
    r = {"informacion_cambia_seguido": False, "problema_de_formato_o_tono": True,
         "dataset_grande_y_de_calidad": True, "presupuesto_limitado_o_iterar_rapido": False,
         "necesita_multiples_variantes": False}
    puntos, g = dec.recomendar_estrategia(r)
    assert puntos == {"RAG": 0, "Fine-tuning completo": 3, "PEFT": 3}
    assert g == ["Fine-tuning completo", "PEFT"]


def test_costo_de_etiquetar_como_en_la_leccion():
    h, c = dec.estimar_costo_de_etiquetar(200, 5, 25)
    assert round(h, 2) == 16.67 and round(c, 2) == 416.67


def test_casos_de_prueba_son_validos_y_nuevos():
    assert len(pe.CASOS_PRUEBA) == 20
    entrenamiento = {t for t, _ in pe.ejemplos_raw}
    for texto, esperado in pe.CASOS_PRUEBA:
        assert texto not in entrenamiento
        assert pe.problemas_de_formato(json.dumps(esperado, ensure_ascii=False)) == []


def test_limpiar_cercas():
    assert pe.limpiar_cercas('```json\n{"a": 1}\n```') == '{"a": 1}'


def test_formato_detecta_problemas():
    assert pe.problemas_de_formato("hola")[0].startswith("no es JSON")
    assert any("falta" in p for p in pe.problemas_de_formato("{}"))
    malo = dict(pe.CASOS_PRUEBA[0][1], destino="casino")
    assert any("no permitido" in p for p in pe.problemas_de_formato(json.dumps(malo)))
    malo = dict(pe.CASOS_PRUEBA[0][1], superficie_nueva_m2="4800")
    assert any("numero" in p for p in pe.problemas_de_formato(json.dumps(malo)))


def _respuestas_perfectas():
    return [json.dumps(e, ensure_ascii=False) for _, e in pe.CASOS_PRUEBA]


def test_evaluar_respuestas_perfectas():
    r = pe.evaluar(_respuestas_perfectas())
    assert r["incumplimientos"] == 0 and r["aciertos_campos"] == r["total_campos"] == 160


def test_evaluar_distingue_estricto_de_tolerante():
    resp = _respuestas_perfectas()
    resp[0] = "```json\n" + resp[0] + "\n```"
    resp[1] = "no puedo ayudar"
    r = pe.evaluar(resp)
    assert r["fallos_estrictos"] == 2 and r["incumplimientos"] == 1


def _res(fallos):
    return {"n": 20, "incumplimientos": fallos, "fallos_estrictos": fallos,
            "aciertos_campos": 150, "total_campos": 160}


def _doc(fallos):
    resp = dec.construir_respuestas(_res(fallos), 16)
    puntos, g = dec.recomendar_estrategia(resp)
    balance = {"habitacional": 3, "otro": 1}
    return puntos, g, dec.generar_documento(_res(fallos), None, puntos, g, balance, 16)


def test_con_fallos_gana_peft_y_documento_tiene_cuatro_secciones_en_orden():
    puntos, g, doc = _doc(6)
    assert g == ["PEFT"] and puntos["PEFT"] == 3
    pos = [doc.index(f"## {i}.") for i in range(1, 5)]
    assert pos == sorted(pos)
    assert "faltan 184" in doc and "15.3 horas" in doc


def test_sin_fallos_el_documento_no_finge_un_ganador():
    puntos, g, doc = _doc(1)
    assert g == ["RAG"]
    assert "NO personalizar" in doc and "no encaja" in doc


def test_sensibilidad_devuelve_cinco_lineas():
    resp = dec.construir_respuestas(_res(6), 16)
    _, g = dec.recomendar_estrategia(resp)
    assert len(dec.sensibilidad(resp, g)) == 5
