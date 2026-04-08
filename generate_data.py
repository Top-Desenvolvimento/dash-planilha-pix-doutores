from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

from regras_doutores import carregar_doutores_config, normalizar_nome


ANO_REFERENCIA = 2026

DATA_DIR = Path("data")

ARQUIVO_PIX = DATA_DIR / "pix_doutores.json"
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


def extrair_competencia_do_item(item: Dict[str, Any]) -> str:
    if not isinstance(item, dict):
        return ""

    competencia = normalizar_competencia(item.get("competencia"))
    if competencia:
        return competencia

    data_item = str(item.get("data") or "").strip()
    if len(data_item) >= 7:
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
            registro = dict(item)
            if not registro.get("competencia"):
                registro["competencia"] = competencia
            agrupado[competencia].append(registro)

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
                saida = []
                for item in conteudo:
                    if not isinstance(item, dict):
                        continue
                    registro = dict(item)
                    if not registro.get("competencia"):
                        registro["competencia"] = mes
                    saida.append(registro)
                resultado[mes] = saida

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
                saida = []
                for item in conteudo:
                    if not isinstance(item, dict):
                        continue
                    registro = dict(item)
                    if not registro.get("competencia"):
                        registro["competencia"] = mes
                    saida.append(registro)
                resultado[mes] = saida

    return resultado


def somar_pix_por_doutor(registros: List[Dict[str, Any]]) -> Dict[str, float]:
    totais: Dict[str, float] = {}

    for item in registros:
        if not isinstance(item, dict):
            continue

        nome_doutor = item.get("doutor_final") or ""
        nome_norm = normalizar_nome(nome_doutor)
        if not nome_norm:
            continue

        # regra do mês: soma o PIX do mês
        valor = float(item.get("valor", 0) or 0)

        totais[nome_norm] = round(totais.get(nome_norm, 0.0) + valor, 2)

    return totais


def montar_saldos_do_mes(registros_mes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    doutores = carregar_doutores_config()
    totais_pix = somar_pix_por_doutor(registros_mes)

    saldos: List[Dict[str, Any]] = []

    for doutor in doutores:
        nome_norm = doutor.get("nome_normalizado") or normalizar_nome(doutor.get("nome"))
        credito_inicial = round(float(doutor.get("credito") or 0), 2)
        utilizado = round(float(totais_pix.get(nome_norm, 0.0)), 2)
        credito_disponivel = round(max(0.0, credito_inicial - utilizado), 2)

        saldos.append({
            "doutor_id": doutor.get("id"),
            "doutor": doutor.get("nome"),
            "credito_inicial": credito_inicial,
            "utilizado": utilizado,
            "credito_disponivel": credito_disponivel,
            "pix_key": doutor.get("pix_key", ""),
        })

    saldos.sort(key=lambda x: str(x.get("doutor") or "").lower())
    return saldos


def montar_resumo_do_mes(competencia: str, registros_mes: List[Dict[str, Any]]) -> Dict[str, Any]:
    quantidade_total = len(registros_mes)
    valor_total = round(sum(float(item.get("valor", 0) or 0) for item in registros_mes), 2)
    valor_total_descontado = round(sum(float(item.get("valor_descontado", 0) or 0) for item in registros_mes), 2)
    valor_total_pendente = round(sum(float(item.get("pendente", 0) or 0) for item in registros_mes), 2)

    por_unidade: Dict[str, Dict[str, Any]] = {}
    por_doutor: Dict[str, Dict[str, Any]] = {}

    for item in registros_mes:
        unidade = str(item.get("unidade") or "Não informado")
        doutor = str(item.get("doutor_final") or "Sem responsável fiscal")

        valor = float(item.get("valor", 0) or 0)
        descontado = float(item.get("valor_descontado", 0) or 0)
        pendente = float(item.get("pendente", 0) or 0)

        if unidade not in por_unidade:
            por_unidade[unidade] = {
                "unidade": unidade,
                "quantidade": 0,
                "valor": 0.0,
                "descontado": 0.0,
                "pendente": 0.0,
            }

        por_unidade[unidade]["quantidade"] += 1
        por_unidade[unidade]["valor"] += valor
        por_unidade[unidade]["descontado"] += descontado
        por_unidade[unidade]["pendente"] += pendente

        if doutor not in por_doutor:
            por_doutor[doutor] = {
                "doutor": doutor,
                "quantidade": 0,
                "valor": 0.0,
                "descontado": 0.0,
                "pendente": 0.0,
            }

        por_doutor[doutor]["quantidade"] += 1
        por_doutor[doutor]["valor"] += valor
        por_doutor[doutor]["descontado"] += descontado
        por_doutor[doutor]["pendente"] += pendente

    return {
        "competencia": competencia,
        "quantidade_total": quantidade_total,
        "valor_total": round(valor_total, 2),
        "valor_total_descontado": round(valor_total_descontado, 2),
        "valor_total_pendente": round(valor_total_pendente, 2),
        "por_unidade": sorted(por_unidade.values(), key=lambda x: x["unidade"]),
        "por_doutor": sorted(por_doutor.values(), key=lambda x: x["doutor"]),
    }


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

    saldos_por_competencia: Dict[str, List[Dict[str, Any]]] = {}
    resumos_por_competencia: Dict[str, Dict[str, Any]] = {}

    for mes in meses_disponiveis:
        registros_mes = registros_por_competencia.get(mes, [])
        saldos_por_competencia[mes] = montar_saldos_do_mes(registros_mes)
        resumos_por_competencia[mes] = montar_resumo_do_mes(mes, registros_mes)

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

    for mes in meses_disponiveis:
        qtd_registros = len(registros_por_competencia.get(mes, []))
        qtd_saldos = len(saldos_por_competencia.get(mes, []))
        print(f"[OK] {mes} -> registros={qtd_registros}, saldos={qtd_saldos}")


if __name__ == "__main__":
    main()
