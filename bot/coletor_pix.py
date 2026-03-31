# coletor_pix.py
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from regras_doutores import montar_mapa_creditos, aplicar_desconto


USUARIO = "MANUS"
SENHA = "MANUS2026"

SISTEMAS = [
    {"unidade": "Caxias", "url": "http://caxias.topesteticabucal.com.br/sistema"},
    {"unidade": "Farroupilha", "url": "http://farroupilha.topesteticabucal.com.br/sistema"},
    {"unidade": "Bento", "url": "http://bento.topesteticabucal.com.br/sistema"},
    {"unidade": "Encantado", "url": "http://encantado.topesteticabucal.com.br/sistema"},
    {"unidade": "Soledade", "url": "http://soledade.topesteticabucal.com.br/sistema"},
    {"unidade": "Garibaldi", "url": "http://garibaldi.topesteticabucal.com.br/sistema"},
    {"unidade": "Veranopolis", "url": "http://veranopolis.topesteticabucal.com.br/sistema"},
    {"unidade": "Ssdocai", "url": "http://ssdocai.topesteticabucal.com.br/sistema"},
]

ARQUIVO_SAIDA = Path("data/pix_doutores.json")


def parse_valor(texto: str) -> float:
    if not texto:
        return 0.0

    texto = texto.strip()
    texto = texto.replace("R$", "").replace(".", "").replace(",", ".")
    texto = re.sub(r"[^\d.-]", "", texto)

    try:
        return round(float(texto), 2)
    except ValueError:
        return 0.0


