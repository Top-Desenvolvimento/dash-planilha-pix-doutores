from playwright.sync_api import sync_playwright
import os

TOP_USER = os.getenv("TOP_USER")
TOP_PASS = os.getenv("TOP_PASS")

UNIDADE = ("Caxias", "http://caxias.topesteticabucal.com.br/sistema")


def salvar_debug(page, nome):
    with open(f"{nome}.html", "w", encoding="utf-8") as f:
        f.write(page.content())
    page.screenshot(path=f"{nome}.png", full_page=True)
    print(f"[DEBUG] Arquivos salvos: {nome}.html e {nome}.png")


def fazer_login(page):
    page.locator('input[type="text"], input[name="usuario"], input[name="login"]').first.fill(TOP_USER)
    page.locator('input[type="password"], input[name="senha"]').first.fill(TOP_PASS)

    botoes = [
        'input[type="submit"]',
        'button[type="submit"]',
        'text=Entrar',
        'text=Login',
        'text=Acessar'
    ]

    for seletor in botoes:
        try:
            if page.locator(seletor).first.count() > 0:
                page.locator(seletor).first.click(timeout=5000)
                print(f"[DEBUG] Login clicado com: {seletor}")
                page.wait_for_timeout(5000)
                return
        except Exception:
            continue

    page.locator('input[type="password"]').first.press("Enter")
    page.wait_for_timeout(5000)
    print("[DEBUG] Login via Enter")


def navegar_demonstrativo(page):
    page.locator("text=FINANÇAS").first.click(timeout=10000)
    print("[DEBUG] Clique em FINANÇAS")
    page.wait_for_timeout(2000)

    opcoes = [
        "text=Demonstrativo de Resultado",
        "text=Demonstrativo de Resultados",
        "a:has-text('Demonstrativo de Resultado')",
        "a:has-text('Demonstrativo de Resultados')"
    ]

    for seletor in opcoes:
        try:
            if page.locator(seletor).first.count() > 0:
                page.locator(seletor).first.click(timeout=10000)
                print(f"[DEBUG] Clique em demonstrativo com: {seletor}")
                page.wait_for_timeout(4000)
                return
        except Exception:
            continue

    raise RuntimeError("Não encontrei Demonstrativo de Resultado.")


def main():
    if not TOP_USER or not TOP_PASS:
        raise RuntimeError("TOP_USER e TOP_PASS não definidos nos Secrets.")

    nome, url = UNIDADE

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(f"[INFO] Acessando {nome}")
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)

        salvar_debug(page, "debug_Caxias_01_abertura")

        fazer_login(page)
        print("[DEBUG] URL após login:", page.url)
        salvar_debug(page, "debug_Caxias_02_pos_login")

        navegar_demonstrativo(page)
        print("[DEBUG] URL no demonstrativo:", page.url)
        salvar_debug(page, "debug_Caxias_03_demonstrativo")

        browser.close()


if __name__ == "__main__":
    main()
