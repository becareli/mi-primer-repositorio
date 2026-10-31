import os
import time
import requests
import json
import re
from dotenv import load_dotenv

# Carga las variables de entorno desde el archivo .env
load_dotenv()

MODELO_POR_DEFECTO = "gemini-3.8-flash"

def armar_peticion(pregunta, system_instruction=None, response_schema=None, modelo=MODELO_POR_DEFECTO):
    if not pregunta:
        raise ValueError("La pregunta no puede estar vacía.")
    # Obtiene la clave de API desde el entorno de forma segura
    api_key = os.getenv("GEMINI_API_KEY")
   
    if not api_key:
        raise RuntimeError("No se encontró la variable GEMINI_API_KEY.")
    # URL oficial de la API de Gemini con el modelo configurado
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
    # Estructura del cuerpo (body) de la petición requerida por la API
    body = {"contents": [{"parts": [{"text": pregunta}]}]}

    if system_instruction is not None:
        body["systemInstruction"] = {"parts": [{"text": system_instruction}]}
    if response_schema is not None:
        body["generationConfig"] = {
            "responseMimeType": "application/json",
            "responseSchema": response_schema,  
        }
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
        raise RuntimeError(
            f"Error en la petición (Código {respuesta.status_code}): {respuesta.text}"
        )
        
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
    

def parsear_respuesta_json(texto, claves_esperadas=None):
    texto_limpio = texto.strip()
    texto_limpio = re.sub(r"^```(?:json)?\s*", "", texto_limpio)
    texto_limpio = re.sub(r"\s*```$", "", texto_limpio)
    try:
        datos = json.loads(texto_limpio)
    except json.JSONDecodeError as e:    
        raise ValueError(f"La respuesta del modelo no es un JSON válido.")
    if claves_esperadas is not None:
        if not isinstance(datos, dict) or not all(c in datos for c in claves_esperadas):
            raise ValueError("La respuesta no tiene la estructura esperada.")
    return datos

# Precios por token en USD (tarifa estándar de gemini-3.5-flash-lite: USD 0,30 de entrada
# y USD 2,50 de salida por cada 1 millón de tokens). 
PRECIO_ENTRADA = 0.30 / 1_000_000
PRECIO_SALIDA = 2.50 / 1_000_000

def calcular_costo(datos, precio_entrada, precio_salida):
    uso = datos["usageMetadata"]
    tokens_entrada = uso["promptTokenCount"]
    tokens_salida = uso["candidatesTokenCount"]
    return (tokens_entrada * precio_entrada) + (tokens_salida * precio_salida)
 
def obtener_datos_de_prueba(pregunta, modelo=MODELO_POR_DEFECTO):
    url, body = armar_peticion(pregunta, modelo=modelo)
    datos = enviar_peticion(url, body)
    texto = extraer_texto(datos)
    costo = calcular_costo(datos, PRECIO_ENTRADA, PRECIO_SALIDA)
    return texto, costo
 
def medir_latencia(pregunta, modelo=MODELO_POR_DEFECTO, repeticiones=4):
    latencias = []
    for i in range(repeticiones):
        url, body = armar_peticion(pregunta, modelo=modelo)
        inicio = time.perf_counter()
        datos = enviar_peticion(url, body)
        fin = time.perf_counter()
        latencias.append(fin - inicio)
        print(f"Repetición {i + 1}: Latencia = {latencias[-1]:.2f} segundos")
        time.sleep(1)  # Pausa de 1 segundo entre repeticiones para evitar sobrecarga
    promedio = sum(latencias) / len(latencias)   
    return promedio, datos   

# Bloque de prueba local 
if __name__ == "__main__":
    
    texto, costo = obtener_datos_de_prueba("Un terreno de 300 m2 tiene ocupación de suelo de 0,6 y coeficiente de constructibilidad de 1,2. ¿Cuántos m2 puedo ocupar en el primer piso y cuántos m2 totales puedo construir? Responde en texto plano, sin Markdown ni símbolos LaTeX, en máximo 3 líneas.")
    print(texto)
    print(f"Costo estimado de la petición: {costo:.6f} USD")
 
 