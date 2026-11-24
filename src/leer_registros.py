"""Resume registros_latencia_costo.jsonl: una línea por corrida."""
import json

with open("registros_latencia_costo.jsonl", encoding="utf-8") as f:
    for linea in f:
        r = json.loads(linea)
        t = r["tokens"]
        entrada = t["input_tokens"] if t else None
        etapas = r["tiempos_ms"]
        lenta = max(etapas, key=etapas.get)
        print(
            f"k={r['k']} input_tokens={entrada} total={r['tiempo_total_ms']} ms "
            f"(mas lenta: {lenta}) {r.get('pregunta_huella') or r.get('pregunta', '')[:35]}"
        )
