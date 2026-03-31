from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


ARQUIVO_PIX = Path("data/pix_doutores.json")
ARQUIVO_SALDOS = Path("data/saldos_doutores.json")
ARQUIVO_RESUMO = Path("data/resumo_pix_doutores.json")
ARQUIVO_DASH = Path("data/dashboard_data.json")


def carregar_json(caminho: Path) -> Any:
    if not caminho.exists():
        return None

    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_json(dados: Any, caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def main() -> None:
    pix = carregar_json(ARQUIVO_PIX) or []
    saldos = carregar_json(ARQUIVO_SALDOS) or []
    resumo = carregar_json(ARQUIVO_RESUMO) or {}

    registros_validos: List[Dict[str, Any]] = [r for r in pix if "erro" not in r]
    erros: List[Dict[str, Any]] = [r for r in pix if "erro" in r]

    dashboard = {
        "status": "ok",
        "arquivo_origem": ARQUIVO_PIX.name,
        "titulo_dashboard": "Dashboard PIX Doutores",
        "resumo": resumo,
        "totais": {
            "linhas_validas": len(registros_validos),
            "linhas_com_erro": len(erros),
        },
        "registros": registros_validos,
        "erros": erros,
        "saldos_doutores": saldos,
    }

    salvar_json(dashboard, ARQUIVO_DASH)
    print(f"[OK] Dashboard gerado em: {ARQUIVO_DASH}")


if __name__ == "__main__":
    main()
