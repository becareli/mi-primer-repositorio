import time
import random
from typing import Callable, Any # Solo para describir tipos de datos (ayuda a leer el código)


from consumir_gemini import armar_peticion, enviar_peticion, extraer_texto


def con_reintento(
    funcion: Callable[[], Any], # La función que se va a intentar (sin argumentos)
    intentos: int = 3, 
    espera_base: float = 2,
    espera_maxima: float = 30, 
) -> Any:
    for intento in range(1, intentos + 1): # Cuenta 1, 2, 3 (el +1 es porque range no incluye el último)
        try:
            return funcion()
        except  TimeoutError:
            if intento == intentos:
                raise
            espera =min(espera_base * (2 ** (intento - 1)), espera_maxima) # Espera exponencial con límite
            espera_total = espera + random.uniform(0, espera * 0.1) # Añade un poco de aleatoriedad para evitar colisiones    
            print(f"Intento {intento} de {intentos} falló por límite de uso. Reintentando en {espera_total:.1f} segundos.")
            time.sleep(espera_total)


COSTO_POR_1000_TOKENS = 0.00225 

costo_total_sesion = 0.0

def registrar_costo(respuesta: dict) -> float:
    global costo_total_sesion
    uso = respuesta.get("usageMetadata", {})
    total_tokens = uso.get("totalTokenCount", 0)
    costo_estimado = (total_tokens / 1000) * COSTO_POR_1000_TOKENS
    costo_total_sesion += costo_estimado
    print(f"Operación: {total_tokens} tokens, costo estimado: ${costo_estimado:.5f}, (acumulado: ${costo_total_sesion:.5f})")
    return costo_estimado

def consultar_modelo(pregunta, system_instruction=None):        
    url, body = armar_peticion(pregunta, system_instruction)
    try:
        respuesta = con_reintento(lambda: enviar_peticion(url, body))
    except TimeoutError:
        raise RuntimeError("El servicio no respondió tras varios intentos. Intenta más tarde.")
    registrar_costo(respuesta)
    return extraer_texto(respuesta)


if __name__ == "__main__":
    for i in range(40):
        try:
            respuesta = consultar_modelo(f"Pregunta de prueba numero {i}")
            print(f"Respuesta {i}: {respuesta [:40]}...")  # Muestra solo los primeros 40 caracteres
        except RuntimeError as error:
            print(f"Respuesta {i} falló definitivamente: {error}") 
    print(f"Costo total de la sesión: ${costo_total_sesion:.5f}")        