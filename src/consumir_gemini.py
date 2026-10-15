import os
import requests
from dotenv import load_dotenv

# Carga las variables de entorno desde el archivo .env
load_dotenv()

def obtener_datos_gemini(pregunta):
    # Obtiene la clave de API desde el entorno de forma segura
    api_key = os.getenv("GEMINI_API_KEY")
    
    # URL oficial de la API de Gemini con el modelo configurado
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={api_key}"

    # Estructura del cuerpo (body) de la petición requerida por la API
    body = {
        "contents": [{
            "parts": [{"text": pregunta}]
        }]
    }

    # Envía la petición HTTP POST enviando el diccionario como JSON
    respuesta = requests.post(url, json=body)

    # Validación por si la API rechaza la petición (ej. clave incorrecta)
    if respuesta.status_code != 200:
        return f"Error en la petición (Código {respuesta.status_code}): {respuesta.text}"

    # Convierte la respuesta de JSON a un diccionario de Python
    datos = respuesta.json()

    # Extrae el texto generado navegando por la estructura JSON oficial
    texto_generado = datos["candidates"][0]["content"]["parts"][0]["text"]

    return texto_generado

# Bloque de prueba local (bien indentado al margen izquierdo)
if __name__ == "__main__":
    resultado = obtener_datos_gemini("¿Es muy dificil trabajar en LATAM como IA Engineer?")
    print("Respuesta de Gemini:")
    print(resultado)
 