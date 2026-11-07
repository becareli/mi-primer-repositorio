import re

def limpiar_texto(texto: str) -> str:
    """
    Normaliza el texto: minúsculas, sin puntuación, sin espacios repetidos.
    """
    if not isinstance(texto, str):
        tipo = type(texto).__name__
        raise TypeError(f"limpiar_texto espera str, no {tipo}.")
    texto = texto.lower()  # Convertir a minúsculas
    texto = re.sub(r"[^\w\s]", "", texto)  # Eliminar puntuación
    texto = re.sub(r"\s+", " ", texto).strip()  # Reemplazar múltiples
    return texto

def tokenizar(texto_limpio: str) -> list[str]:
    """
    Convierte texto limpio en una lista de tokens (palabras) 
    """
    return texto_limpio.split()

def procesar_texto(texto: str) -> list[str]:
    """
    Pipeline completo: limpia y luego tokeniza el texto.
    """
    return tokenizar(limpiar_texto(texto))

if __name__ == "__main__":
    # Prueba del pipeline de procesamiento de texto
    ejemplo = "¡El Gato, el perro y el GATO corren!"
    print("Limpio: ", limpiar_texto(ejemplo))
    print("Tokens:", procesar_texto(ejemplo))           