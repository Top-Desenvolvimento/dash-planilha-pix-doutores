from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, List


ANO_REFERENCIA = 2026

ARQUIVO_PIX = Path("data/pix_doutores.json")
ARQUIVO_SALDOS = Path("data/saldos_doutores.json")
ARQUIVO_RESUMO = Path("data/resumo_pix_doutores.json")
ARQUIVO_ERROS = Path("data/erros_pix_doutores.json")
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


def gerar_meses_ano(ano: int) -> List[str]:
    return [f"{ano}-{mes:02d}" for mes in range(1, 13)]


def obter_competencia_padrao(ano: int, resumos_por_competencia: Dict[str, Any]) -> str:
    hoje = date.today()

    if hoje.year == ano:
        return f"{ano}-{hoje.month:02d}"

    # pega a última competência com algum dado
    competencias_com_dado = []
    for competencia, resumo in (resumos_por_competencia or {}).items():
        if resumo and resumo.get("quantidade_total", 0) > 0:
            competencias_com_dado.append(competencia)

    if competencias_com_dado:
        competencias_com_dado.sort()
        return competencias_com_dado[-1]

    return f"{ano}-01"


def main() -> None:
    registros = carregar_json(ARQUIVO_PIX) or []
    saldos_por_competencia = carregar_json(ARQUIVO_SALDOS) or {}
    resumos_por_competencia = carregar_json(ARQUIVO_RESUMO) or {}
    erros = carregar_json(ARQUIVO_ERROS) or []

    meses_disponiveis = gerar_meses_ano(ANO_REFERENCIA)
    competencia_padrao = obter_competencia_padrao(ANO_REFERENCIA, resumos_por_competencia)

    dashboard = {
        "status": "ok",
        "titulo_dashboard": "Painel Gerencial",
        "arquivo_origem": ARQUIVO_PIX.name,
        "ano_referencia": ANO_REFERENCIA,
        "meses_disponiveis": meses_disponiveis,
        "competencia_padrao": competencia_padrao,
        "registros": registros,
        "erros": erros,
        "resumos_por_competencia": resumos_por_competencia,
        "saldos_por_competencia": saldos_por_competencia,
    }

    salvar_json(dashboard, ARQUIVO_DASH)
    print(f"[OK] Dashboard gerado em: {ARQUIVO_DASH}")


if __name__ == "__main__":
    main()
