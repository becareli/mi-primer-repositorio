"""Bloque 30 - Medir con evidencia la pregunta "problema_de_formato_o_tono".

Toma 20 mensajes NUEVOS de clientes (ninguno esta entre los 16 del dataset),
le pide al modelo la ficha JSON y cuenta cuantas respuestas incumplen el formato.

Uso (desde la raiz del repo, con el (.venv) activo):
    python src\\probar_extraccion.py             # modelo base, sin ejemplos
    python src\\probar_extraccion.py --fewshot   # modelo base + los 16 ejemplos en el prompt
"""
import argparse
import json
import re
import unicodedata

from dataset_tuning import CLAVES, VALORES_PERMITIDOS, ejemplos_raw

MODELO = "gemini-3.8-flash"
UMBRAL_FALLOS = 3  # criterio del curso: 3 o mas de 20 (15 %) incumplen

# Etiquetas escritas ANTES de ver lo que responde el modelo. No las cambies despues.
# Revisalas con tu criterio de revisor (p. ej. hotel, gimnasio, Cesfam, iglesia).
CASOS_PRUEBA = [
    ("Hola Patricio, soy el arquitecto del proyecto. Es un edificio de oficinas de 5 pisos en Viña del Mar, unos 4.800 m². Estructura de hormigón. Todavía no lo hemos ingresado a la DOM.",
     {"rol_cliente": "arquitecto", "destino": "oficinas", "destino_declarado": "edificio de oficinas", "comuna": "Viña del Mar", "ingreso_dom": "no", "superficie_existente_m2": None, "superficie_nueva_m2": 4800, "estructura": "hormigon"}),
    ("Buenas tardes, necesito cotización. Somos la inmobiliaria dueña del terreno y vamos a construir 120 departamentos en Concepción, 9.300 m2 construidos, hormigón armado. Ya pasó por la DOM y tenemos acta.",
     {"rol_cliente": "mandante", "destino": "habitacional", "destino_declarado": "departamentos", "comuna": "Concepción", "ingreso_dom": "si", "superficie_existente_m2": None, "superficie_nueva_m2": 9300, "estructura": "hormigon"}),
    ("Colegio en Coquimbo, ampliación. Existente 2.200 mt2 con recepción final, ampliamos 540 mt2 más. Soy el arquitecto. Albañilería.",
     {"rol_cliente": "arquitecto", "destino": "educacional", "destino_declarado": "colegio", "comuna": "Coquimbo", "ingreso_dom": None, "superficie_existente_m2": 2200, "superficie_nueva_m2": 540, "estructura": "albanileria"}),
    ("wena, necesito el informe favorable pa un gimnasio municipal en Peñalolén, 1.100 m2 nuevos. soy de la constructora",
     {"rol_cliente": "constructora", "destino": "otro", "destino_declarado": "gimnasio municipal", "comuna": "Peñalolén", "ingreso_dom": None, "superficie_existente_m2": None, "superficie_nueva_m2": 1100, "estructura": None}),
    ("Jardín infantil JUNJI en Calama, 480 m². Estructura metálica. Soy la arquitecta y aún no ingresamos.",
     {"rol_cliente": "arquitecto", "destino": "jardin_infantil", "destino_declarado": "jardín infantil", "comuna": "Calama", "ingreso_dom": "no", "superficie_existente_m2": None, "superficie_nueva_m2": 480, "estructura": "acero"}),
    ("Consulta: un hospital en Antofagasta de 15.000 m2, 8 pisos. Representamos al mandante. No sabemos si ya ingresó.",
     {"rol_cliente": "mandante", "destino": "salud", "destino_declarado": "hospital", "comuna": "Antofagasta", "ingreso_dom": None, "superficie_existente_m2": None, "superficie_nueva_m2": 15000, "estructura": None}),
    ("Somos una empresa de logística. Queremos ampliar nuestra bodega de Lampa: tiene 6.000 m² con permiso y recepción, y agregamos 2.500 m² en estructura de acero.",
     {"rol_cliente": "mandante", "destino": "industrial", "destino_declarado": "bodega", "comuna": "Lampa", "ingreso_dom": None, "superficie_existente_m2": 6000, "superficie_nueva_m2": 2500, "estructura": "acero"}),
    ("Soy dueño de un motel en Machalí. Quiero regularizar una ampliación de 150 m2. Existente 600 m2 con recepción. Ya tengo acta de observaciones de la DOM.",
     {"rol_cliente": "mandante", "destino": "habitacional", "destino_declarado": "motel", "comuna": "Machalí", "ingreso_dom": "si", "superficie_existente_m2": 600, "superficie_nueva_m2": 150, "estructura": None}),
    ("Hola! Casas de madera en Osorno, un conjunto de 24 casas, total 2.900 m2. Soy constructora. No ingresado todavía.",
     {"rol_cliente": "constructora", "destino": "habitacional", "destino_declarado": "casas", "comuna": "Osorno", "ingreso_dom": "no", "superficie_existente_m2": None, "superficie_nueva_m2": 2900, "estructura": "madera"}),
    ("Necesito cotizar un centro comercial en Talca, 12.000 metros cuadrados nuevos, estructura mixta.",
     {"rol_cliente": None, "destino": "comercial", "destino_declarado": "centro comercial", "comuna": "Talca", "ingreso_dom": None, "superficie_existente_m2": None, "superficie_nueva_m2": 12000, "estructura": "mixta"}),
    ("Iglesia evangélica en Rancagua, 700 m2 nuevos, albañilería confinada. Soy el pastor y dueño del proyecto.",
     {"rol_cliente": "mandante", "destino": "otro", "destino_declarado": "iglesia evangélica", "comuna": "Rancagua", "ingreso_dom": None, "superficie_existente_m2": None, "superficie_nueva_m2": 700, "estructura": "albanileria"}),
    ("Clínica dental en Providencia: remodelación de un edificio existente (1.800 m2 con recepción) más 200 m2 nuevos. Soy arquitecto, ya tuvimos acta de observaciones.",
     {"rol_cliente": "arquitecto", "destino": "salud", "destino_declarado": "clínica dental", "comuna": "Providencia", "ingreso_dom": "si", "superficie_existente_m2": 1800, "superficie_nueva_m2": 200, "estructura": None}),
    ("Edificio corporativo en Santiago centro, 20.000 m2, hormigón. Soy el mandante y pido cotización.",
     {"rol_cliente": "mandante", "destino": "oficinas", "destino_declarado": "edificio corporativo", "comuna": "Santiago", "ingreso_dom": None, "superficie_existente_m2": None, "superficie_nueva_m2": 20000, "estructura": "hormigon"}),
    ("Liceo técnico en Iquique. Proyecto nuevo de 3.400 m². Constructora a cargo. Estructura de albañilería. Aún no entra a DOM.",
     {"rol_cliente": "constructora", "destino": "educacional", "destino_declarado": "liceo técnico", "comuna": "Iquique", "ingreso_dom": "no", "superficie_existente_m2": None, "superficie_nueva_m2": 3400, "estructura": "albanileria"}),
    ("Buenos días, restaurante con terraza en Pucón, 380 m2, madera. Soy arquitecto. Ya ingresamos y nos dieron acta.",
     {"rol_cliente": "arquitecto", "destino": "comercial", "destino_declarado": "restaurante", "comuna": "Pucón", "ingreso_dom": "si", "superficie_existente_m2": None, "superficie_nueva_m2": 380, "estructura": "madera"}),
    ("Fábrica de muebles en San Bernardo, 2.000 m2 existentes con recepción, ampliación de 750 m2. Soy el mandante.",
     {"rol_cliente": "mandante", "destino": "industrial", "destino_declarado": "fábrica de muebles", "comuna": "San Bernardo", "ingreso_dom": None, "superficie_existente_m2": 2000, "superficie_nueva_m2": 750, "estructura": None}),
    ("Cesfam en Maipú, 1.600 m2 nuevos, hormigón armado. Somos la constructora que ganó la licitación; no ha ingresado a la DOM.",
     {"rol_cliente": "constructora", "destino": "salud", "destino_declarado": "Cesfam", "comuna": "Maipú", "ingreso_dom": "no", "superficie_existente_m2": None, "superficie_nueva_m2": 1600, "estructura": "hormigon"}),
    ("Hola, quiero saber cuánto cuesta un informe favorable para mi proyecto",
     {"rol_cliente": None, "destino": None, "destino_declarado": None, "comuna": None, "ingreso_dom": None, "superficie_existente_m2": None, "superficie_nueva_m2": None, "estructura": None}),
    ("buenas, tngo un edificio d departamentos en la florida 5 pisos 2500 m2 soy el dueño, hormigon, no ingresa a dom",
     {"rol_cliente": "mandante", "destino": "habitacional", "destino_declarado": "edificio de departamentos", "comuna": "La Florida", "ingreso_dom": "no", "superficie_existente_m2": None, "superficie_nueva_m2": 2500, "estructura": "hormigon"}),
    ("Hotel en Puerto Varas, dos mil quinientos metros cuadrados nuevos, estructura mixta. Soy arquitecto.",
     {"rol_cliente": "arquitecto", "destino": "habitacional", "destino_declarado": "hotel", "comuna": "Puerto Varas", "ingreso_dom": None, "superficie_existente_m2": None, "superficie_nueva_m2": 2500, "estructura": "mixta"}),
]

