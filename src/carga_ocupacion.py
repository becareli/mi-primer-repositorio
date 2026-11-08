# Tabla de carga de ocupación, OGUC Art. 4.2.4 (m2 por persona).
# Fuente: texto del artículo (versión impresa marzo 2016): verificar que siga vigente.
TABLA_M2_POR_PERSONA = {
    # Vivienda (superficie útil, por unidad)
    "vivienda_hasta_60": 15.0,
    "vivienda_mas_de_60_hasta_140": 20.0,
    "vivienda_mas_de_140": 30.0,
    # Oficinas (superficie útil)
    "oficinas": 10.0,
    # Comercio (locales en general)
    "comercio_sala_venta_niveles_menos1_1_y_2": 3.0,
    "comercio_sala_venta_otros_pisos": 5.0,
    "supermercado_area_publico": 3.0,
    "supermercado_trastienda": 15.0,
    "mercado_feria_area_publico": 1.0,
    "mercado_feria_puestos_venta": 4.0,
    # Comercio (malls)
    "mall_locales_nivel_acceso_exterior": 10.0,
    "mall_pasillos_nivel_acceso_exterior": 5.0,
    "mall_locales_otros_niveles": 14.0,
    "mall_pasillos_otros_niveles": 7.0,
    "mall_patio_comidas_areas_con_mesas": 1.0,
    # Educación
    "educacion_salones_auditorios": 0.5,
    "educacion_uso_multiple_casino": 1.0,
    "educacion_salas_de_clase": 1.5,
    "educacion_camarines_gimnasios": 4.0,
    "educacion_talleres_laboratorios_bibliotecas": 5.0,
    "educacion_oficinas_administrativas": 7.0,
    "educacion_cocina": 15.0,
    # Salud (hospitales y clínicas)
    "salud_ambulatorio_y_diagnostico": 6.0,
    "salud_sector_habitaciones": 8.0,
    "salud_oficinas_administrativas": 10.0,
    "salud_tratamiento_pacientes_internos": 20.0,
    # Salud (consultorios, policlínicos)
    "consultorio_salas_de_espera": 0.8,
    "consultorio_consultas": 3.0,
    # Otros
    "espectaculos_espectadores_de_pie": 0.25,
    "capillas_discotecas": 0.5,
    "salones_de_reuniones": 0.8,
    "bares_cafeterias_pubs_area_publico": 1.0,
    "restaurantes_comedores_salones_de_juego": 1.5,
    "salas_de_exposicion": 3.0,
    "hogares_de_ninos": 3.0,
    "gimnasios_academias_de_danza": 4.0,
    "hogares_de_ancianos": 6.0,
    "estacionamientos": 16.0,
    "hoteles": 18.0,
    "bodegas_archivos": 40.0,
}

UMBRAL_EDIFICIO_USO_PUBLICO = 100  # personas: más de 100 = edificio de uso público


def calcular_carga(destino: str, superficie_m2: float) -> float:
    """Carga de ocupación (personas) de un sector: superficie ÷ m2 por persona."""
    if destino not in TABLA_M2_POR_PERSONA:
        raise ValueError(f"Destino no está en la tabla del Art. 4.2.4: {destino}")
    if superficie_m2 <= 0:
        raise ValueError("La superficie debe ser mayor que cero.")
    return superficie_m2 / TABLA_M2_POR_PERSONA[destino]


def calcular_carga_total(sectores: list[tuple[str, float]]) -> float:
    """Suma la carga de cada sector, cada uno según su propio destino."""
    return sum(calcular_carga(destino, superficie) for destino, superficie in sectores)


def es_edificio_uso_publico(carga: float) -> bool:
    """Más de 100 personas. Exactamente 100 NO lo es."""
    return carga > UMBRAL_EDIFICIO_USO_PUBLICO