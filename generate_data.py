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


def carregar_json(caminho: Path, padrao: Any) -> Any:
    if not caminho.exists():
        return padrao
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_json(dados: Any, caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def gerar_meses_ano(ano: int) -> List[str]:
    return [f"{ano}-{mes:02d}" for mes in range(1, 13)]


def normalizar_competencia(valor: str | None) -> str:
    valor = str(valor or "").strip()
    if not valor:
        return ""

    partes = valor.split("-")
    if len(partes) == 2 and partes[0].isdigit() and partes[1].isdigit():
        return f"{int(partes[0]):04d}-{int(partes[1]):02d}"

    return valor


def agrupar_por_competencia(registros: List[Dict[str, Any]], meses_disponiveis: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    agrupado = {mes: [] for mes in meses_disponiveis}

    for item in registros:
        competencia = normalizar_competencia(item.get("competencia"))
        if competencia in agrupado:
            agrupado[competencia].append(item)

    return agrupado


def normalizar_dict_por_competencia(valor: Any, meses_disponiveis: List[str], padrao_valor: Any) -> Dict[str, Any]:
    saida = {mes: (padrao_valor() if callable(padrao_valor) else padrao_valor) for mes in meses_disponiveis}

    if isinstance(valor, dict):
        for competencia, conteudo in valor.items():
            chave = normalizar_competencia(competencia)
            if chave in saida:
                saida[chave] = conteudo
    return saida


def obter_competencia_padrao(ano: int, registros_por_competencia: Dict[str, List[Dict[str, Any]]]) -> str:
    hoje = date.today()
    atual = f"{ano}-{hoje.month:02d}"

    if hoje.year == ano and registros_por_competencia.get(atual):
        return atual

    meses_com_dado = sorted([mes for mes, itens in registros_por_competencia.items() if itens])
    if meses_com_dado:
        return meses_com_dado[-1]

    if hoje.year == ano:
        return atual

    return f"{ano}-12"


def main() -> None:
    registros = carregar_json(ARQUIVO_PIX, [])
    saldos_brutos = carregar_json(ARQUIVO_SALDOS, {})
    resumos_brutos = carregar_json(ARQUIVO_RESUMO, {})
    erros = carregar_json(ARQUIVO_ERROS, [])

    if not isinstance(registros, list):
        registros = []
    if not isinstance(erros, list):
        erros = []

    meses_disponiveis = gerar_meses_ano(ANO_REFERENCIA)

    registros_por_competencia = agrupar_por_competencia(registros, meses_disponiveis)
    erros_por_competencia = agrupar_por_competencia(erros, meses_disponiveis)

    saldos_por_competencia = normalizar_dict_por_competencia(saldos_brutos, meses_disponiveis, list)
    resumos_por_competencia = normalizar_dict_por_competencia(resumos_brutos, meses_disponiveis, dict)

    for mes in meses_disponiveis:
        resumos_por_competencia.setdefault(mes, {
            "competencia": mes,
            "gerado_em": None,
            "quantidade_total": 0,
            "valor_total": 0,
            "valor_total_descontado": 0,
            "valor_total_pendente": 0,
            "por_unidade": [],
            "por_doutor": [],
        })
        saldos_por_competencia.setdefault(mes, [])

    competencia_padrao = obter_competencia_padrao(ANO_REFERENCIA, registros_por_competencia)

    dashboard = {
        "status": "ok",
        "titulo_dashboard": "Painel Gerencial",
        "arquivo_origem": ARQUIVO_PIX.name,
        "ano_referencia": ANO_REFERENCIA,
        "meses_disponiveis": meses_disponiveis,
        "competencia_padrao": competencia_padrao,
        "registros": registros,
        "erros": erros,
        "registros_por_competencia": registros_por_competencia,
        "erros_por_competencia": erros_por_competencia,
        "resumos_por_competencia": resumos_por_competencia,
        "saldos_por_competencia": saldos_por_competencia,
    }

    salvar_json(dashboard, ARQUIVO_DASH)
    print(f"[OK] Dashboard gerado em: {ARQUIVO_DASH}")


if __name__ == "__main__":
    main()
