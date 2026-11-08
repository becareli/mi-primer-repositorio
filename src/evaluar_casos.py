import json
from cliente import consultar_modelo
from metricas import calcular_metricas, resumir_metricas
from casos import CASOS

ARCHIVO = "resultados_metricas.json"

if __name__ == "__main__":
    resultados = []
    for i, (consulta, referencia) in enumerate(CASOS, start=1):
        respuesta = consultar_modelo(consulta + " Responde en maximo 3 lineas")
        metricas = calcular_metricas(referencia, respuesta)
        resultados.append(
            {"consulta": consulta, "referencia": referencia, "respuesta": respuesta, **metricas}
        )
        # Se guarda en cada vuelta: si algo falla a mitad, no se pierde lo ya hecho. 
        with open(ARCHIVO, "w", encoding="utf-8") as archivo:
            json.dump(resultados, archivo, ensure_ascii=False, indent=2)
        print(f"[{i}/{len(CASOS)}] f1= {metricas['f1']:.2f} - {consulta}.")    

resumen = resumir_metricas(resultados)
print({clave: round(valor, 3) for clave, valor in resumen.items()})