INSTRUCCION = """Eres un asistente de ArquitectoChile. Convierte el mensaje de un cliente en una ficha JSON.
Campos (todos obligatorios; si el mensaje no dice el dato, usa null):
- rol_cliente: arquitecto | constructora | mandante
- destino: habitacional | comercial | industrial | oficinas | educacional | jardin_infantil | salud | otro
- destino_declarado: las palabras del cliente para el destino, tal cual
- comuna: texto
- ingreso_dom: si | no
- superficie_existente_m2: numero
- superficie_nueva_m2: numero
- estructura: acero | hormigon | albanileria | madera | mixta
Responde solo con el JSON."""


def construir_prompt(mensaje: str, fewshot: bool) -> str:
    partes = [INSTRUCCION]
    if fewshot:
        partes.append("Ejemplos:")
        for texto, salida in ejemplos_raw:
            partes.append(f"Mensaje: {texto}\nFicha: {json.dumps(salida, ensure_ascii=False)}")
    partes.append(f"Mensaje: {mensaje}\nFicha:")
    return "\n\n".join(partes)


def limpiar_cercas(texto: str) -> str:
    """Quita las cercas ```json ... ``` que el modelo suele agregar (arreglo de una linea)."""
    t = (texto or "").strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\s*", "", t)
        t = re.sub(r"\s*```$", "", t)
    return t.strip()


