import json
from pathlib import Path

DATA_DIR = Path("data")

pix = json.load(open(DATA_DIR / "pix_doutores.json", encoding="utf-8"))
creditos = json.load(open(DATA_DIR / "doutores_credito.json", encoding="utf-8"))

totais = {}

for r in pix:
    doutor = r["doutor"]
    if not doutor:
        continue

    totais[doutor] = totais.get(doutor, 0) + r["valor"]

resultado = {}

for c in creditos:
    doutor = c["doutor"]
    credito = c["credito"]
    total = totais.get(doutor, 0)

    resultado[doutor] = {
        "credito": credito,
        "pix_mes": total,
        "saldo": credito - total
    }

json.dump(resultado, open(DATA_DIR / "dashboard_data.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)

print("✅ Dashboard gerado")
