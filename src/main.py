from datetime import datetime
from consumir_gemini import medir_latencia, calcular_costo, extraer_texto

MODELOS = {
    "gemini-3.5-flash-lite": (0.30 / 1_000_000, 2.50 / 1_000_000),  # (precio_entrada, precio_salida)
    "gemini-3.8-flash": (0.75 / 1_000_000, 3.75 / 1_000_000),     #Estos precios subiran a USD 1.50 y 7.50 a partir del 1 de enero de 2027
}

PREGUNTAS = [
    "Explica en 3 líneas qué es el coeficiente de constructibilidad.",
    "¿Qué documentos mínimos pide una DOM para un permiso de edificación de una vivienda unifamiliar?",
    "Un terreno de 300 m2 tiene ocupación de suelo de 0,6. ¿Cuántos m2 puedo ocupar en el primer piso?",
]

print(f"Comparación de Modelos Gemini - fecha: {datetime.today()}")

for modelo, (precio_entrada, precio_salida) in MODELOS.items():
    print(f"\n=== Modelo: {modelo} ===")
    try:
        promedio, datos = medir_latencia(PREGUNTAS[0], modelo=modelo)
        costo = calcular_costo(datos, precio_entrada, precio_salida)
        print(f"Latencia promedio para la primera pregunta: {promedio:.2f} segundos")
        print(f"Costo estimado para la ultima petición: ${costo:.6f} USD")

        for pregunta in PREGUNTAS:
            print(f"\nP: {pregunta}")
            _, datos = medir_latencia(pregunta, modelo, repeticiones=1)  
            print(f"R: {extraer_texto(datos)}")
    except (RuntimeError, ValueError) as error: 
        print(f"Falló la prueba de  {modelo}: {error}") 
   





