"""Bloque 29 - Dataset propio para personalizacion (PEFT).

Tarea: funcion 1 del copiloto de ArquitectoChile
"extraer la ficha del proyecto desde el mensaje libre del cliente".
Es un problema de COMPORTAMIENTO consistente (texto libre -> JSON fijo),
no de conocimiento: por eso es candidato a tuning y no a RAG.

Uso (desde la raiz del repo, con el (.venv) activo):
    python src\\dataset_tuning.py
"""
import copy
import json
import time
from collections import Counter

from google import genai
from google.genai import types

# ---------------------------------------------------------------
# Reglas del formato (el "contrato" que el modelo debe aprender)
# ---------------------------------------------------------------
CLAVES = (
    "rol_cliente",
    "destino",
    "destino_declarado",
    "comuna",
    "ingreso_dom",
    "superficie_existente_m2",
    "superficie_nueva_m2",
    "estructura",
)

VALORES_PERMITIDOS = {
    "rol_cliente": {"arquitecto", "constructora", "mandante"},
    "destino": {
        "habitacional", "comercial", "industrial", "oficinas",
        "educacional", "jardin_infantil", "salud", "otro",
    },
    "ingreso_dom": {"si", "no"},
    "estructura": {"acero", "hormigon", "albanileria", "madera", "mixta"},
    # "destino_declarado" NO se restringe: es el texto libre del cliente.
}

