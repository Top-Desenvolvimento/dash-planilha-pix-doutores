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


def normalizar_competencia(valor: str | None) -> str:
    valor = str(valor or "").strip()

    if not valor:
        return ""

    partes = valor.split("-")
    if len(partes) == 2:
        ano, mes = partes
        if ano.isdigit() and mes.isdigit():
            return f"{int(ano):04d}-{int(mes):02d}"

    return valor


def agrupar_por_competencia(registros: List[Dict[str, Any]], meses_disponiveis: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    agrupado: Dict[str, List[Dict[str, Any]]] = {mes: [] for mes in meses_disponiveis}

    for item in registros:
        competencia = normalizar_competencia(item.get("competencia"))
        if competencia in agrupado:
            agrupado[competencia].append(item)

    return agrupado


def normalizar_resumos_por_competencia(
    resumos_brutos: Any,
    meses_disponiveis: List[str]
) -> Dict[str, Dict[str, Any]]:
    saida: Dict[str, Dict[str, Any]] = {mes: {} for mes in meses_disponiveis}

    if isinstance(resumos_brutos, dict):
        for competencia, resumo in resumos_brutos.items():
            chave = normalizar_competencia(competencia)
            if chave in saida:
                saida[chave] = resumo or {}

    elif isinstance(resumos_brutos, list):
        # formato antigo não tem resumo por competência
        # mantém vazio e a tela calcula pelo registro
        pass

    return saida


def normalizar_saldos_por_competencia(
    saldos_brutos: Any,
    meses_disponiveis: List[str],
    competencia_padrao_fallback: str
) -> Dict[str, List[Dict[str, Any]]]:
    saida: Dict[str, List[Dict[str, Any]]] = {mes: [] for mes in meses_disponiveis}

    if isinstance(saldos_brutos, dict):
        for competencia, saldos in saldos_brutos.items():
            chave = normalizar_competencia(competencia)
            if chave in saida and isinstance(saldos, list):
                saida[chave] = saldos

    elif isinstance(saldos_brutos, list):
        # formato antigo: uma lista única de saldos
        # joga no mês padrão/fallback para não quebrar a dashboard
        if competencia_padrao_fallback in saida:
            saida[competencia_padrao_fallback] = saldos_brutos

    return saida


def obter_competencia_padrao(
    ano: int,
    meses_disponiveis: List[str],
    registros_por_competencia: Dict[str, List[Dict[str, Any]]]
) -> str:
    hoje = date.today()
    competencia_atual = f"{ano}-{hoje.month:02d}"

    if hoje.year == ano and competencia_atual in meses_disponiveis:
        if registros_por_competencia.get(competencia_atual):
            return competencia_atual

    meses_com_dados = [
        mes for mes in meses_disponiveis
        if registros_por_competencia.get(mes)
    ]

    if meses_com_dados:
        return meses_com_dados[-1]

    if hoje.year == ano and competencia_atual in meses_disponiveis:
        return competencia_atual

    return meses_disponiveis[0]


def main() -> None:
    registros = carregar_json(ARQUIVO_PIX) or []
    saldos_brutos = carregar_json(ARQUIVO_SALDOS) or {}
    resumos_brutos = carregar_json(ARQUIVO_RESUMO) or {}
    erros = carregar_json(ARQUIVO_ERROS) or []

    meses_disponiveis = gerar_meses_ano(ANO_REFERENCIA)

    registros_por_competencia = agrupar_por_competencia(registros, meses_disponiveis)
    erros_por_competencia = agrupar_por_competencia(erros, meses_disponiveis)

    competencia_padrao = obter_competencia_padrao(
        ANO_REFERENCIA,
        meses_disponiveis,
        registros_por_competencia
    )

    resumos_por_competencia = normalizar_resumos_por_competencia(
        resumos_brutos,
        meses_disponiveis
    )

    saldos_por_competencia = normalizar_saldos_por_competencia(
        saldos_brutos,
        meses_disponiveis,
        competencia_padrao
    )

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
