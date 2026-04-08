from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, List


ANO_REFERENCIA = 2026

DATA_DIR = Path("data")

ARQUIVO_PIX = DATA_DIR / "pix_doutores.json"
ARQUIVO_SALDOS = DATA_DIR / "saldos_doutores.json"
ARQUIVO_RESUMO = DATA_DIR / "resumo_pix_doutores.json"
ARQUIVO_ERROS = DATA_DIR / "erros_pix_doutores.json"
ARQUIVO_DASH = DATA_DIR / "dashboard_data.json"


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
    hoje = date.today()
    mes_final = hoje.month if hoje.year == ano else 12
    return [f"{ano}-{mes:02d}" for mes in range(1, mes_final + 1)]


def normalizar_competencia(valor: Any) -> str:
    texto = str(valor or "").strip()
    if not texto:
        return ""

    partes = texto.split("-")
    if len(partes) == 2 and partes[0].isdigit() and partes[1].isdigit():
        return f"{int(partes[0]):04d}-{int(partes[1]):02d}"

    return texto


def garantir_lista(valor: Any) -> List[Any]:
    if isinstance(valor, list):
        return valor
    return []


def garantir_dict(valor: Any) -> Dict[str, Any]:
    if isinstance(valor, dict):
        return valor
    return {}


def extrair_competencia_do_item(item: Dict[str, Any]) -> str:
    if not isinstance(item, dict):
        return ""

    competencia = normalizar_competencia(item.get("competencia"))
    if competencia:
        return competencia

    data_item = str(item.get("data") or "").strip()
    if len(data_item) >= 7 and data_item[4] == "-" and data_item[7:8] in {"", "-"}:
        try:
            ano = int(data_item[0:4])
            mes = int(data_item[5:7])
            return f"{ano:04d}-{mes:02d}"
        except Exception:
            return ""

    return ""