# ---------------------------------------------------------------
# PASO 1: ejemplos (mensajes INVENTADOS, sin datos personales).
# Regla de oro: si el mensaje no dice el dato, la salida es null.
# ---------------------------------------------------------------
ejemplos_raw = [
    # --- habitacional ---
    (
        "Hola, soy arquitecta del proyecto: un edificio de departamentos en Nunoa, "
        "6 pisos de hormigon armado. Son 3.200 m2 de obra nueva y no hay construccion "
        "previa en el terreno. Aun no lo ingresamos a la DOM.",
        {"rol_cliente": "arquitecto", "destino": "habitacional", "destino_declarado": "edificio de departamentos", "comuna": "Nunoa",
         "ingreso_dom": "no", "superficie_existente_m2": 0,
         "superficie_nueva_m2": 3200, "estructura": "hormigon"},
    ),
    (
        "Buenas, somos constructora y tenemos un conjunto de 18 casas de madera en "
        "Puerto Montt, 1.450 m2 en total. Ya ingreso a la DOM y nos entregaron acta "
        "de observaciones.",
        {"rol_cliente": "constructora", "destino": "habitacional", "destino_declarado": "casas", "comuna": "Puerto Montt",
         "ingreso_dom": "si", "superficie_existente_m2": None,
         "superficie_nueva_m2": 1450, "estructura": "madera"},
    ),
    # --- comercial ---
    (
        "Necesito cotizar el informe favorable de un strip center en La Florida, "
        "2.100 m2 nuevos, estructura de acero. Soy el dueno del terreno.",
        {"rol_cliente": "mandante", "destino": "comercial", "destino_declarado": "strip center", "comuna": "La Florida",
         "ingreso_dom": None, "superficie_existente_m2": None,
         "superficie_nueva_m2": 2100, "estructura": "acero"},
    ),
    (
        "Ampliacion de un supermercado en Rancagua: hoy tiene 1.800 m2 con recepcion "
        "final y vamos a agregar 650 m2. Soy el arquitecto, la muni ya nos dio acta "
        "de observaciones. Estructura mixta.",
        {"rol_cliente": "arquitecto", "destino": "comercial", "destino_declarado": "supermercado", "comuna": "Rancagua",
         "ingreso_dom": "si", "superficie_existente_m2": 1800,
         "superficie_nueva_m2": 650, "estructura": "mixta"},
    ),
    # --- industrial ---
    (
        "Bodega logistica en Quilicura, 4.500 m2, galpon metalico. Todavia no entra "
        "a la DOM. Escribo como gerente de la empresa duena del proyecto.",
        {"rol_cliente": "mandante", "destino": "industrial", "destino_declarado": "bodega logistica", "comuna": "Quilicura",
         "ingreso_dom": "no", "superficie_existente_m2": None,
         "superficie_nueva_m2": 4500, "estructura": "acero"},
    ),
    (
        "Hola, ampliacion de planta de alimentos en San Bernardo. Existente 3.000 m2 "
        "con recepcion, ampliamos 900 m2. Somos la constructora a cargo.",
        {"rol_cliente": "constructora", "destino": "industrial", "destino_declarado": "planta de alimentos", "comuna": "San Bernardo",
         "ingreso_dom": None, "superficie_existente_m2": 3000,
         "superficie_nueva_m2": 900, "estructura": None},
    ),
    # --- oficinas ---
    (
        "Edificio de oficinas en Las Condes, 12 pisos, 8.000 m2 nuevos, hormigon. "
        "Soy el arquitecto del proyecto y aun no lo ingresamos.",
        {"rol_cliente": "arquitecto", "destino": "oficinas", "destino_declarado": "edificio de oficinas", "comuna": "Las Condes",
         "ingreso_dom": "no", "superficie_existente_m2": None,
         "superficie_nueva_m2": 8000, "estructura": "hormigon"},
    ),
    (
        "Remodelacion de oficinas en Providencia: el edificio tiene 2.500 m2 con "
        "recepcion final y la remodelacion suma 300 m2. Soy el propietario. Ya "
        "tuvimos acta de observaciones.",
        {"rol_cliente": "mandante", "destino": "oficinas", "destino_declarado": "oficinas", "comuna": "Providencia",
         "ingreso_dom": "si", "superficie_existente_m2": 2500,
         "superficie_nueva_m2": 300, "estructura": None},
    ),
    # --- educacional ---
    (
        "Colegio nuevo en Puente Alto, 5.600 m2, albanileria confinada. Somos la "
        "sostenedora y queremos contratar el revisor. No ha ingresado a la DOM.",
        {"rol_cliente": "mandante", "destino": "educacional", "destino_declarado": "colegio", "comuna": "Puente Alto",
         "ingreso_dom": "no", "superficie_existente_m2": None,
         "superficie_nueva_m2": 5600, "estructura": "albanileria"},
    ),
    (
        "Ampliacion de un liceo en Temuco: 4.200 m2 existentes con recepcion final, "
        "queremos agregar un pabellon de 800 m2. Soy el arquitecto; ya tuvimos acta "
        "de observaciones.",
        {"rol_cliente": "arquitecto", "destino": "educacional", "destino_declarado": "liceo", "comuna": "Temuco",
         "ingreso_dom": "si", "superficie_existente_m2": 4200,
         "superficie_nueva_m2": 800, "estructura": None},
    ),
    # --- jardin infantil ---
    (
        "Jardin infantil nuevo en Maipu, 620 m2, estructura de madera. Soy arquitecta "
        "y todavia no lo ingresamos a la DOM.",
        {"rol_cliente": "arquitecto", "destino": "jardin_infantil", "destino_declarado": "jardin infantil", "comuna": "Maipu",
         "ingreso_dom": "no", "superficie_existente_m2": None,
         "superficie_nueva_m2": 620, "estructura": "madera"},
    ),
    (
        "Quiero regularizar la ampliacion de mi jardin infantil en Valdivia: tiene "
        "350 m2 con recepcion y la ampliacion es de 120 m2. Soy la duena.",
        {"rol_cliente": "mandante", "destino": "jardin_infantil", "destino_declarado": "jardin infantil", "comuna": "Valdivia",
         "ingreso_dom": None, "superficie_existente_m2": 350,
         "superficie_nueva_m2": 120, "estructura": None},
    ),
    # --- salud ---
    (
        "Clinica en Vina del Mar, 7 pisos de hormigon armado, 9.500 m2 nuevos. Somos "
        "la constructora. Ya ingreso a la DOM, tenemos acta.",
        {"rol_cliente": "constructora", "destino": "salud", "destino_declarado": "clinica", "comuna": "Vina del Mar",
         "ingreso_dom": "si", "superficie_existente_m2": None,
         "superficie_nueva_m2": 9500, "estructura": "hormigon"},
    ),
    (
        "Centro medico en Concepcion: ampliacion de 400 m2 sobre un existente de "
        "1.100 m2 con recepcion. Soy arquitecto. Estructura de acero.",
        {"rol_cliente": "arquitecto", "destino": "salud", "destino_declarado": "centro medico", "comuna": "Concepcion",
         "ingreso_dom": None, "superficie_existente_m2": 1100,
         "superficie_nueva_m2": 400, "estructura": "acero"},
    ),
    # --- destino que el cliente escribe distinto a la categoria ---
    (
        "Hola, necesito el informe favorable para un motel en Pudahuel, 900 m2 "
        "nuevos, albanileria. Soy el dueno y aun no lo ingreso a la DOM.",
        {"rol_cliente": "mandante", "destino": "habitacional", "destino_declarado": "motel",
         "comuna": "Pudahuel", "ingreso_dom": "no", "superficie_existente_m2": None,
         "superficie_nueva_m2": 900, "estructura": "albanileria"},
    ),
    # --- destino fuera de la lista: se conserva tal cual y lo revisa el humano ---
    (
        "Buenas tardes, somos una sociedad que quiere construir un casino en Arica, "
        "6.000 m2 nuevos, hormigon. Soy el arquitecto del proyecto.",
        {"rol_cliente": "arquitecto", "destino": "otro", "destino_declarado": "casino",
         "comuna": "Arica", "ingreso_dom": None, "superficie_existente_m2": None,
         "superficie_nueva_m2": 6000, "estructura": "hormigon"},
    ),
]

