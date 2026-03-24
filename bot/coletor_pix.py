from playwright.sync_api import sync_playwright
import json
from datetime import datetime

TOP_USER = ""
TOP_PASS = ""

import os
TOP_USER = os.getenv("TOP_USER")
TOP_PASS = os.getenv("TOP_PASS")

UNIDADES = [
    ("Caxias", "http://caxias.topesteticabucal.com.br/sistema"),
]

def coletar_unidade(nome, url, page):
    print(f"[INFO] Acessando {nome}")

    page.goto(url)

    # LOGIN (AJUSTAR SE NECESSÁRIO)
    page.fill('input[type="text"]', TOP_USER)
    page.fill('input[type="password"]', TOP_PASS)
    page.click('button')

    page.wait_for_timeout(3000)

    print("[DEBUG] URL após login:", page.url)

    # TENTAR NAVEGAR
    try:
        page.click("text=Finanças")
        page.click("text=Demonstrativo de Resultados")
    except:
        print("[ERRO] Não encontrou menus")

    page.wait_for_timeout(3000)

    # FILTRO PIX
    try:
        page.select_option("select", label="PIX Doutores")
    except:
        print("[ERRO] Não encontrou filtro PIX")

    page.wait_for_timeout(2000)

    try:
        page.click("text=Buscar")
    except:
        print("[ERRO] Não encontrou botão buscar")

    page.wait_for_timeout(5000)

    # DEBUG: salvar HTML
    html = page.content()
    with open("debug.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("[DEBUG] HTML salvo")

    # TENTAR PEGAR LINHAS
    linhas = page.locator("table tr")
    print("[DEBUG] Linhas encontradas:", linhas.count())

    dados = []

    for i in range(linhas.count()):
        try:
            cols = linhas.nth(i).locator("td")
            if cols.count() >= 4:
                dados.append({
                    "data": cols.nth(0).inner_text(),
                    "unidade": nome,
                    "doutor": cols.nth(1).inner_text(),
                    "metodo": "PIX Doutores",
                    "origem": cols.nth(2).inner_text(),
                    "valor": cols.nth(3).inner_text(),
                    "mes": 3,
                    "ano": 2026
                })
        except:
            pass

    return dados


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        todos = []

        for nome, url in UNIDADES:
            dados = coletar_unidade(nome, url, page)
            todos.extend(dados)

        browser.close()

    with open("data/pix_doutores.json", "w", encoding="utf-8") as f:
        json.dump(todos, f, indent=2, ensure_ascii=False)

    print("✅ Dados coletados:", len(todos))


if __name__ == "__main__":
    main()
