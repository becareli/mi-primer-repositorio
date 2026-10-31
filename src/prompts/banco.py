BANCO_DE_PROMPTS = [
    {
        "nombre": "extraer_datos_proyecto",
        "system_instruction": (
            "Eres un asistente de arquitectura en Chile. Del texto de una memoria de proyecto, "
            "extrae los datos y responde únicamente con un JSON con las claves "
            "'superficie_terreno_m2' (número), 'superficie_construida_total_m2' (número) "
            "y 'numero_de_pisos' (número entero). No agregues texto adicional."
        ),
        "ejemplo_usuario": (
            "Vivienda unifamiliar de 2 pisos en un terreno de 300 m2, "
            "con 100 m2 construidos en el primer piso y 80 m2 en el segundo."
        ),
        "claves_esperadas": [
            "superficie_terreno_m2",
            "superficie_construida_total_m2",
            "numero_de_pisos",
        ],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "superficie_terreno_m2": {"type": "NUMBER"},
                "superficie_construida_total_m2": {"type": "NUMBER"},
                "numero_de_pisos": {"type": "INTEGER"},
            },
            "required": [
                "superficie_terreno_m2",
                "superficie_construida_total_m2",
                "numero_de_pisos",
            ],
        },
    },
    {
        "nombre": "clasificar_consulta",
        "system_instruction": (
            "Eres un asistente de normativa de arquitectura y construcción de Chile. "
            "Clasifica la consulta del usuario y responde únicamente con un JSON con las claves "
            "'categoria' ('ocupacion_suelo', 'constructibilidad', 'documentos', 'rasantes' u 'otro') "
            "y 'confianza' (número entre 0 y 1). No agregues texto adicional."
        ),
        "ejemplo_usuario": "¿Qué documentos necesito para ingresar un permiso de edificación en la DOM?",
        "claves_esperadas": ["categoria", "confianza"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "categoria": {"type": "STRING"},
                "confianza": {"type": "NUMBER"},
            },
            "required": ["categoria", "confianza"],
        },
    },
    {
        "nombre": "detectar_documentos_faltantes",
        "system_instruction": (
            "Eres un revisor de expedientes de permiso de edificación en Chile. "
            "Según los documentos que el usuario dice haber entregado, responde únicamente con un JSON "
            "con las claves 'documentos_faltantes' (lista de textos) y 'expediente_completo' "
            "(verdadero o falso). Considera como documentos mínimos: formulario de solicitud, "
            "certificado de informaciones previas, título de dominio, planos de arquitectura "
            "y especificaciones técnicas. No agregues texto adicional."
        ),
        "ejemplo_usuario": (
            "El expediente incluye el formulario de solicitud, el certificado de informaciones previas "
            "y los planos de arquitectura."
        ),
        "claves_esperadas": ["documentos_faltantes", "expediente_completo"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "documentos_faltantes": {"type": "ARRAY", "items": {"type": "STRING"}},
                "expediente_completo": {"type": "BOOLEAN"},
            },
            "required": ["documentos_faltantes", "expediente_completo"],
        },
    },
]