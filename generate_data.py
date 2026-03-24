import pandas as pd
import json
from datetime import datetime

# =========================
# CONFIG
# =========================

ARQUIVO_EXCEL = "entrada.xlsx"
ABA = 0  # ou nome da aba

# =========================
# LEITURA
# =========================

df = pd.read_excel(ARQUIVO_EXCEL, sheet_name=ABA)

# Ajuste os nomes conforme seu Excel
df.columns = [c.strip() for c in df.columns]

# =========================
# TRATAMENTO
# =========================

def extrair_doutor(texto):
    if pd.isna(texto):
        return "Desconhecido"

    texto = str(texto)

    # Ajuste aqui conforme padrão real
    if "Dr." in texto:
        return texto.strip()

    return texto.strip()

dados = []

for _, row in df.iterrows():
    try:
        data = pd.to_datetime(row["Data"])
        valor = float(row["Valor"])

        doutor = extrair_doutor(row["Mét. Pag."])

        dados.append({
            "data": data.strftime("%Y-%m-%d"),
            "unidade": row.get("Unidade", "Não informado"),
            "doutor": doutor,
            "metodo": row.get("Mét. Pag.", ""),
            "origem": row.get("Origem", ""),
            "valor": valor,
            "mes": data.month,
            "ano": data.year
        })

    except Exception as e:
        print("Erro na linha:", e)

# =========================
# SALVAR JSON
# =========================

with open("data/pix_doutores.json", "w", encoding="utf-8") as f:
    json.dump(dados, f, ensure_ascii=False, indent=2)

print("✅ JSON gerado com sucesso!")
