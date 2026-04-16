from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

try:
    import requests
except Exception:
    requests = None


ANO_REFERENCIA = 2026
DATA_DIR = Path("data")

ARQUIVO_PIX = DATA_DIR / "pix_doutores.json"
ARQUIVO_ERROS = DATA_DIR / "erros_pix_doutores.json"
ARQUIVO_DASH = DATA_DIR / "dashboard_data.json"
ARQ_DOUTORES_LOCAL = DATA_DIR / "doutores_config_local.json"
ARQ_SALDOS_LOCAL = DATA_DIR / "doutores_saldos_mensais_local.json"

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()


def carregar_json(caminho: Path, padrao: Any) -> Any:
    if not caminho.exists():
        return padrao
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_json(dados: Any, caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def usando_supabase() -> bool:
    return bool(SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY and requests is not None)


def headers_supabase() -> Dict[str, str]:
    return {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def get_supabase(url: str, params: Dict[str, str] | None = None) -> Any:
    resp = requests.get(url, headers=headers_supabase(), params=params or {}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def normalizar_nome(nome: str) -> str:
    texto = str(nome or "").strip().lower()
    texto = (
        texto.replace("á", "a")
        .replace("à", "a")
        .replace("ã", "a")
        .replace("â", "a")
        .replace("é", "e")
        .replace("ê", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ô", "o")
        .replace("õ", "o")
        .replace("ú", "u")
        .replace("ç", "c")
    )
    texto = " ".join(texto.split())

    aliases = {
        "cir.dionathan paim pohlmann": "dionathan pohlmann",
        "cir dionathan paim pohlmann": "dionathan pohlmann",
        "dionathan paim pohlmann": "dionathan pohlmann",
        "cir.dionathan pohlmann": "dionathan pohlmann",
        "cir dionathan pohlmann": "dionathan pohlmann",
        "dionathan pohlmann": "dionathan pohlmann",
        "andriele da silva": "adriele da silva",
        "dra andriele da silva": "adriele da silva",
        "dra adriele da silva": "adriele da silva",
        "adriele da silva": "adriele da silva",
    }

    return aliases.get(texto, texto)


def normalizar_competencia(valor: Any) -> str:
    texto = str(valor or "").strip()
    if not texto:
        return ""

    partes = texto.split("-")
    if len(partes) == 2 and partes[0].isdigit() and partes[1].isdigit():
        return f"{int(partes[0]):04d}-{int(partes[1]):02d}"

    return texto


def extrair_competencia_do_item(item: Dict[str, Any]) -> str:
    competencia = normalizar_competencia(item.get("competencia"))
    if competencia:
        return competencia

    data_item = str(item.get("data") or "").strip()
    if len(data_item) >= 7:
        try:
            ano = int(data_item[6:10]) if "/" in data_item else int(data_item[0:4])
            mes = int(data_item[3:5]) if "/" in data_item else int(data_item[5:7])
            return f"{ano:04d}-{mes:02d}"
        except Exception:
            return ""

    return ""


def gerar_meses_ano(ano: int) -> List[str]:
    hoje = date.today()
    mes_final = hoje.month if hoje.year == ano else 12
    return [f"{ano}-{mes:02d}" for mes in range(1, mes_final + 1)]


def obter_arquivo_mensal(prefixo: str, competencia: str) -> Path:
    return DATA_DIR / f"{prefixo}_{competencia}.json"


def carregar_registros_por_mes(meses: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    resultado: Dict[str, List[Dict[str, Any]]] = {mes: [] for mes in meses}

    registros_gerais = carregar_json(ARQUIVO_PIX, [])
    if isinstance(registros_gerais, list):
        for item in registros_gerais:
            if not isinstance(item, dict):
                continue
            comp = extrair_competencia_do_item(item)
            if comp in resultado:
                registro = dict(item)
                registro["competencia"] = comp
                resultado[comp].append(registro)

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
                    registro["competencia"] = mes
                    saida.append(registro)
                resultado[mes] = saida

    return resultado


def carregar_erros_por_mes(meses: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    resultado: Dict[str, List[Dict[str, Any]]] = {mes: [] for mes in meses}

    erros_gerais = carregar_json(ARQUIVO_ERROS, [])
    if isinstance(erros_gerais, list):
        for item in erros_gerais:
            if not isinstance(item, dict):
                continue
            comp = extrair_competencia_do_item(item)
            if comp in resultado:
                registro = dict(item)
                registro["competencia"] = comp
                resultado[comp].append(registro)

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
                    registro["competencia"] = mes
                    saida.append(registro)
                resultado[mes] = saida

    return resultado


def carregar_doutores_local() -> List[Dict[str, Any]]:
    dados = carregar_json(ARQ_DOUTORES_LOCAL, [])
    if not isinstance(dados, list):
        return []

    saida = []
    for item in dados:
        if not isinstance(item, dict):
            continue
        if item.get("ativo", True) is False:
            continue

        nome = str(item.get("nome") or "").strip()
        if not nome:
            continue

        saida.append({
            "id": item.get("id") or normalizar_nome(nome),
            "nome": nome,
            "nome_normalizado": normalizar_nome(nome),
            "credito": float(item.get("credito") or 0),
            "pix_key": item.get("pix_key") or "",
            "ativo": bool(item.get("ativo", True)),
        })
    return saida


def carregar_doutores_config() -> List[Dict[str, Any]]:
    if not usando_supabase():
        return carregar_doutores_local()

    try:
        url = f"{SUPABASE_URL}/rest/v1/doutores_config"
        params = {
            "select": "id,nome,nome_normalizado,credito,pix_key,ativo",
            "order": "nome.asc",
        }
        data = get_supabase(url, params)
        if not isinstance(data, list):
            return carregar_doutores_local()

        saida = []
        for item in data:
            if item.get("ativo", True) is False:
                continue

            nome = str(item.get("nome") or "").strip()
            if not nome:
                continue

            saida.append({
                "id": item.get("id") or normalizar_nome(nome),
                "nome": nome,
                "nome_normalizado": normalizar_nome(item.get("nome_normalizado") or nome),
                "credito": float(item.get("credito") or 0),
                "pix_key": item.get("pix_key") or "",
                "ativo": bool(item.get("ativo", True)),
            })

        return saida
    except Exception:
        return carregar_doutores_local()


def carregar_saldos_local(competencia: str) -> List[Dict[str, Any]]:
    dados = carregar_json(ARQ_SALDOS_LOCAL, {})
    if not isinstance(dados, dict):
        return []
    itens = dados.get(competencia, [])
    return itens if isinstance(itens, list) else []


def carregar_saldos_mensais(competencia: str) -> List[Dict[str, Any]]:
    if not usando_supabase():
        return carregar_saldos_local(competencia)

    try:
        url = f"{SUPABASE_URL}/rest/v1/doutores_saldos_mensais"
        params = {
            "select": "*",
            "competencia": f"eq.{competencia}",
        }
        data = get_supabase(url, params)
        return data if isinstance(data, list) else carregar_saldos_local(competencia)
    except Exception:
        return carregar_saldos_local(competencia)


def somar_pix_por_doutor(registros: List[Dict[str, Any]]) -> Dict[str, float]:
    totais: Dict[str, float] = {}

    for item in registros:
        if not isinstance(item, dict):
            continue

        nome = normalizar_nome(item.get("doutor_final") or "")
        if not nome:
            continue

        valor = float(item.get("valor") or 0)
        totais[nome] = round(totais.get(nome, 0.0) + valor, 2)

    return totais


def montar_saldos_do_mes(competencia: str, registros_mes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    doutores = carregar_doutores_config()
    saldos_salvos = carregar_saldos_mensais(competencia)
    pix_por_doutor = somar_pix_por_doutor(registros_mes)

    salvos_por_id: Dict[str, Dict[str, Any]] = {}
    for item in saldos_salvos:
        doutor_id = item.get("doutor_id")
        if doutor_id:
            salvos_por_id[str(doutor_id)] = item

    saida: List[Dict[str, Any]] = []

    for doutor in doutores:
        doutor_id = str(doutor.get("id"))
        nome = str(doutor.get("nome") or "").strip()
        nome_norm = normalizar_nome(doutor.get("nome_normalizado") or nome)
        credito_base = float(doutor.get("credito") or 0)

        salvo = salvos_por_id.get(doutor_id, {})

        credito_inicial_salvo = salvo.get("credito_inicial")
        ajuste_manual = float(salvo.get("ajuste_manual") or 0)

        if credito_inicial_salvo is not None and str(credito_inicial_salvo) != "":
            credito_inicial = float(credito_inicial_salvo)
            if credito_inicial < 0 and credito_base > 0:
                credito_inicial = round(credito_base + credito_inicial, 2)
        elif ajuste_manual != 0:
            credito_inicial = round(credito_base + ajuste_manual, 2)
        else:
            credito_inicial = round(credito_base, 2)

        utilizado = round(float(pix_por_doutor.get(nome_norm, 0.0)), 2)
        saldo_final = round(credito_inicial - utilizado, 2)

        saida.append({
            "doutor_id": doutor_id,
            "doutor": nome,
            "credito_inicial": credito_inicial,
            "utilizado": utilizado,
            "credito_disponivel": saldo_final,
            "credito_final": saldo_final,
            "pix_key": doutor.get("pix_key") or "",
        })

    saida.sort(key=lambda x: str(x.get("doutor") or "").lower())
    return saida


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
        "valor_total": valor_total,
        "valor_total_descontado": valor_total_descontado,
        "valor_total_pendente": valor_total_pendente,
        "por_unidade": sorted(por_unidade.values(), key=lambda x: x["unidade"]),
        "por_doutor": sorted(por_doutor.values(), key=lambda x: x["doutor"]),
    }


def achatar_registros_por_mes(registros_por_competencia: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    saida: List[Dict[str, Any]] = []
    for competencia, itens in registros_por_competencia.items():
        for item in itens:
            registro = dict(item)
            registro["competencia"] = competencia
            saida.append(registro)
    return saida


def achatar_erros_por_mes(erros_por_competencia: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    saida: List[Dict[str, Any]] = []
    for competencia, itens in erros_por_competencia.items():
        for item in itens:
            registro = dict(item)
            registro["competencia"] = competencia
            saida.append(registro)
    return saida


def obter_competencia_padrao(
    ano: int,
    registros_por_competencia: Dict[str, List[Dict[str, Any]]],
    saldos_por_competencia: Dict[str, List[Dict[str, Any]]],
) -> str:
    hoje = date.today()
    atual = f"{ano}-{hoje.month:02d}"

    if hoje.year == ano and (registros_por_competencia.get(atual) or saldos_por_competencia.get(atual)):
        return atual

    meses_com_dado = []
    for mes in sorted(registros_por_competencia.keys()):
        if registros_por_competencia.get(mes) or saldos_por_competencia.get(mes):
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
        saldos_por_competencia[mes] = montar_saldos_do_mes(mes, registros_mes)
        resumos_por_competencia[mes] = montar_resumo_do_mes(mes, registros_mes)

    registros = achatar_registros_por_mes(registros_por_competencia)
    erros = achatar_erros_por_mes(erros_por_competencia)

    competencia_padrao = obter_competencia_padrao(
        ANO_REFERENCIA,
        registros_por_competencia,
        saldos_por_competencia,
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


if __name__ == "__main__":
    main()
