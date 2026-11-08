import json

with open("resultados_metricas.json",  encoding="utf-8") as archivo:
    resultados = json.load(archivo)

ordenados = sorted(resultados, key=lambda r: r["f1"]) 
muestra = ordenados[:5] + ordenados[-5:] # Los 5 mejores y los 5 peores

for n, caso in enumerate(muestra, start=1):
    print(f"\n===== Caso {n} | f1= {caso['f1']:.2f} "
          f"precision= {caso['precision']:.2f} cobertura= {caso['cobertura']:.2f}")
    print("CONSULTA: ", caso["consulta"])  
    print("REFERENCIA: ", caso["referencia"])
    print("RESPUESTA: ", caso["respuesta"])     

    