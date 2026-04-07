from __future__ import annotations

import os
import unicodedata
from typing import Dict, List, Any, Optional

import requests


SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()


def normalizar_nome(nome: str) -> str:
    nome = (nome or "").strip().lower()
    nome = unicodedata.normalize("NFKD", nome)
    nome = "".join(c for c in nome if not unicodedata.combining(c))
    nome = " ".join(nome.split())
    return nome


def headers_supabase() -> Dict[str, str]:
    return {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def get_supabase(url: str, params: Optional[Dict[str, str]] = None) -> Any:
    resp = requests.get(url, headers=headers_supabase(), params=params or {}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def upsert_supabase(url: str, payload: List[Dict[str, Any]], on_conflict: str) -> Any:
    headers = headers_supabase()
    headers["Prefer"] = "resolution=merge-duplicates,return=representation"

    resp = requests.post(
        url,
        headers=headers,
        params={"on_conflict": on_conflict},
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def patch_supabase(url: str, payload: Dict[str, Any], params: Dict[str, str]) -> Any:
    resp = requests.patch(url, headers=headers_supabase(), params=params, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def carregar_doutores_config() -> List[Dict[str, Any]]:
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY não configurados.")

    url = f"{SUPABASE_URL}/rest/v1/doutores_config"
    params = {
        "select": "id,nome,nome_normalizado,credito,pix_key,ativo",
        "order": "nome.asc",
    }
    data = get_supabase(url, params)

    if not isinstance(data, list):
        return []

    saida = []
    for item in data:
        if not item.get("ativo", True):
            continue

        saida.append({
            "id": item["id"],
            "nome": item["nome"],
            "nome_normalizado": item.get("nome_normalizado") or normalizar_nome(item["nome"]),
            "credito": float(item.get("credito") or 0),
            "pix_key": item.get("pix_key") or "",
            "ativo": bool(item.get("ativo", True)),
        })

    return saida


def carregar_saldos_mensais(competencia: str) -> List[Dict[str, Any]]:
    url = f"{SUPABASE_URL}/rest/v1/doutores_saldos_mensais"
    params = {
        "select": "id,competencia,doutor_id,credito_inicial,utilizado,credito_final,ajuste_manual,observacao",
        "competencia": f"eq.{competencia}",
    }
    data = get_supabase(url, params)
    return data if isinstance(data, list) else []


def inicializar_saldos_competencia(competencia: str, competencia_anterior: Optional[str]) -> List[Dict[str, Any]]:
    doutores = carregar_doutores_config()
    saldos_atuais = carregar_saldos_mensais(competencia)

    if saldos_atuais:
        return saldos_atuais

    saldo_anterior_por_doutor: Dict[str, Dict[str, Any]] = {}
    if competencia_anterior:
        for item in carregar_saldos_mensais(competencia_anterior):
            saldo_anterior_por_doutor[item["doutor_id"]] = item

    payload = []
    for doutor in doutores:
        anterior = saldo_anterior_por_doutor.get(doutor["id"])
        credito_inicial = float(doutor["credito"] or 0)

        if anterior:
            credito_inicial = float(anterior.get("credito_final") or 0)

        payload.append({
            "competencia": competencia,
            "doutor_id": doutor["id"],
            "credito_inicial": round(credito_inicial, 2),
            "utilizado": 0,
            "credito_final": round(credito_inicial, 2),
            "ajuste_manual": 0,
            "observacao": None,
        })

    if not payload:
        return []

    url = f"{SUPABASE_URL}/rest/v1/doutores_saldos_mensais"
    return upsert_supabase(url, payload, "competencia,doutor_id")


def montar_mapa_creditos(competencia: str, competencia_anterior: Optional[str]) -> Dict[str, Dict[str, Any]]:
    doutores = carregar_doutores_config()
    saldos = inicializar_saldos_competencia(competencia, competencia_anterior)

    saldos_por_doutor: Dict[str, Dict[str, Any]] = {
        item["doutor_id"]: item for item in saldos
    }

    mapa: Dict[str, Dict[str, Any]] = {}

    for doutor in doutores:
        saldo = saldos_por_doutor.get(doutor["id"])
        credito_inicial = float(doutor["credito"] or 0)
        utilizado = 0.0
        credito_final = credito_inicial

        if saldo:
            credito_inicial = float(saldo.get("credito_inicial") or 0)
            utilizado = float(saldo.get("utilizado") or 0)
            credito_final = float(saldo.get("credito_final") or 0)

        mapa[doutor["nome_normalizado"]] = {
            "id": doutor["id"],
            "nome_original": doutor["nome"],
            "nome_normalizado": doutor["nome_normalizado"],
            "credito_inicial": round(credito_inicial, 2),
            "utilizado": round(utilizado, 2),
            "credito_disponivel": round(credito_final, 2),
            "pix_key": doutor.get("pix_key", ""),
        }

    return mapa


def aplicar_desconto(
    mapa_creditos: Dict[str, Dict[str, Any]],
    nome_doutor: str,
    valor: float
) -> Dict[str, Any]:
    chave = normalizar_nome(nome_doutor)
    valor = round(float(valor), 2)

    if chave not in mapa_creditos:
        return {
            "doutor_encontrado": False,
            "doutor_id": None,
            "nome_padronizado": nome_doutor,
            "credito_antes": 0.0,
            "valor_descontado": 0.0,
            "credito_depois": 0.0,
            "utilizado_depois": 0.0,
            "pendente": valor,
        }

    item = mapa_creditos[chave]
    credito_antes = round(float(item["credito_disponivel"]), 2)
    utilizado_antes = round(float(item["utilizado"]), 2)

    valor_descontado = round(min(valor, credito_antes), 2)
    credito_depois = round(credito_antes - valor_descontado, 2)
    utilizado_depois = round(utilizado_antes + valor_descontado, 2)
    pendente = round(valor - valor_descontado, 2)

    item["credito_disponivel"] = credito_depois
    item["utilizado"] = utilizado_depois

    return {
        "doutor_encontrado": True,
        "doutor_id": item["id"],
        "nome_padronizado": item["nome_original"],
        "credito_antes": credito_antes,
        "valor_descontado": valor_descontado,
        "credito_depois": credito_depois,
        "utilizado_depois": utilizado_depois,
        "pendente": pendente,
    }


def persistir_saldos_mensais(competencia: str, mapa_creditos: Dict[str, Dict[str, Any]]) -> None:
    payload = []

    for _, item in mapa_creditos.items():
        payload.append({
            "competencia": competencia,
            "doutor_id": item["id"],
            "credito_inicial": round(float(item["credito_inicial"]), 2),
            "utilizado": round(float(item["utilizado"]), 2),
            "credito_final": round(float(item["credito_disponivel"]), 2),
        })

    if not payload:
        return

    url = f"{SUPABASE_URL}/rest/v1/doutores_saldos_mensais"
    upsert_supabase(url, payload, "competencia,doutor_id")


def listar_saldos_finais(mapa_creditos: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    saida: List[Dict[str, Any]] = []

    for _, item in mapa_creditos.items():
        saida.append({
            "doutor_id": item["id"],
            "doutor": item["nome_original"],
            "credito_inicial": round(float(item["credito_inicial"]), 2),
            "utilizado": round(float(item["utilizado"]), 2),
            "credito_disponivel": round(float(item["credito_disponivel"]), 2),
            "pix_key": item.get("pix_key", ""),
        })

    saida.sort(key=lambda x: x["doutor"].lower())
    return saida
