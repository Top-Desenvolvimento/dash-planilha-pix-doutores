from __future__ import annotations

import json
import os
import unicodedata
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    import requests
except Exception:
    requests = None


SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

DATA_DIR = Path("data")
ARQ_DOUTORES_LOCAL = DATA_DIR / "doutores_config_local.json"
ARQ_SALDOS_LOCAL = DATA_DIR / "doutores_saldos_mensais_local.json"


def normalizar_nome(nome: str) -> str:
    nome = (nome or "").strip().lower()
    nome = unicodedata.normalize("NFKD", nome)
    nome = "".join(c for c in nome if not unicodedata.combining(c))
    nome = " ".join(nome.split())
    return nome


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


def carregar_doutores_config_local() -> List[Dict[str, Any]]:
    dados = carregar_json(ARQ_DOUTORES_LOCAL, [])
    if not dados:
        dados = [
            {"id": "1", "nome": "Adriele da Silva", "nome_normalizado": normalizar_nome("Adriele da Silva"), "credito": 3000.00, "pix_key": "", "ativo": True},
            {"id": "2", "nome": "Alan Sechin", "nome_normalizado": normalizar_nome("Alan Sechin"), "credito": 0.00, "pix_key": "", "ativo": True},
            {"id": "3", "nome": "Alexandre Favero", "nome_normalizado": normalizar_nome("Alexandre Favero"), "credito": 1500.00, "pix_key": "", "ativo": True},
            {"id": "4", "nome": "Ana Carolina Portes", "nome_normalizado": normalizar_nome("Ana Carolina Portes"), "credito": 1200.00, "pix_key": "", "ativo": True},
            {"id": "5", "nome": "Ana Cristina Corso", "nome_normalizado": normalizar_nome("Ana Cristina Corso"), "credito": 1500.00, "pix_key": "", "ativo": True},
            {"id": "6", "nome": "Andrielli Caxambu", "nome_normalizado": normalizar_nome("Andrielli Caxambu"), "credito": 0.00, "pix_key": "", "ativo": True},
            {"id": "7", "nome": "Bianca Hofman", "nome_normalizado": normalizar_nome("Bianca Hofman"), "credito": 0.00, "pix_key": "", "ativo": True},
            {"id": "8", "nome": "Bruno Castellan", "nome_normalizado": normalizar_nome("Bruno Castellan"), "credito": 600.00, "pix_key": "", "ativo": True},
            {"id": "9", "nome": "Bruno Lorenzoni", "nome_normalizado": normalizar_nome("Bruno Lorenzoni"), "credito": 0.00, "pix_key": "", "ativo": True},
            {"id": "10", "nome": "Cristian Pressi", "nome_normalizado": normalizar_nome("Cristian Pressi"), "credito": 8000.00, "pix_key": "", "ativo": True},
            {"id": "11", "nome": "Murilo Debortoli", "nome_normalizado": normalizar_nome("Murilo Debortoli"), "credito": 500.00, "pix_key": "", "ativo": True},
            {"id": "12", "nome": "CIR.Dionathan Paim Pohlmann", "nome_normalizado": normalizar_nome("CIR.Dionathan Paim Pohlmann"), "credito": 6000.00, "pix_key": "", "ativo": True},
            {"id": "13", "nome": "Keyla Daniele", "nome_normalizado": normalizar_nome("Keyla Daniele"), "credito": 500.00, "pix_key": "", "ativo": True},
            {"id": "14", "nome": "Everlize Cipriani", "nome_normalizado": normalizar_nome("Everlize Cipriani"), "credito": 2000.00, "pix_key": "", "ativo": True},
            {"id": "15", "nome": "Fernana Sozo", "nome_normalizado": normalizar_nome("Fernana Sozo"), "credito": 1500.00, "pix_key": "", "ativo": True},
            {"id": "16", "nome": "Franciele Pedrotti", "nome_normalizado": normalizar_nome("Franciele Pedrotti"), "credito": 10000.00, "pix_key": "", "ativo": True},
            {"id": "17", "nome": "Norberto Filipe", "nome_normalizado": normalizar_nome("Norberto Filipe"), "credito": 500.00, "pix_key": "", "ativo": True},
            {"id": "18", "nome": "Gabrielli Fabonato", "nome_normalizado": normalizar_nome("Gabrielli Fabonato"), "credito": 4000.00, "pix_key": "", "ativo": True},
            {"id": "19", "nome": "Giovana Gasparini", "nome_normalizado": normalizar_nome("Giovana Gasparini"), "credito": 1000.00, "pix_key": "", "ativo": True},
            {"id": "20", "nome": "Gislaine Santos", "nome_normalizado": normalizar_nome("Gislaine Santos"), "credito": 1000.00, "pix_key": "", "ativo": True},
            {"id": "21", "nome": "Greici Matiello", "nome_normalizado": normalizar_nome("Greici Matiello"), "credito": 500.00, "pix_key": "", "ativo": True},
            {"id": "22", "nome": "Indiamara Rech", "nome_normalizado": normalizar_nome("Indiamara Rech"), "credito": 0.00, "pix_key": "", "ativo": True},
            {"id": "23", "nome": "Jéssica Barreto", "nome_normalizado": normalizar_nome("Jéssica Barreto"), "credito": 1000.00, "pix_key": "", "ativo": True},
            {"id": "24", "nome": "Joana Sganzerla", "nome_normalizado": normalizar_nome("Joana Sganzerla"), "credito": 500.00, "pix_key": "", "ativo": True},
            {"id": "25", "nome": "João Augusto Keler", "nome_normalizado": normalizar_nome("João Augusto Keler"), "credito": 1000.00, "pix_key": "", "ativo": True},
            {"id": "26", "nome": "Juana Billig", "nome_normalizado": normalizar_nome("Juana Billig"), "credito": 2500.00, "pix_key": "", "ativo": True},
            {"id": "27", "nome": "Laura Luiza Cimolin", "nome_normalizado": normalizar_nome("Laura Luiza Cimolin"), "credito": 0.00, "pix_key": "", "ativo": True},
            {"id": "28", "nome": "Leandro Diniz", "nome_normalizado": normalizar_nome("Leandro Diniz"), "credito": 400.00, "pix_key": "", "ativo": True},
            {"id": "29", "nome": "Letícia Cauzzi", "nome_normalizado": normalizar_nome("Letícia Cauzzi"), "credito": 4000.00, "pix_key": "", "ativo": True},
            {"id": "30", "nome": "Luiz Henrique", "nome_normalizado": normalizar_nome("Luiz Henrique"), "credito": 2500.00, "pix_key": "", "ativo": True},
            {"id": "31", "nome": "Leticia Canabarro (SOL)", "nome_normalizado": normalizar_nome("Leticia Canabarro (SOL)"), "credito": 900.00, "pix_key": "", "ativo": True},
            {"id": "32", "nome": "Marcella Zancanaro", "nome_normalizado": normalizar_nome("Marcella Zancanaro"), "credito": 1200.00, "pix_key": "", "ativo": True},
            {"id": "33", "nome": "Matheus Strapasson", "nome_normalizado": normalizar_nome("Matheus Strapasson"), "credito": 1000.00, "pix_key": "", "ativo": True},
            {"id": "34", "nome": "Morgana Zambiasi", "nome_normalizado": normalizar_nome("Morgana Zambiasi"), "credito": 1500.00, "pix_key": "", "ativo": True},
            {"id": "35", "nome": "Naiane Pieta", "nome_normalizado": normalizar_nome("Naiane Pieta"), "credito": 1000.00, "pix_key": "", "ativo": True},
            {"id": "36", "nome": "Nelson Vaccari", "nome_normalizado": normalizar_nome("Nelson Vaccari"), "credito": 4000.00, "pix_key": "", "ativo": True},
            {"id": "37", "nome": "Nicoli Weber", "nome_normalizado": normalizar_nome("Nicoli Weber"), "credito": 1000.00, "pix_key": "", "ativo": True},
            {"id": "38", "nome": "Evalda Baldissera", "nome_normalizado": normalizar_nome("Evalda Baldissera"), "credito": 5604.82, "pix_key": "", "ativo": True},
            {"id": "39", "nome": "Rodrigo Silveira", "nome_normalizado": normalizar_nome("Rodrigo Silveira"), "credito": 458.00, "pix_key": "", "ativo": True},
            {"id": "40", "nome": "Sara Trevisol", "nome_normalizado": normalizar_nome("Sara Trevisol"), "credito": 1000.00, "pix_key": "", "ativo": True},
            {"id": "41", "nome": "Sofie Owens", "nome_normalizado": normalizar_nome("Sofie Owens"), "credito": 3500.00, "pix_key": "", "ativo": True},
            {"id": "42", "nome": "Tamara Macanan", "nome_normalizado": normalizar_nome("Tamara Macanan"), "credito": 5000.00, "pix_key": "", "ativo": True},
            {"id": "43", "nome": "Gustavo Lourenço Ongaratto", "nome_normalizado": normalizar_nome("Gustavo Lourenço Ongaratto"), "credito": 3000.00, "pix_key": "", "ativo": True},
            {"id": "44", "nome": "Thiany Cristofoli", "nome_normalizado": normalizar_nome("Thiany Cristofoli"), "credito": 4000.00, "pix_key": "", "ativo": True},
            {"id": "45", "nome": "Thalia Tessaro", "nome_normalizado": normalizar_nome("Thalia Tessaro"), "credito": 2700.00, "pix_key": "", "ativo": True},
            {"id": "46", "nome": "Thalia Vezzosi", "nome_normalizado": normalizar_nome("Thalia Vezzosi"), "credito": 2500.00, "pix_key": "", "ativo": True},
        ]
        salvar_json(dados, ARQ_DOUTORES_LOCAL)
    return [d for d in dados if d.get("ativo", True)]


