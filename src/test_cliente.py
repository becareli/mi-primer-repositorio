from unittest.mock import patch, Mock
import pytest
import cliente
from consumir_gemini import enviar_peticion
from cliente import con_reintento

def test_enviar_peticion_credencial_invalida():
    respuesta_falsa = Mock(status_code=401)

    with patch('consumir_gemini.requests.post', return_value=respuesta_falsa):
        with pytest.raises(ValueError) as excinfo:
            enviar_peticion("http://url-de-prueba.com", {"pregunta": "test"})   

    assert "Credencial inválida o sin permiso" in str(excinfo.value)

def test_enviar_peticion_limite_de_uso():
    respuesta_falsa = Mock(status_code=429)

    with patch('consumir_gemini.requests.post', return_value=respuesta_falsa):
        with pytest.raises(TimeoutError):
            enviar_peticion("http://url-de-prueba.com", {"pregunta": "test"})   

def test_enviar_peticion_exito():
    respuesta_falsa = Mock(status_code=200)
    respuesta_falsa.json.return_value = {"text": "respuesta simulada"}

    with patch('consumir_gemini.requests.post', return_value=respuesta_falsa):
        resultado = enviar_peticion("http://url-de-prueba.com", {"pregunta": "test"})   

    assert resultado == {"text": "respuesta simulada"}

def test_con_reintento_agota_intentos():
    llamadas = []

    def siempre_falla():
        llamadas.append(1)
        raise TimeoutError("Simulado.")

    with patch("cliente.time.sleep") as sleep_falso:
        with pytest.raises(TimeoutError):
            con_reintento(siempre_falla, intentos=3)

    assert len(llamadas) == 3  # Se intentó 3 veces
    assert sleep_falso.call_count == 2  # Se durmió 2 veces entre intentos


def test_con_reintento_no_reintenta_value_error():
    llamadas = []

    def falla_con_credencial():
        llamadas.append(1)
        raise ValueError("Credencial inválida o sin permiso.")

    with patch("cliente.time.sleep") as sleep_falso:
        with pytest.raises(ValueError):
            con_reintento(falla_con_credencial, intentos=3)

    assert len(llamadas) == 1  # Se intentó 1 vez
    sleep_falso.assert_not_called()  # No se durmió porque no es un error temporal

def test_con_reintento_reintenta_en_timeout():
    llamadas = []

    def falla_dos_veces_y_luego_funciona():
        llamadas.append(1)
        if len(llamadas) < 3:
            raise TimeoutError("simulado")
        return "respuesta final"

    with patch("cliente.time.sleep") as sleep_falso:
        resultado = con_reintento(falla_dos_veces_y_luego_funciona, intentos=3)

    assert resultado == "respuesta final"
    assert len(llamadas) == 3
    assert sleep_falso.call_count == 2

@pytest.fixture(autouse=True)
def reiniciar_costo_total():
    cliente.costo_total_sesion = 0
    yield

def test_registrar_costo_calcula_costo_correcto(): 
    respuesta_falsa = {"usageMetadata": {"totalTokenCount": 1000}} 

    costo = cliente.registrar_costo(respuesta_falsa)

    assert costo == cliente.COSTO_POR_1000_TOKENS       

def test_registrar_costo_acumula_en_total_sesion():
    respuesta_falsa = {"usageMetadata": {"totalTokenCount": 1000}} 

    cliente.registrar_costo(respuesta_falsa)
    cliente.registrar_costo(respuesta_falsa)

    assert cliente.costo_total_sesion == pytest.approx(2 * cliente.COSTO_POR_1000_TOKENS)

def test_consultar_modelo_convierte_timeout_en_runtime_error():
    with patch('cliente.armar_peticion', return_value=("http://url-de-prueba.com", {})):
        with patch('cliente.con_reintento', side_effect=TimeoutError("Simulado")):
            with pytest.raises(RuntimeError) as excinfo:
                cliente.consultar_modelo("Pregunta de prueba")

    assert "no respondió" in str(excinfo.value)

def test_consultar_modelo_propaga_value_error_sin_cambios():
    with patch('cliente.armar_peticion', return_value=("http://url-de-prueba.com", {})):
        with patch('cliente.con_reintento', side_effect=ValueError("Credencial inválida o sin permiso.")):
            with pytest.raises(ValueError) as excinfo:
                cliente.consultar_modelo("Pregunta de prueba")

    assert str(excinfo.value) == "Credencial inválida o sin permiso."


def test_consultar_modelo_flujo_exitoso(): 
    respuesta_falsa = {
        "candidates": [{"content": {"parts": [{"text": "Santiago es la Capital de Argentina."}]}}], 
        "usageMetadata": {"totalTokenCount": 1000}}

    with patch('cliente.armar_peticion', return_value=("http://url-de-prueba.com", {})):
        with patch('cliente.con_reintento', return_value=respuesta_falsa):
            resultado = cliente.consultar_modelo("¿Cual es la Capital de Argentina?")

    assert resultado == "Santiago es la Capital de Argentina."
    assert cliente.costo_total_sesion == pytest.approx(cliente.COSTO_POR_1000_TOKENS) 


def test_enviar_peticion_clave_invalida_con_400():
    respuesta_falsa = Mock(status_code=400, text='{"error": {"reason": "API_KEY_INVALID"}}')

    with patch("consumir_gemini.requests.post", return_value=respuesta_falsa):
        with pytest.raises(ValueError):
            enviar_peticion("http://url-de-prueba.com", {"pregunta": "test"})