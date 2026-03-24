from playwright.sync_api import sync_playwright
import json
import os

TOP_USER = os.getenv("TOP_USER")
TOP_PASS = os.getenv("TOP_PASS")

UNIDADES = [
    ("Caxias", "http://caxias.topesteticabucal.com.br/sistema"),
]

def salvar_debug(page, nome):
    with open(f"debug_{nome}.html", "w", encoding="utf-8") as f:
        f.write(page.content())
    page.screenshot(path=f"debug_{nome}.png", full_page=True)
    print(f"[DEBUG] Salvos: debug_{nome}.html e debug_{nome}.png")

def clicar_login(page):
    tentativas = [
        'button[type="submit"]',
        'input[type="submit"]',
        'button',
        'text=Entrar',
        'text=Login',
        'text=Acessar'
    ]

    for seletor in tentativas:
        try:
            loc = page.locator(seletor).first
            if loc.count() > 0:
                loc.click(timeout=5000)
                print(f"[DEBUG] Clique no login com seletor: {seletor}")
                return
        except Exception:
            continue

    try:
        page.locator('input[type="password"]').first.press("Enter")
        print("[DEBUG] Login via Enter no campo senha")
        return
    except Exception:
        pass

    raise RuntimeError("Não encontrei um botão de login válido.")

def coletar_unidade(nome, url, page):
    print(f"[INFO] Acessando {nome}")
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(3000)

    salvar_debug(page, "01_abertura")

    page.locator('input[type="text"], input[name="usuario"], input[name="login"]').first.fill(TOP_USER)
    page.locator('input[type="password"], input[name="senha"]').first.fill(TOP_PASS)
    print("[DEBUG] Usuário e senha preenchidos")

    clicar_login(page)
    page.wait_for_timeout(5000)

    print("[DEBUG] URL após login:", page.url)
    print("[DEBUG] Título:", page.title())
    salvar_debug(page, "02_pos_login")

    dados = []
    return dados

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        todos = []
        for nome, url in UNIDADES:
            try:
                dados = coletar_unidade(nome, url, page)
                todos.extend(dados)
            except Exception as e:
                print(f"[ERRO] Unidade {nome}: {e}")

        browser.close()

    with open("data/pix_doutores.json", "w", encoding="utf-8") as f:
        json.dump(todos, f, indent=2, ensure_ascii=False)

    print("✅ Dados coletados:", len(todos))

if __name__ == "__main__":
    main()
