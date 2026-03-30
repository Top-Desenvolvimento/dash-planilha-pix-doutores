import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

ARQUIVO_PIX = DATA_DIR / "pix_doutores.json"
ARQUIVO_CREDITOS = DATA_DIR / "doutores_credito.json"
ARQUIVO_SAIDA = DATA_DIR / "dashboard_data.json"


def carregar_json(caminho: Path):
    if not caminho.exists():
        return None

    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    pix = carregar_json(ARQUIVO_PIX)
    creditos = carregar_json(ARQUIVO_CREDITOS)

    if pix is None:
        raise FileNotFoundError(f"Arquivo não encontrado: {ARQUIVO_PIX}")

    if creditos is None:
        raise FileNotFoundError(f"Arquivo não encontrado: {ARQUIVO_CREDITOS}")

    ativos = [d for d in creditos if d.get("ativo", True)]

    dashboard_data = {
        "periodo": pix.get("periodo", {}),
        "resumo": pix.get("resumo", {}),
        "totais_pix_por_doutor": pix.get("totais_pix_por_doutor", {}),
        "saldos_ajustados": pix.get("saldos_ajustados", {}),
        "nao_mapeados": pix.get("nao_mapeados", []),
        "lancamentos": pix.get("lancamentos", []),
        "doutores_ativos": ativos
    }

    with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f:
        json.dump(dashboard_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Arquivo gerado com sucesso: {ARQUIVO_SAIDA}")


if __name__ == "__main__":
    main()
