from playwright.sync_api import sync_playwright
import json
import os
from datetime import datetime, date

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

def periodo_mes_atual():
    hoje = date.today()
    inicio = hoje.replace(day=1)
    if hoje.month == 12:
        fim = hoje.replace(day=31)
    else:
        if hoje.month == 12:
            prox = date(hoje.year + 1, 1, 1)
        else:
            prox = date(hoje.year, hoje.month + 1, 1)
        fim = date.fromordinal(prox.toordinal() - 1)
    return inicio.strftime("%d/%m/%Y"), fim.strftime("%d/%m/%Y")

def navegar_relatorio(page):
    print("[DEBUG] Tentando abrir Finanças")
    opcoes_financas = [
        'text=Finanças',
        'text=Financas',
        'a:has-text("Finanças")',
        'a:has-text("Financas")'
    ]

    clicou_financas = False
    for seletor in opcoes_financas:
        try:
            if page.locator(seletor).first.count() > 0:
                page.locator(seletor).first.click(timeout=5000)
                clicou_financas = True
                print(f"[DEBUG] Finanças clicado com: {seletor}")
                break
        except Exception:
            continue

    if not clicou_financas:
        raise RuntimeError("Não encontrou o menu Finanças")

    page.wait_for_timeout(3000)

    print("[DEBUG] Tentando abrir Demonstrativo de Resultados")
    opcoes_demo = [
        'text=Demonstrativo de Resultados',
        'a:has-text("Demonstrativo de Resultados")',
        'text=Demonstrativo'
    ]

    clicou_demo = False
    for seletor in opcoes_demo:
        try:
            if page.locator(seletor).first.count() > 0:
                page.locator(seletor).first.click(timeout=5000)
                clicou_demo = True
                print(f"[DEBUG] Demonstrativo clicado com: {seletor}")
                break
        except Exception:
            continue

    if not clicou_demo:
        raise RuntimeError("Não encontrou Demonstrativo de Resultados")

    page.wait_for_timeout(5000)

def aplicar_filtros(page):
    data_ini, data_fim = periodo_mes_atual()

    print("[DEBUG] Procurando selects")
    selects = page.locator("select")
    total_selects = selects.count()
    print("[DEBUG] Quantidade de selects:", total_selects)

    encontrou_pix = False
    for i in range(total_selects):
        try:
            opcoes = selects.nth(i).locator("option").all_inner_texts()
            print(f"[DEBUG] Select {i}: {opcoes}")
            for op in opcoes:
                if "pix doutores" in op.lower():
                    selects.nth(i).select_option(label=op)
                    encontrou_pix = True
                    print("[DEBUG] PIX Doutores selecionado")
                    break
            if encontrou_pix:
                break
        except Exception:
            continue

    if not encontrou_pix:
        raise RuntimeError("Não encontrou a opção PIX Doutores")

    print("[DEBUG] Preenchendo datas")
    inputs = page.locator('input[type="text"], input[type="date"]')
    total_inputs = inputs.count()
    print("[DEBUG] Quantidade de inputs:", total_inputs)

    datas_preenchidas = 0
    for i in range(total_inputs):
        try:
            valor_atual = inputs.nth(i).input_value(timeout=1000)
            placeholder = inputs.nth(i).get_attribute("placeholder") or ""
            name = inputs.nth(i).get_attribute("name") or ""
            id_attr = inputs.nth(i).get_attribute("id") or ""

            campo_info = f"name={name} id={id_attr} placeholder={placeholder}"
            print(f"[DEBUG] Input {i}: {campo_info}")

            texto_ref = f"{name} {id_attr} {placeholder}".lower()
            if "data" in texto_ref or "/" in valor_atual or valor_atual == "":
                if datas_preenchidas == 0:
                    inputs.nth(i).fill(data_ini)
                    datas_preenchidas += 1
                elif datas_preenchidas == 1:
                    inputs.nth(i).fill(data_fim)
                    datas_preenchidas += 1
                    break
        except Exception:
            continue

    print(f"[DEBUG] Datas preenchidas: {datas_preenchidas}")

    print("[DEBUG] Procurando botão Buscar")
    botoes = [
        'button:has-text("Buscar")',
        'input[value="Buscar"]',
        'text=Buscar'
    ]

    clicou_buscar = False
    for seletor in botoes:
        try:
            if page.locator(seletor).first.count() > 0:
                page.locator(seletor).first.click(timeout=5000)
                clicou_buscar = True
                print(f"[DEBUG] Buscar clicado com: {seletor}")
                break
        except Exception:
            continue

    if not clicou_buscar:
        raise RuntimeError("Não encontrou o botão Buscar")

    page.wait_for_timeout(6000)

def ler_tabela(page, unidade):
    dados = []
    linhas = page.locator("table tr")
    total_linhas = linhas.count()
    print("[DEBUG] Linhas encontradas na tabela:", total_linhas)

    for i in range(total_linhas):
        try:
            cols = linhas.nth(i).locator("td")
            if cols.count() >= 4:
                data_txt = cols.nth(0).inner_text().strip()
                metodo_txt = cols.nth(1).inner_text().strip()
                origem_txt = cols.nth(2).inner_text().strip()
                valor_txt = cols.nth(3).inner_text().strip()

                if not data_txt or "data" in data_txt.lower():
                    continue

                try:
                    data_obj = datetime.strptime(data_txt, "%d/%m/%Y")
                    valor_num = float(
                        valor_txt.replace("R$", "").replace(".", "").replace(",", ".").strip()
                    )
                except Exception:
                    continue

                dados.append({
                    "data": data_obj.strftime("%Y-%m-%d"),
                    "unidade": unidade,
                    "doutor": metodo_txt,
                    "metodo": metodo_txt,
                    "origem": origem_txt,
                    "valor": valor_num,
                    "mes": data_obj.month,
                    "ano": data_obj.year
                })
        except Exception:
            continue

    return dados

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

    navegar_relatorio(page)
    salvar_debug(page, "03_relatorio")

    aplicar_filtros(page)
    salvar_debug(page, "04_resultado")

    dados = ler_tabela(page, nome)
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
