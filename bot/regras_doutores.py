# regras_doutores.py
from __future__ import annotations

import unicodedata
from typing import Dict, List, Any


DOUTORES_BASE: List[Dict[str, Any]] = [
    { "doutor": "Adriele da Silva", "credito": 3000.00, "ativo": True },
    { "doutor": "Alan Sechin", "credito": 0.00, "ativo": True },
    { "doutor": "Alexandre Favero", "credito": 1500.00, "ativo": True },
    { "doutor": "Ana Carolina Portes", "credito": 1200.00, "ativo": True },
    { "doutor": "Ana Cristina Corso", "credito": 1500.00, "ativo": True },
    { "doutor": "Andrielli Caxambu", "credito": 0.00, "ativo": True },
    { "doutor": "Bianca Hofman", "credito": 0.00, "ativo": True },
    { "doutor": "Bruno Castellan", "credito": 600.00, "ativo": True },
    { "doutor": "Bruno Lorenzoni", "credito": 0.00, "ativo": True },
    { "doutor": "Cristian Pressi", "credito": 8000.00, "ativo": True },
    { "doutor": "Murilo Debortoli", "credito": 500.00, "ativo": True },
    { "doutor": "CIR.Dionathan Paim Pohlmann", "credito": 6000.00, "ativo": True },
    { "doutor": "Keyla Daniele", "credito": 500.00, "ativo": True },
    { "doutor": "Everlize Cipriani", "credito": 2000.00, "ativo": True },
    { "doutor": "Fernana Sozo", "credito": 1500.00, "ativo": True },
    { "doutor": "Franciele Pedrotti", "credito": 10000.00, "ativo": True },
    { "doutor": "Norberto Filipe", "credito": 500.00, "ativo": True },
    { "doutor": "Gabrielli Fabonato", "credito": 4000.00, "ativo": True },
    { "doutor": "Giovana Gasparini", "credito": 1000.00, "ativo": True },
    { "doutor": "Gislaine Santos", "credito": 1000.00, "ativo": True },
    { "doutor": "Greici Matiello", "credito": 500.00, "ativo": True },
    { "doutor": "Indiamara Rech", "credito": 0.00, "ativo": True },
    { "doutor": "Jéssica Barreto", "credito": 1000.00, "ativo": True },
    { "doutor": "Joana Sganzerla", "credito": 500.00, "ativo": True },
    { "doutor": "João Augusto Keler", "credito": 1000.00, "ativo": True },
    { "doutor": "Juana Billig", "credito": 2500.00, "ativo": True },
    { "doutor": "Laura Luiza Cimolin", "credito": 0.00, "ativo": True },
    { "doutor": "Leandro Diniz", "credito": 400.00, "ativo": True },
    { "doutor": "Letícia Cauzzi", "credito": 4000.00, "ativo": True },
    { "doutor": "Luiz Henrique", "credito": 2500.00, "ativo": True },
    { "doutor": "Leticia Canabarro (SOL)", "credito": 900.00, "ativo": True },
    { "doutor": "Marcella Zancanaro", "credito": 1200.00, "ativo": True },
    { "doutor": "Matheus Strapasson", "credito": 1000.00, "ativo": True },
    { "doutor": "Morgana Zambiasi", "credito": 1500.00, "ativo": True },
    { "doutor": "Naiane Pieta", "credito": 1000.00, "ativo": True },
    { "doutor": "Nelson Vaccari", "credito": 4000.00, "ativo": True },
    { "doutor": "Nicoli Weber", "credito": 1000.00, "ativo": True },
    { "doutor": "Evalda Baldissera", "credito": 5604.82, "ativo": True },
    { "doutor": "Rodrigo Silveira", "credito": 458.00, "ativo": True },
    { "doutor": "Sara Trevisol", "credito": 1000.00, "ativo": True },
    { "doutor": "Sofie Owens", "credito": 3500.00, "ativo": True },
    { "doutor": "Tamara Macanan", "credito": 5000.00, "ativo": True },
    { "doutor": "Gustavo Lourenço Ongaratto", "credito": 3000.00, "ativo": True },
    { "doutor": "Thiany Cristofoli", "credito": 4000.00, "ativo": True },
    { "doutor": "Thalia Tessaro", "credito": 2700.00, "ativo": True },
    { "doutor": "Thalia Vezzosi", "credito": 2500.00, "ativo": True },
]


def normalizar_nome(nome: str) -> str:
    nome = nome.strip().lower()
    nome = unicodedata.normalize("NFKD", nome)
    nome = "".join(c for c in nome if not unicodedata.combining(c))
    nome = " ".join(nome.split())
    return nome


def montar_mapa_creditos() -> Dict[str, Dict[str, Any]]:
    mapa: Dict[str, Dict[str, Any]] = {}

    for item in DOUTORES_BASE:
        if not item.get("ativo", False):
            continue

        chave = normalizar_nome(item["doutor"])
        mapa[chave] = {
            "nome_original": item["doutor"],
            "credito_inicial": float(item["credito"]),
            "credito_disponivel": float(item["credito"]),
            "ativo": item["ativo"],
        }

    return mapa


def aplicar_desconto(mapa_creditos: Dict[str, Dict[str, Any]], nome_doutor: str, valor: float) -> Dict[str, Any]:
    chave = normalizar_nome(nome_doutor)

    if chave not in mapa_creditos:
        return {
            "doutor_encontrado": False,
            "nome_padronizado": chave,
            "credito_antes": 0.0,
            "valor_descontado": 0.0,
            "credito_depois": 0.0,
            "pendente": round(valor, 2),
        }

    credito_antes = float(mapa_creditos[chave]["credito_disponivel"])
    valor_descontado = min(valor, credito_antes)
    credito_depois = round(credito_antes - valor_descontado, 2)
    pendente = round(valor - valor_descontado, 2)

    mapa_creditos[chave]["credito_disponivel"] = credito_depois

    return {
        "doutor_encontrado": True,
        "nome_padronizado": mapa_creditos[chave]["nome_original"],
        "credito_antes": round(credito_antes, 2),
        "valor_descontado": round(valor_descontado, 2),
        "credito_depois": round(credito_depois, 2),
        "pendente": round(pendente, 2),
    }