def agrupar_por_competencia(registros: List[Dict[str, Any]], meses: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    agrupado = {mes: [] for mes in meses}

    for item in registros:
        if not isinstance(item, dict):
            continue

        competencia = extrair_competencia_do_item(item)
        if competencia in agrupado:
            agrupado[competencia].append(item)

    return agrupado


def obter_arquivo_mensal(prefixo: str, competencia: str) -> Path:
    return DATA_DIR / f"{prefixo}_{competencia}.json"


def carregar_registros_por_mes(meses: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    resultado: Dict[str, List[Dict[str, Any]]] = {mes: [] for mes in meses}

    registros_gerais = carregar_json(ARQUIVO_PIX, [])
    if isinstance(registros_gerais, list) and registros_gerais:
        agrupado = agrupar_por_competencia(registros_gerais, meses)
        for mes in meses:
            resultado[mes] = agrupado.get(mes, [])

    for mes in meses:
        arquivo_mensal = obter_arquivo_mensal("pix_doutores", mes)
        if arquivo_mensal.exists():
            conteudo = carregar_json(arquivo_mensal, [])
            if isinstance(conteudo, list):
                resultado[mes] = conteudo

    return resultado


def carregar_erros_por_mes(meses: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    resultado: Dict[str, List[Dict[str, Any]]] = {mes: [] for mes in meses}

    erros_gerais = carregar_json(ARQUIVO_ERROS, [])
    if isinstance(erros_gerais, list) and erros_gerais:
        agrupado = agrupar_por_competencia(erros_gerais, meses)
        for mes in meses:
            resultado[mes] = agrupado.get(mes, [])

    for mes in meses:
        arquivo_mensal = obter_arquivo_mensal("erros_pix_doutores", mes)
        if arquivo_mensal.exists():
            conteudo = carregar_json(arquivo_mensal, [])
            if isinstance(conteudo, list):
                resultado[mes] = conteudo

    return resultado


def carregar_saldos_por_mes(meses: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    resultado: Dict[str, List[Dict[str, Any]]] = {mes: [] for mes in meses}

    saldos_gerais = carregar_json(ARQUIVO_SALDOS, {})
    if isinstance(saldos_gerais, dict):
        for chave, conteudo in saldos_gerais.items():
            competencia = normalizar_competencia(chave)
            if competencia in resultado and isinstance(conteudo, list):
                resultado[competencia] = conteudo
    elif isinstance(saldos_gerais, list):
        # caso raro: arquivo genérico seja uma lista única de um mês
        # nesse caso deixamos como fallback só no mês atual/default depois
        pass

    for mes in meses:
        arquivo_mensal = obter_arquivo_mensal("saldos_doutores", mes)
        if arquivo_mensal.exists():
            conteudo = carregar_json(arquivo_mensal, [])
            if isinstance(conteudo, list):
                resultado[mes] = conteudo

    return resultado


def carregar_resumos_por_mes(meses: List[str]) -> Dict[str, Dict[str, Any]]:
    resultado: Dict[str, Dict[str, Any]] = {mes: {} for mes in meses}

    resumos_gerais = carregar_json(ARQUIVO_RESUMO, {})
    if isinstance(resumos_gerais, dict):
        # se já for dict por competência
        for chave, conteudo in resumos_gerais.items():
            competencia = normalizar_competencia(chave)
            if competencia in resultado and isinstance(conteudo, dict):
                resultado[competencia] = conteudo

        # se o arquivo genérico for um resumo único do mês atual
        competencia_unica = normalizar_competencia(resumos_gerais.get("competencia"))
        if competencia_unica in resultado and "quantidade_total" in resumos_gerais:
            resultado[competencia_unica] = resumos_gerais

    for mes in meses:
        arquivo_mensal = obter_arquivo_mensal("resumo_pix_doutores", mes)
        if arquivo_mensal.exists():
            conteudo = carregar_json(arquivo_mensal, {})
            if isinstance(conteudo, dict):
                resultado[mes] = conteudo

    return resultado


def achatar_registros_por_mes(registros_por_competencia: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    saida: List[Dict[str, Any]] = []

    for competencia, itens in registros_por_competencia.items():
        for item in itens:
            if not isinstance(item, dict):
                continue

            registro = dict(item)
            if not registro.get("competencia"):
                registro["competencia"] = competencia
            saida.append(registro)

    return saida


def achatar_erros_por_mes(erros_por_competencia: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    saida: List[Dict[str, Any]] = []

    for competencia, itens in erros_por_competencia.items():
        for item in itens:
            if not isinstance(item, dict):
                continue

            registro = dict(item)
            if not registro.get("competencia"):
                registro["competencia"] = competencia
            saida.append(registro)

    return saida


def obter_competencia_padrao(
    ano: int,
    registros_por_competencia: Dict[str, List[Dict[str, Any]]],
    saldos_por_competencia: Dict[str, List[Dict[str, Any]]],
    resumos_por_competencia: Dict[str, Dict[str, Any]],
) -> str:
    hoje = date.today()
    atual = f"{ano}-{hoje.month:02d}"

    if hoje.year == ano:
        if registros_por_competencia.get(atual):
            return atual
        if saldos_por_competencia.get(atual):
            return atual
        if resumos_por_competencia.get(atual):
            return atual

    meses_com_dado = []
    for mes in sorted(registros_por_competencia.keys()):
        if registros_por_competencia.get(mes) or saldos_por_competencia.get(mes) or resumos_por_competencia.get(mes):
            meses_com_dado.append(mes)

    if meses_com_dado:
        return meses_com_dado[-1]

    return atual if hoje.year == ano else f"{ano}-12"


def main() -> None:
    meses_disponiveis = gerar_meses_ano(ANO_REFERENCIA)

    registros_por_competencia = carregar_registros_por_mes(meses_disponiveis)
    erros_por_competencia = carregar_erros_por_mes(meses_disponiveis)
    saldos_por_competencia = carregar_saldos_por_mes(meses_disponiveis)
    resumos_por_competencia = carregar_resumos_por_mes(meses_disponiveis)

    registros = achatar_registros_por_mes(registros_por_competencia)
    erros = achatar_erros_por_mes(erros_por_competencia)

    competencia_padrao = obter_competencia_padrao(
        ANO_REFERENCIA,
        registros_por_competencia,
        saldos_por_competencia,
        resumos_por_competencia,
    )

    dashboard = {
        "status": "ok",
        "titulo_dashboard": "PIX Doutores",
        "arquivo_origem": ARQUIVO_PIX.name,
        "ano_referencia": ANO_REFERENCIA,
        "meses_disponiveis": meses_disponiveis,
        "competencia_padrao": competencia_padrao,
        "registros": registros,
        "erros": erros,
        "registros_por_competencia": registros_por_competencia,
        "erros_por_competencia": erros_por_competencia,
        "saldos_por_competencia": saldos_por_competencia,
        "resumos_por_competencia": resumos_por_competencia,
    }

    salvar_json(dashboard, ARQUIVO_DASH)

    print(f"[OK] Dashboard gerado em: {ARQUIVO_DASH}")
    print(f"[OK] Competência padrão: {competencia_padrao}")
    print(f"[OK] Meses disponíveis: {', '.join(meses_disponiveis)}")

    for mes in meses_disponiveis:
        qtd_registros = len(registros_por_competencia.get(mes, []))
        qtd_erros = len(erros_por_competencia.get(mes, []))
        qtd_saldos = len(saldos_por_competencia.get(mes, []))
        tem_resumo = bool(resumos_por_competencia.get(mes))

        print(
            f"[OK] {mes} -> "
            f"registros={qtd_registros}, "
            f"erros={qtd_erros}, "
            f"saldos={qtd_saldos}, "
            f"resumo={'sim' if tem_resumo else 'nao'}"
        )


if __name__ == "__main__":
    main()
