import os
import requests
from dotenv import load_dotenv

# Carga las variables de entorno desde el archivo .env
load_dotenv()

def armar_peticion(pregunta):
    if not pregunta:
        raise ValueError("La pregunta no puede estar vacía.")
    # Obtiene la clave de API desde el entorno de forma segura
    api_key = os.getenv("GEMINI_API_KEY")
   
    if not api_key:
        raise RuntimeError("No se encontró la variable GEMINI_API_KEY.")
    # URL oficial de la API de Gemini con el modelo configurado
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={api_key}"
    # Estructura del cuerpo (body) de la petición requerida por la API
    body = {"contents": [{"parts": [{"text": pregunta}]}]}
    return url, body

def enviar_peticion(url, body):
    try:
        # Envía la petición HTTP POST enviando el diccionario como JSON
        respuesta = requests.post(url, json=body)
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Error de conexión: No se pudo conectar a la API de Gemini"
        )
     # Validación por si la API rechaza la petición (ej. clave incorrecta)

    if respuesta.status_code != 200:
       return f"Error en la petición (Código {respuesta.status_code}): {respuesta.text}"
        
    try:
        return respuesta.json()
    except requests.exceptions.JSONDecodeError:
        raise RuntimeError(
        "Error al decodificar la respuesta JSON de la API de Gemini."
        )  
     
def extraer_texto(datos):
    try:
        return datos["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError("Error al extraer el texto de la respuesta de la API de Gemini. La estructura de datos no es la esperada.")   

def obtener_datos_de_prueba(pregunta):
    url, body = armar_peticion(pregunta)
    datos = enviar_peticion(url, body)
    return extraer_texto(datos)

# Bloque de prueba local (bien indentado al margen izquierdo)
if __name__ == "__main__":
    
    print(obtener_datos_de_prueba("¿Cuanto gana en promedio un  IA Engineer junior en latam?"))
 