def salvar_json(dados: List[Dict[str, Any]], caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def fazer_login(page, url: str) -> None:
    page.goto(url, wait_until="domcontentloaded", timeout=60000)

    # Ajuste esses seletores conforme o HTML real da página
    page.fill('input[name="login"], input[name="usuario"], input[type="text"]', USUARIO)
    page.fill('input[name="senha"], input[type="password"]', SENHA)
    page.click('button[type="submit"], input[type="submit"], button:has-text("Entrar")')

    page.wait_for_load_state("networkidle")


def acessar_demonstrativo(page) -> None:
    # Ajuste os seletores/textos conforme o sistema
    page.click("text=Finanças")
    page.click("text=Demonstrativo de Resultados")
    page.wait_for_load_state("networkidle")

    # Tenta selecionar "mês atual" se existir campo/filtro
    possiveis_seletores = [
        'select[name*="period"]',
        'select[name*="mes"]',
        'input[name*="period"]',
        'input[name*="mes"]',
    ]

    for seletor in possiveis_seletores:
        try:
            if page.locator(seletor).count() > 0:
                locator = page.locator(seletor).first
                tag_name = locator.evaluate("el => el.tagName.toLowerCase()")
                if tag_name == "select":
                    try:
                        locator.select_option(label="Mês Atual")
                    except Exception:
                        pass
                break
        except Exception:
            pass

    # Botão para aplicar filtro, se existir
    for texto in ["Filtrar", "Buscar", "Pesquisar", "Aplicar"]:
        try:
            if page.locator(f'text={texto}').count() > 0:
                page.click(f"text={texto}")
                page.wait_for_load_state("networkidle")
                break
        except Exception:
            pass


def extrair_linhas_pix(page, unidade: str, mapa_creditos: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    resultados: List[Dict[str, Any]] = []

    # Você vai provavelmente ajustar esse seletor para a tabela correta do sistema
    tabelas = page.locator("table")
    total_tabelas = tabelas.count()

    for i in range(total_tabelas):
        tabela = tabelas.nth(i)
        linhas = tabela.locator("tr")
        qtd_linhas = linhas.count()

        for j in range(qtd_linhas):
            linha = linhas.nth(j)
            texto_linha = linha.inner_text().strip()

            if not texto_linha:
                continue

            if "pix doutores" not in texto_linha.lower():
                continue

            registro = interpretar_linha(linha, texto_linha, unidade, mapa_creditos)
            if registro:
                resultados.append(registro)

    return resultados


def interpretar_linha(linha, texto_linha: str, unidade: str, mapa_creditos: Dict[str, Dict[str, Any]]) -> Dict[str, Any] | None:
    colunas = linha.locator("td")
    qtd_colunas = colunas.count()

    textos_colunas = []
    for i in range(qtd_colunas):
        textos_colunas.append(colunas.nth(i).inner_text().strip())

    # IMPORTANTE:
    # Aqui você precisa ajustar a posição das colunas conforme a tabela real.
    # Exemplo suposto:
    # [data, paciente, doutor, forma_pagamento, valor, ...]
    nome_doutor = ""
    valor = 0.0
    forma_pagamento = ""

    if qtd_colunas >= 5:
        nome_doutor = textos_colunas[2]
        forma_pagamento = textos_colunas[3]
        valor = parse_valor(textos_colunas[4])
    else:
        # fallback bruto pelo texto inteiro
        forma_pagamento = "PIX DOUTORES"
        valor = extrair_primeiro_valor(texto_linha)
        nome_doutor = tentar_extrair_nome(textos_colunas, texto_linha)

    desconto = aplicar_desconto(mapa_creditos, nome_doutor, valor)

    return {
        "unidade": unidade,
        "competencia": datetime.now().strftime("%Y-%m"),
        "doutor_lido": nome_doutor,
        "doutor_final": desconto["nome_padronizado"],
        "doutor_encontrado": desconto["doutor_encontrado"],
        "forma_pagamento": forma_pagamento,
        "valor_pix_doutores": round(valor, 2),
        "credito_antes": desconto["credito_antes"],
        "valor_descontado": desconto["valor_descontado"],
        "credito_depois": desconto["credito_depois"],
        "pendente": desconto["pendente"],
        "linha_original": texto_linha,
        "coletado_em": datetime.now().isoformat(),
    }


def extrair_primeiro_valor(texto: str) -> float:
    padroes = re.findall(r'R?\$?\s?\d{1,3}(?:\.\d{3})*,\d{2}', texto)
    if not padroes:
        return 0.0
    return parse_valor(padroes[0])


def tentar_extrair_nome(colunas: List[str], texto_linha: str) -> str:
    # Ajuste essa heurística conforme o padrão real do sistema
    for item in colunas:
        if len(item.split()) >= 2 and "pix" not in item.lower():
            return item.strip()
    return texto_linha.strip()


def processar_unidade(browser, sistema: Dict[str, str], mapa_creditos: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    unidade = sistema["unidade"]
    url = sistema["url"]

    print(f"[INFO] Processando unidade: {unidade}")

    context = browser.new_context()
    page = context.new_page()

    try:
        fazer_login(page, url)
        acessar_demonstrativo(page)
        resultados = extrair_linhas_pix(page, unidade, mapa_creditos)
        return resultados

    except PlaywrightTimeoutError:
        print(f"[ERRO] Timeout na unidade {unidade}")
        return [{
            "unidade": unidade,
            "erro": "Timeout ao acessar sistema",
            "coletado_em": datetime.now().isoformat(),
        }]
    except Exception as e:
        print(f"[ERRO] Falha na unidade {unidade}: {e}")
        return [{
            "unidade": unidade,
            "erro": str(e),
            "coletado_em": datetime.now().isoformat(),
        }]
    finally:
        context.close()


def main() -> None:
    mapa_creditos = montar_mapa_creditos()
    todos_resultados: List[Dict[str, Any]] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for sistema in SISTEMAS:
            resultados = processar_unidade(browser, sistema, mapa_creditos)
            todos_resultados.extend(resultados)

        browser.close()

    salvar_json(todos_resultados, ARQUIVO_SAIDA)
    print(f"[OK] Arquivo gerado em: {ARQUIVO_SAIDA}")


if __name__ == "__main__":
    main()
