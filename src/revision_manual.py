import json

revision_manual = [
    {
        "consulta": "¿Qué es la DOM?",
        "f1": 0.19,
        "correccion_factual": "no",
        "completitud": "no",
        "contradiccion": "no",
        "nota": "Confunde la DOM (Dirección de Obras Municipales) con el DOM de programación web (Document Object Model). Respuesta fuera de tema, sin relación con la normativa de construcción.",
    },
    {
        "consulta": "¿Qué es la línea oficial?",
        "f1": 0.25,
        "correccion_factual": "no",
        "completitud": "no",
        "contradiccion": "no",
        "nota": "Entiende 'línea oficial' como la postura de un gobierno o partido político, no como el límite entre propiedad privada y espacio público. Fuera de tema, sin relación con la normativa urbana.",
    },
    {
        "consulta": "¿Qué es un anteproyecto de edificación?",
        "f1": 0.28,
        "correccion_factual": "parcialmente",
        "completitud": "parcialmente",
        "contradiccion": "no",
        "nota": "Describe el anteproyecto de diseño arquitectónico en general, no el de edificación de la LGUC. El único fin del anteproyecto de edificación es validar las normas urbanísticas ante la DOM antes del permiso; no evalúa lo económico.",
    },
    {
        "consulta": "¿Qué es una obra menor?",
        "f1": 0.31,
        "correccion_factual": "no",
        "completitud": "no",
        "contradiccion": "sí",
        "nota": "La reduce a una reforma sencilla de mantenimiento que no toca estructura ni fachada. Una obra menor puede ser una ampliación (por ejemplo un segundo piso, bajo 100 m²) que sí altera estructura y fachada. Tampoco es un trámite básico: exige muchos antecedentes, y con más artefactos sanitarios se pide proyecto de agua potable y alcantarillado.",
    },
    {
        "consulta": "¿Qué es un revisor independiente de proyectos?",
        "f1": 0.31,
        "correccion_factual": "parcialmente",
        "completitud": "parcialmente",
        "contradiccion": "no",
        "nota": "Acierta en que verifica el cumplimiento normativo antes de ejecutar, pero lo llama 'entidad externa'; es un profesional acreditado ante el Minvu (de arquitectura o de cálculo) y es solidariamente responsable con el arquitecto o ingeniero patrocinante. Falta que se usa en proyectos de más de 100 personas de carga de ocupación y en edificios de uso público.",
    },
    {
        "consulta": "¿Qué es la Ley General de Urbanismo y Construcciones?",
        "f1": 0.45,
        "correccion_factual": "sí",
        "completitud": "parcialmente",
        "contradiccion": "no",
        "nota": "Lo que dice es correcto, pero no identifica la ley como el DFL 458 de 1975, que es el dato que más ayuda a reconocerla.",
    },
    {
        "consulta": "¿Qué es el coeficiente de constructibilidad?",
        "f1": 0.46,
        "correccion_factual": "sí",
        "completitud": "sí",
        "contradiccion": "no",
        "nota": "Definición correcta; además explica cómo se calcula (factor por la superficie del predio).",
    },
    {
        "consulta": "¿Qué es el certificado de informaciones previas?",
        "f1": 0.47,
        "correccion_factual": "sí",
        "completitud": "parcialmente",
        "contradiccion": "no",
        "nota": "Falta lo más importante: define el uso de suelo permitido (por ejemplo si se puede instalar un cementerio o un estadio). Además de la altura máxima define rasante, coeficientes de ocupación y constructibilidad, densidades y usos prohibidos. Es como los exámenes médicos de un inmueble.",
    },
    {
        "consulta": "Un terreno de 500 m2 tiene un coeficiente de constructibilidad de 1,2. ¿Cuántos m2 puedo construir como máximo?",
        "f1": 0.47,
        "correccion_factual": "sí",
        "completitud": "sí",
        "contradiccion": "no",
        "nota": "Resultado correcto (500 x 1,2 = 600 m2) y con el cálculo explicado. Aun siendo perfecta, su F1 fue solo 0,47: la métrica castiga las palabras de más.",
    },
    {
        "consulta": "¿Qué es la densidad bruta?",
        "f1": 0.49,
        "correccion_factual": "sí",
        "completitud": "sí",
        "contradiccion": "no",
        "nota": "Definición correcta de acuerdo a la LGUC y a la OGUC. Agrega la diferencia con la densidad neta.",
    },
]

if __name__ == "__main__":
    with open("revision_manual.json", "w", encoding="utf-8") as archivo:
        json.dump(revision_manual, archivo, indent=2, ensure_ascii=False)
    print(f"Guardados {len(revision_manual)} casos en revision_manual.json")