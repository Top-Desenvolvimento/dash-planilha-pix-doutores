from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
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
            if page.locator(seletor).first.is_visible(timeout=3000):
                page.locator(seletor).first.click(timeout=5000)
                print(f"[DEBUG] Clique no login com seletor: {seletor}")
                return
        except Exception:
            continue

    # fallback: Enter no campo senha
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

    # Login
    page.locator('input[type="text"], input[name="usuario"], input[name="login"]').first.fill(TOP_USER)
    page.locator('input[type="password"], input[name="senha"]').first.fill(TOP_PASS)
    print("[DEBUG] Usuário e senha preenchidos")

    clicar_login(page)
    page.wait_for_timeout(5000)

    print("[DEBUG] URL após login:", page.url)
    print("[DEBUG] Título:", page.title())
    salvar_debug(page, "02_pos_login")

    # Navegação
    try:
        page.locator("text=Finanças").first.click(timeout=10000)
        page.wait_for_timeout(2000)
        page.locator("text=Demonstrativo de Resultados").first.click(timeout=10000)
        page.wait_for_timeout(4000)
        print("[DEBUG] Navegação até relatório OK")
    except Exception as e:
        print("[ERRO] Não encontrou menus:", e)
        salvar_debug(page, "03_erro_menu")
        return []

    # Filtro PIX
    try:
        selects = page.locator("select")
        total = selects.count()
        print("[DEBUG] Quantidade de selects:", total)

        encontrou = False
        for i in range(total):
            opcoes = selects.nth(i).locator("option").all_inner_texts()
            print(f"[DEBUG] Select {i} opções:", opcoes)
            for op in opcoes:
                if "PIX Doutores" in op:
                    selects.nth(i).select_option(label=op)
                    encontrou = True
                    print("[DEBUG] PIX Doutores selecionado")
                    break
            if encontrou:
                break

        if not encontrou:
            print("[ERRO] Não encontrou opção PIX Doutores")
            salvar_debug(page, "04_erro_pix")
            return []

    except Exception as e:
        print("[ERRO] Falha no filtro PIX:", e)
        salvar_debug(page, "04_erro_pix")
        return []

    # Buscar
    try:
        possiveis_botoes = [
            'button:has-text("Buscar")',
            'input[value="Buscar"]',
            'text=Buscar'
        ]
        clicou = False
        for seletor in possiveis_botoes:
            try:
                if page.locator(seletor).first.is_visible(timeout=3000):
                    page.locator(seletor).first.click(timeout=5000)
                    print(f"[DEBUG] Clique no Buscar com seletor: {seletor}")
                    clicou = True
                    break
            except Exception:
                continue

        if not clicou:
            print("[ERRO] Não encontrou botão Buscar")
            salvar_debug(page, "05_erro_buscar")
            return []

        page.wait_for_timeout(6000)
    except Exception as e:
        print("[ERRO] Falha ao buscar:", e)
        salvar_debug(page, "05_erro_buscar")
        return []

    salvar_debug(page, "06_resultado")

    # Leitura da tabela
    dados = []
    try:
        linhas = page.locator("table tr")
        total_linhas = linhas.count()
        print("[DEBUG] Linhas encontradas:", total_linhas)

        for i in range(total_linhas):
            try:
                cols = linhas.nth(i).locator("td")
                if cols.count() >= 4:
                    dados.append({
                        "data": cols.nth(0).inner_text().strip(),
                        "unidade": nome,
                        "doutor": cols.nth(1).inner_text().strip(),
                        "metodo": "PIX Doutores",
                        "origem": cols.nth(2).inner_text().strip(),
                        "valor": cols.nth(3).inner_text().strip(),
                        "mes": 3,
                        "ano": 2026
                    })
            except Exception:
                pass

    except Exception as e:
        print("[ERRO] Falha ao ler tabela:", e)
        salvar_debug(page, "07_erro_tabela")

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
