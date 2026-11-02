import time
from typing import Callable, Any # Solo para describir tipos de datos (ayuda a leer el código)


from consumir_gemini import armar_peticion, enviar_peticion, extraer_texto


def con_reintento(
    funcion: Callable[[], Any], # La función que se va a intentar (sin argumentos)
    intentos: int = 3, 
    espera_segundos: int = 2, 
) -> Any:
    for intento in range(1, intentos + 1): # Cuenta 1, 2, 3 (el +1 es porque range no incluye el último)
        try:
            return funcion()
        except  TimeoutError:
            if intento == intentos:
                raise
            print(f"Intento {intento} de {intentos} falló por límite de uso. Reintentando ... ")
            time.sleep(espera_segundos)


def consultar_modelo(pregunta, system_instruction=None):        
    url, body = armar_peticion(pregunta, system_instruction)
    try:
        respuesta = con_reintento(lambda: enviar_peticion(url, body))
    except TimeoutError:
        raise RuntimeError("El servicio no respondió tras varios intentos. Intenta más tarde.")
    return extraer_texto(respuesta)


