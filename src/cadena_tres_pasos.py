import os

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from carga_ocupacion import (
    TABLA_M2_POR_PERSONA,
    calcular_carga_total,
    es_edificio_uso_publico,
)

# Regla de negocio. Fuente: dictamen UrbaLEX REG-2026-RI01 (verificar con LGUC/OGUC).
REGLAS = (
    "- Edificio de uso público (carga de ocupación mayor a 100 personas, o propiedad "
    "pública destinada a atención de público): el informe favorable del revisor "
    "independiente es OBLIGATORIO (Art. 116 bis LGUC; Art. 1.1.2 y 5.1.6 OGUC).\n"
    "- Carga de 100 personas o menos: es VOLUNTARIO. Si se contrata, rebaja de 30% "
    "en derechos municipales y plazo de revisión de la DOM de 15 días hábiles.\n"
    "- Anteproyecto de edificación: VOLUNTARIO (Art. 5.1.5 OGUC).\n"
    "- Vivienda social: EXENTO/ESPECIAL (Art. 116 bis A LGUC)."
)


def calcular_en_python(texto: str) -> dict:
    """Función intermedia: lee la salida del paso 1 y calcula la carga SIN usar la IA."""
    especial = "ninguna"
    sectores = []
    for linea in texto.strip().splitlines():
        linea = linea.strip()
        if linea.lower().startswith("especial:"):
            especial = linea.split(":", 1)[1].strip()
        elif linea.lower().startswith("sector:"):
            destino, superficie = linea.split(":", 1)[1].split("|")
            sectores.append((destino.strip(), float(superficie.strip())))
    if not sectores:
        raise ValueError("El paso 1 no entregó ningún sector con destino y superficie.")
    carga = calcular_carga_total(sectores)
    return {
        "especial": especial,
        "carga": round(carga, 1),
        "es_uso_publico": "SÍ" if es_edificio_uso_publico(carga) else "NO",
        "reglas": REGLAS,
    }


def construir_cadena(modelo):
    """Arma la cadena de tres pasos y la devuelve sin ejecutarla."""
    # PASO 1: leer la descripción libre y dejarla en formato fijo.
    plantilla_extraer = PromptTemplate.from_template(
        "Lee la descripción de un proyecto de edificación. Responde SOLO con estas "
        "líneas, sin texto adicional:\n"
        "especial: ninguna, vivienda_social, propiedad_publica o anteproyecto\n"
        "sector: <destino> | <superficie_m2 solo el número>\n"
        "Una línea 'sector' por cada destino. El destino debe ser EXACTAMENTE uno de "
        "esta lista: {destinos}. Si no está, usa el más parecido.\n\n"
        "Descripción: {descripcion}"
    ).partial(destinos=", ".join(TABLA_M2_POR_PERSONA))
    paso_extraer = plantilla_extraer | modelo | StrOutputParser()

    # PASO 2: aplicar la regla a los datos ya calculados.
    plantilla_determinar = PromptTemplate.from_template(
        "Aplica estas reglas sobre el informe favorable de revisor independiente:\n"
        "{reglas}\n\n"
        "Datos del proyecto: caso especial = {especial}; carga de ocupación = {carga} "
        "personas; ¿es edificio de uso público? = {es_uso_publico}.\n"
        "Responde en 2 líneas: 'Determinación: OBLIGATORIO, VOLUNTARIO, EXENTO o "
        "REQUIERE REVISIÓN HUMANA' y 'Motivo:' citando el artículo y copiando la carga "
        "tal como te la di. Si los datos no calzan con ninguna regla, usa REQUIERE "
        "REVISIÓN HUMANA."
    )
    paso_determinar = plantilla_determinar | modelo | StrOutputParser()

    # PASO 3: explicar el resultado al arquitecto.
    plantilla_explicar = PromptTemplate.from_template(
        "Eres un revisor de arquitectura. Con esta determinación:\n{determinacion}\n"
        "Escribe un mensaje de máximo 4 líneas para el arquitecto. Nombra siempre el "
        "documento con estas palabras exactas: 'informe favorable de revisor "
        "independiente de arquitectura, acreditado en el MINVU'. Indica qué debe hacer "
        "a continuación y, si es voluntario, el beneficio (rebaja de 30% y 15 días "
        "hábiles de revisión). No inventes datos que no estén en la determinación."
    )
    paso_explicar = plantilla_explicar | modelo | StrOutputParser()

    return (
        paso_extraer
        | calcular_en_python
        | paso_determinar
        | (lambda determinacion: {"determinacion": determinacion})
        | paso_explicar
    )


if __name__ == "__main__":
    load_dotenv()
    modelo = ChatGoogleGenerativeAI(
        model="gemini-3.8-flash", google_api_key=os.getenv("GEMINI_API_KEY")
    )
    cadena = construir_cadena(modelo)
    resultado = cadena.invoke(
        {
            "descripcion": (
                "Obra nueva en Providencia: oficinas con 500 m2 de superficie útil y "
                "816 m2 de estacionamientos de uso común."
            )
        }
    )
    print(resultado)