examples = [
    types.TuningExample(
        text_input=texto,
        output=json.dumps(salida, ensure_ascii=False),
    )
    for texto, salida in ejemplos_raw
]


# ---------------------------------------------------------------
# PASO 2: balance por categoria
# ---------------------------------------------------------------
def chequear_balance(ejemplos_raw: list[tuple[str, dict]], clave: str) -> Counter:
    """Cuenta cuantos ejemplos hay por valor de `clave`."""
    return Counter(salida[clave] for _, salida in ejemplos_raw)


# ---------------------------------------------------------------
# PASO 3: validador (devuelve lista de problemas; vacia = dataset listo)
# ---------------------------------------------------------------
def validar_dataset(
    examples: list[types.TuningExample],
    claves_esperadas: tuple[str, ...],
    valores_permitidos: dict[str, set] | None = None,
) -> list[str]:
    problemas = []
    vistos = set()
    for i, ej in enumerate(examples):
        if not ej.text_input or not ej.text_input.strip():
            problemas.append(f"ejemplo {i}: text_input vacio")
        if not ej.output or not ej.output.strip():
            problemas.append(f"ejemplo {i}: output vacio")
            continue
        if ej.text_input in vistos:
            problemas.append(f"ejemplo {i}: text_input duplicado")
        vistos.add(ej.text_input)
        try:
            salida = json.loads(ej.output)
        except json.JSONDecodeError:
            problemas.append(f"ejemplo {i}: output no es JSON valido")
            continue
        for clave in claves_esperadas:
            if clave not in salida:
                problemas.append(f'ejemplo {i}: output no tiene la clave "{clave}"')
        # Extra propio de este proyecto: valores fuera del vocabulario permitido.
        for clave, permitidos in (valores_permitidos or {}).items():
            valor = salida.get(clave)
            if valor is not None and valor not in permitidos:
                problemas.append(f'ejemplo {i}: "{clave}" con valor no permitido: {valor!r}')
    return problemas


# ---------------------------------------------------------------
# PASO 4 (DEMO, NO se ejecuta): enviar y seguir un trabajo de tuning.
# Requiere cuenta con tuning habilitado y modelo base que lo soporte
# (verificar en la documentacion antes de usar). Puede tener costo.
# ---------------------------------------------------------------
MODELO_BASE_TUNING = "REEMPLAZAR-por-un-modelo-que-soporte-tuning"


def enviar_tuning(client: genai.Client, examples: list[types.TuningExample]) -> str:
    trabajo = client.tunings.tune(
        base_model=MODELO_BASE_TUNING,
        training_dataset=types.TuningDataset(examples=examples),
        config=types.CreateTuningJobConfig(
            tuned_model_display_name="ficha-cliente-arquitectochile",
            epoch_count=5,
        ),
    )
    return trabajo.name


def esperar_a_que_termine(
    client: genai.Client, nombre_trabajo: str, intervalo_segundos: int = 30
) -> types.TuningJob:
    estados_finales = {
        types.JobState.JOB_STATE_SUCCEEDED,
        types.JobState.JOB_STATE_FAILED,
        types.JobState.JOB_STATE_CANCELLED,
        types.JobState.JOB_STATE_PARTIALLY_SUCCEEDED,
    }
    while True:
        trabajo = client.tunings.get(name=nombre_trabajo)
        print(f"estado actual: {trabajo.state}")
        if trabajo.state in estados_finales:
            return trabajo
        time.sleep(intervalo_segundos)


def main() -> None:
    print(len(examples), "ejemplos construidos\n")

    print("PASO 1: balance de MI dataset (por destino)")
    for categoria, cuenta in chequear_balance(ejemplos_raw, "destino").most_common():
        print(f"  {categoria}: {cuenta}")

    print("\nPASO 2: validacion de MI dataset")
    problemas = validar_dataset(examples, CLAVES, VALORES_PERMITIDOS)
    print(f"{len(examples)} ejemplos, {len(problemas)} problemas encontrados")
    for p in problemas:
        print(" -", p)

    print("\nPASO 3: rompo un ejemplo a proposito")
    rotos = copy.deepcopy(examples)
    rotos[2].output = rotos[2].output.replace('"', "'")  # comillas simples = JSON invalido
    problemas_rotos = validar_dataset(rotos, CLAVES, VALORES_PERMITIDOS)
    print(f"{len(rotos)} ejemplos, {len(problemas_rotos)} problemas encontrados")
    for p in problemas_rotos:
        print(" -", p)


if __name__ == "__main__":
    main()
