from cliente import consultar_modelo
from pipeline_texto import procesar_texto

#Cada caso: una pregunta y la referencia, o sea, la respuesta ideal escrita por ti. 

CASOS_DE_PRUEBA = [
    {
        "pregunta": "¿Cuál documento debo solicitar antes de comenzar a construir en la Dirección de Obras Municipales? ?",
        "referencia": "El certificado de informes previos (CIP) es el documento que debes solicitar antes de comenzar a construir en la Dirección de Obras Municipales. Este certificado proporciona información sobre las regulaciones y requisitos específicos para la construcción en un área determinada, asegurando que tu proyecto cumpla con las normativas locales."
    },
    {
        "pregunta": "¿¿Qué es la rasante de 70°? ?",
        "referencia": "La rasante se refiere a un plano inclinado que nace desde la línea del suelo y define el volumen teórico de la construcción."
    },
    {
        "pregunta": "¿Qué son los derechos municipales de construcción? ?",
        "referencia": "Es el monto de dinero que pagas de una sola vez, una vez que la municipalidad te aprueba tu permiso de edificación. Este pago es un requisito para poder iniciar la construcción y se calcula en base a factores como el tamaño del proyecto, la ubicación y las regulaciones locales. Los derechos municipales de construcción ayudan a financiar los servicios y la infraestructura que apoyan el desarrollo urbano."
    }
]

def coincidencia(tokens_ref: list[str], tokens_resp: list[str]) -> float:
    """
    Calcula la proporción de tokens de referencia que aparecen en la respuesta.
    """
    if not tokens_ref: # Evita división por cero si la referencia está vacía
        return 0.0
    comunes = set(tokens_ref) & set(tokens_resp)
    return len(comunes) / len(set(tokens_ref))

if __name__ == "__main__":
    lineas = []
    for i, caso in enumerate(CASOS_DE_PRUEBA, start=1):
        respuesta = consultar_modelo(caso["pregunta"] + " Responde máximo tres líneas. ")

        #ANTES: texto crudo, solo separado por los espacios 
        pct_crudo  = coincidencia(caso["referencia"].split(), respuesta.split())

        #DESPUES:  pasando por el pipeline 
        pct_proc = coincidencia(procesar_texto(caso["referencia"]), procesar_texto(respuesta))

        lineas.append(f"[Caso {i}] Coincidencia texto crudo: {pct_crudo:.1%}")
        lineas.append(f"[Caso {i}] Coincidencia texto procesado: {pct_proc:.1%}")


    texto  = "\n".join(lineas)
    print(texto)
    with open("resultados_pipeline.txt", "w", encoding="utf-8") as f:
        f.write(texto + "\n")

        