def carregar_doutores_config() -> List[Dict[str, Any]]:
    if not usando_supabase():
        print("[WARN] Supabase não configurado. Usando doutores locais.")
        return carregar_doutores_config_local()

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


def carregar_saldos_locais() -> Dict[str, List[Dict[str, Any]]]:
    return carregar_json(ARQ_SALDOS_LOCAL, {})


def salvar_saldos_locais(dados: Dict[str, List[Dict[str, Any]]]) -> None:
    salvar_json(dados, ARQ_SALDOS_LOCAL)


def carregar_saldos_mensais(competencia: str) -> List[Dict[str, Any]]:
    if not usando_supabase():
        return carregar_saldos_locais().get(competencia, [])

    url = f"{SUPABASE_URL}/rest/v1/doutores_saldos_mensais"
    params = {
        "select": "id,competencia,doutor_id,credito_inicial,utilizado,credito_final,ajuste_manual,observacao,updated_by_email",
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
            "utilizado": 0.0,
            "credito_final": round(credito_inicial, 2),
            "ajuste_manual": 0.0,
            "observacao": None,
            "updated_by_email": None,
        })

    if usando_supabase():
        url = f"{SUPABASE_URL}/rest/v1/doutores_saldos_mensais"
        return upsert_supabase(url, payload, "competencia,doutor_id")

    todos = carregar_saldos_locais()
    todos[competencia] = payload
    salvar_saldos_locais(todos)
    return payload


def montar_mapa_creditos(competencia: str, competencia_anterior: Optional[str]) -> Dict[str, Dict[str, Any]]:
    doutores = carregar_doutores_config()
    saldos = inicializar_saldos_competencia(competencia, competencia_anterior)

    saldos_por_doutor = {item["doutor_id"]: item for item in saldos}
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
            "updated_by_email": None,
        })

    if usando_supabase():
        url = f"{SUPABASE_URL}/rest/v1/doutores_saldos_mensais"
        upsert_supabase(url, payload, "competencia,doutor_id")
        return

    todos = carregar_saldos_locais()
    todos[competencia] = payload
    salvar_saldos_locais(todos)


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
