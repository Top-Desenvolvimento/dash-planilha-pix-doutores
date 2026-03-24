import json
from pathlib import Path

base_dir = Path(__file__).resolve().parents[1]
data_dir = base_dir / "data"
data_dir.mkdir(exist_ok=True)

saida = data_dir / "pix_doutores.json"

with open(saida, "w", encoding="utf-8") as f:
    json.dump([], f, ensure_ascii=False, indent=2)

print("Arquivo pix_doutores.json gerado com sucesso.")