def problemas_de_formato(texto: str) -> list[str]:
    """Lista fija de criterios de formato. Lista vacia = cumple."""
    try:
        salida = json.loads(texto)
    except json.JSONDecodeError:
        return ["no es JSON valido"]
    if not isinstance(salida, dict):
        return ["no es un objeto JSON"]
    problemas = []
    for clave in CLAVES:
        if clave not in salida:
            problemas.append(f'falta la clave "{clave}"')
    for clave in salida:
        if clave not in CLAVES:
            problemas.append(f'clave inesperada "{clave}"')
    for clave, permitidos in VALORES_PERMITIDOS.items():
        valor = salida.get(clave)
        if valor is not None and valor not in permitidos:
            problemas.append(f'"{clave}" con valor no permitido: {valor!r}')
    for clave in ("superficie_existente_m2", "superficie_nueva_m2"):
        valor = salida.get(clave)
        if valor is not None and (isinstance(valor, bool) or not isinstance(valor, (int, float))):
            problemas.append(f'"{clave}" debe ser numero o null: {valor!r}')
    return problemas


def _norm(valor):
    if isinstance(valor, str):
        sin_tildes = unicodedata.normalize("NFD", valor)
        return "".join(c for c in sin_tildes if unicodedata.category(c) != "Mn").strip().lower()
    return valor


def comparar_campos(salida: dict, esperado: dict) -> int:
    """Cuenta campos correctos (8 por mensaje). destino_declarado solo exige null/no-null."""
    aciertos = 0
    for clave in CLAVES:
        if clave == "destino_declarado":
            aciertos += (salida.get(clave) is None) == (esperado[clave] is None)
        else:
            aciertos += _norm(salida.get(clave)) == _norm(esperado[clave])
    return aciertos


def evaluar(respuestas: list[str], casos=CASOS_PRUEBA) -> dict:
    fallos_estrictos = incumplimientos = aciertos = 0
    detalle = []
    for i, (crudo, (_, esperado)) in enumerate(zip(respuestas, casos)):
        crudo = crudo or ""
        try:
            json.loads(crudo.strip())
        except json.JSONDecodeError:
            fallos_estrictos += 1
        limpio = limpiar_cercas(crudo)
        problemas = problemas_de_formato(limpio)
        incumplimientos += bool(problemas)
        ac = 0 if problemas and problemas[0].startswith("no es") else None
        if ac is None:
            ac = comparar_campos(json.loads(limpio), esperado)
        aciertos += ac
        detalle.append({"caso": i, "problemas": problemas, "campos_correctos": ac})
    return {
        "n": len(casos),
        "fallos_estrictos": fallos_estrictos,
        "incumplimientos": incumplimientos,
        "aciertos_campos": aciertos,
        "total_campos": len(casos) * len(CLAVES),
        "detalle": detalle,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fewshot", action="store_true")
    args = parser.parse_args()
    modo = "fewshot" if args.fewshot else "zeroshot"

    from dotenv import load_dotenv
    from google import genai

    load_dotenv()
    client = genai.Client()
    respuestas = []
    for i, (mensaje, _) in enumerate(CASOS_PRUEBA):
        try:
            r = client.models.generate_content(model=MODELO, contents=construir_prompt(mensaje, args.fewshot))
        except Exception as error:
            raise SystemExit(f"Error llamando al modelo en el caso {i}: {error}")
        respuestas.append(r.text or "")
        print(f"caso {i:2d} listo")

    res = evaluar(respuestas)
    res["modo"] = modo
    res["respuestas_crudas"] = respuestas
    nombre = f"resultados_extraccion_{modo}.json"
    with open(nombre, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)

    print(f"\nModo: {modo}")
    print(f"Incumplen el formato estricto (json.loads directo): {res['fallos_estrictos']} de {res['n']}")
    print(f"Incumplen el formato tras quitar cercas ```: {res['incumplimientos']} de {res['n']}  (umbral del curso: {UMBRAL_FALLOS})")
    print(f"Campos correctos: {res['aciertos_campos']} de {res['total_campos']}")
    for d in res["detalle"]:
        if d["problemas"]:
            print(f"  caso {d['caso']}: {d['problemas']}")
    print(f"\nGuardado en {nombre}")


if __name__ == "__main__":
    main()
