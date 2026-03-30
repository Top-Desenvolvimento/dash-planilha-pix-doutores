from playwright.sync_api import sync_playwright
import json
import os
import re
from datetime import datetime, date
from calendar import monthrange
from pathlib import Path
from unicodedata import normalize

TOP_USER = os.getenv("TOP_USER")
TOP_PASS = os.getenv("TOP_PASS")

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

CREDITOS_PATH = DATA_DIR / "doutores_credito.json"
OUTPUT_PATH = DATA_DIR / "pix_doutores.json"

UNIDADES = [
    ("Caxias", "http://caxias.topesteticabucal.com.br/sistema"),
]


def obter_periodo_mes_atual():
    hoje = date.today()
    primeiro = hoje.replace(day=1)
    ultimo = hoje.replace(day=monthrange(hoje.year, hoje.month)[1])
    return primeiro.strftime("%d/%m/%Y"), ultimo.strftime("%d/%m/%Y")


DATA_INICIAL, DATA_FINAL = obter_periodo_mes_atual()


def salvar_debug(page, nome):
    try:
        with open(f"debug_{nome}.html", "w", encoding="utf-8") as f:
            f.write(page.content())
        page.screenshot(path=f"debug_{nome}.png", full_page=True)
        print(f"[DEBUG] Debug salvo: {nome}")
    except:
        pass


def parse_valor_brl(txt):
    txt = str(txt).replace("R$", "").replace(".", "").replace(",", ".")
    return float(txt)


def sem_acento(txt):
    return normalize("NFKD", txt).encode("ASCII", "ignore").decode("ASCII")


def normalizar_nome(txt):
    txt = sem_acento(str(txt)).lower()
    txt = re.sub(r"\b(dr|dra|cir)\.?\b", "", txt)
    txt = re.sub(r"[^a-z0-9\s]", " ", txt)
    return re.sub(r"\s+", " ", txt).strip()


def carregar_creditos():
    with open(CREDITOS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def mapear_nome(nome, creditos):
    alvo = normalizar_nome(nome)

    for c in creditos:
        if normalizar_nome(c["doutor"]) == alvo:
            return c["doutor"]

    return None


def fazer_login(page):
    page.locator("input[type='text']").first.fill(TOP_USER)
    page.locator("input[type='password']").first.fill(TOP_PASS)
    page.keyboard.press("Enter")
    page.wait_for_timeout(5000)


def navegar(page):
    page.locator("text=FINANÇAS").click()
    page.wait_for_timeout(2000)
    page.locator("text=Demonstrativo").click()
    page.wait_for_timeout(4000)


def preencher_filtros(page):
    print("[DEBUG] Preenchendo filtros")

    inputs = page.locator("input")
    inputs.nth(0).fill(DATA_INICIAL)
    inputs.nth(1).fill(DATA_FINAL)

    page.keyboard.press("Tab")
    page.keyboard.type("Pix Doutores")
    page.keyboard.press("Enter")

    page.wait_for_timeout(2000)


def buscar(page):
    page.locator("text=Buscar").click()
    page.wait_for_timeout(5000)


def ler_tabela(page, unidade, creditos):
    dados = []

    tabelas = page.locator("table")
    print("[DEBUG] tabelas:", tabelas.count())

    tabela = tabelas.nth(0)
    linhas = tabela.locator("tr")

    for i in range(linhas.count()):
        try:
            cols = linhas.nth(i).locator("td")

            if cols.count() < 4:
                continue

            data = cols.nth(0).inner_text()
            metodo = cols.nth(1).inner_text()
            valor = cols.nth(3).inner_text()

            if "pix doutores" not in metodo.lower():
                continue

            dados.append({
                "data": data,
                "valor": parse_valor_brl(valor),
                "doutor": mapear_nome(metodo, creditos),
                "unidade": unidade
            })

        except:
            continue

    print("[DEBUG] registros:", len(dados))
    return dados


def main():
    creditos = carregar_creditos()
    todos = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for nome, url in UNIDADES:
            page.goto(url)

            fazer_login(page)
            navegar(page)
            preencher_filtros(page)
            buscar(page)

            dados = ler_tabela(page, nome, creditos)
            todos.extend(dados)

        browser.close()

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(todos, f, indent=2, ensure_ascii=False)

    print("✅ Coleta finalizada")


if __name__ == "__main__":
    main()
