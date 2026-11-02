"""
Prueba del reintento de cliente.py.

Simula un proveedor que falla las dos primeras veces con TimeoutError
y responde correctamente a la tercera. Demuestra que con_reintento
reintenta ante errores temporales.

Ejecutar desde la carpeta src:
    python prueba_reintento.py
"""

from cliente import con_reintento

intentos_previos = 0

def enviar_simulado ():
    global intentos_previos
    intentos_previos += 1
    if intentos_previos < 3:
        raise TimeoutError("Límite de peticiones excedido. Hay que esperar y reintentar.")
    return {"Contenido": "Respuesta simulada exitosa después de reintentos.", "intento": intentos_previos}


print(con_reintento(enviar_simulado))




