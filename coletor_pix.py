from playwright.sync_api import sync_playwright
import json
import os
from datetime import datetime, date

TOP_USER = os.getenv("TOP_USER")
TOP_PASS = os.getenv("TOP_PASS")

UNIDADES = [
    ("Caxias", "http://caxias.topesteticabucal.com.br/sistema"),
    # Depois que validar, adicione as demais:
    # ("Farroupilha", "http://farroupilha.topesteticabucal.com.br/sistema"),
    # ("Bento", "http://bento.topesteticabucal.com.br/sistema"),
    # ("Encantado", "http://encantado.topesteticabucal.com.br/sistema"),
    # ("Soledade", "http://soledade.topesteticabucal.com.br/sistema"),
    # ("Garibaldi", "http://garibaldi.topesteticabucal.com.br/sistema"),
    # ("Veranópolis", "http://veranopolis.topesteticabucal.com.br/sistema"),
    # ("Sobradinho", "http://ssdocai.topesteticabucal.com.br/sistema"),
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

    raise RuntimeError("Não encontrou um botão de login válido.")

def periodo_mes_atual():
    hoje = date.today()
    inicio = hoje.replace(day=1)

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

def encontrar_select_responsavel(page):
    # Pelo seu log validado:
    # Select 1 = Responsável Fiscal
    print("[DEBUG] Usando select fixo de Responsável Fiscal: índice 1")
    return 1

def listar_responsaveis(page, idx_select):
    select = page.locator("select").nth(idx_select)
    opcoes = select.locator("option").all_inner_texts()

    ignorar = {
        "",
        "todos",
        "selecione",
        "selecionar",
        "responsável fiscal",
        "responsavel fiscal"
    }

    validas = []
    for op in opcoes:
        texto = op.strip()
        if texto.lower() not in ignorar:
            validas.append(texto)

    print(f"[DEBUG] Responsáveis encontrados: {len(validas)}")
    print("[DEBUG] Lista:", validas)
    return validas

def preencher_datas_mes(page):
    data_ini, data_fim = periodo_mes_atual()
    inputs = page.locator('input[type="text"], input[type="date"]')
    total_inputs = inputs.count()
    print("[DEBUG] Quantidade de inputs:", total_inputs)

    preenchidos = 0
    for i in range(total_inputs):
        try:
            name = (inputs.nth(i).get_attribute("name") or "").lower()
            id_attr = (inputs.nth(i).get_attribute("id") or "").lower()
            placeholder = (inputs.nth(i).get_attribute("placeholder") or "").lower()

            ref = f"{name} {id_attr} {placeholder}"
            print(f"[DEBUG] Input {i}: name={name} id={id_attr} placeholder={placeholder}")

            if "data" in ref or "periodo" in ref or "período" in ref:
                if preenchidos == 0:
                    inputs.nth(i).fill(data_ini)
                    preenchidos += 1
                    print(f"[DEBUG] Data inicial preenchida: {data_ini}")
                elif preenchidos == 1:
                    inputs.nth(i).fill(data_fim)
                    preenchidos += 1
                    print(f"[DEBUG] Data final preenchida: {data_fim}")
                    break
        except Exception:
            continue

    if preenchidos < 2 and total_inputs >= 2:
        try:
            inputs.nth(0).fill(data_ini)
            inputs.nth(1).fill(data_fim)
            preenchidos = 2
            print("[DEBUG] Datas preenchidas por fallback")
        except Exception:
            pass

    if preenchidos < 2:
        raise RuntimeError("Não conseguiu preencher as datas do período")

def clicar_buscar(page):
    botoes = [
        'button:has-text("Buscar")',
        'input[value="Buscar"]',
        'text=Buscar'
    ]

    for seletor in botoes:
        try:
            if page.locator(seletor).first.count() > 0:
                page.locator(seletor).first.click(timeout=5000)
                print(f"[DEBUG] Buscar clicado com: {seletor}")
                page.wait_for_timeout(5000)
                return
        except Exception:
            continue

    raise RuntimeError("Não encontrou o botão Buscar")

def parse_valor(valor_txt):
    return float(
        valor_txt.replace("R$", "")
        .replace(".", "")
        .replace(",", ".")
        .strip()
    )

def ler_tabela(page, unidade, responsavel):
    dados = []
    linhas = page.locator("table tr")
    total_linhas = linhas.count()
    print(f"[DEBUG] Linhas encontradas para {responsavel}: {total_linhas}")

    for i in range(total_linhas):
        try:
            cols = linhas.nth(i).locator("td")
            qtd_cols = cols.count()

            if qtd_cols < 4:
                continue

            textos = [cols.nth(j).inner_text().strip() for j in range(qtd_cols)]

            data_txt = textos[0]
            metodo_txt = textos[1]
            origem_txt = textos[2]
            valor_txt = textos[3]

            if "/" not in data_txt:
                continue

            try:
                data_obj = datetime.strptime(data_txt, "%d/%m/%Y")
                valor_num = parse_valor(valor_txt)
            except Exception:
                continue

            dados.append({
                "data": data_obj.strftime("%Y-%m-%d"),
                "unidade": unidade,
                "doutor": responsavel,
                "metodo": metodo_txt,
                "origem": origem_txt,
                "valor": valor_num,
                "mes": data_obj.month,
                "ano": data_obj.year
            })
        except Exception:
            continue

    return dados

def coletar_por_responsavel(page, unidade):
    preencher_datas_mes(page)

    idx_select = encontrar_select_responsavel(page)
    responsaveis = listar_responsaveis(page, idx_select)

    todos = []
    select = page.locator("select").nth(idx_select)

    for nome_resp in responsaveis:
        try:
            print(f"[INFO] Coletando responsável: {nome_resp}")
            select.select_option(label=nome_resp)
            page.wait_for_timeout(1000)

            clicar_buscar(page)
            page.wait_for_timeout(3000)

            dados_resp = ler_tabela(page, unidade, nome_resp)
            print(f"[DEBUG] Registros coletados para {nome_resp}: {len(dados_resp)}")
            todos.extend(dados_resp)
        except Exception as e:
            print(f"[ERRO] Falha ao coletar {nome_resp}: {e}")

    return todos

def deduplicar(registros):
    vistos = set()
    saida = []

    for r in registros:
        chave = (
            r["data"],
            r["unidade"],
            r["doutor"],
            r["metodo"],
            r["origem"],
            round(float(r["valor"]), 2),
        )
        if chave not in vistos:
            vistos.add(chave)
            saida.append(r)

    saida.sort(key=lambda x: (x["data"], x["unidade"], x["doutor"], x["valor"]))
    return saida

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

    dados = coletar_por_responsavel(page, nome)
    salvar_debug(page, "04_resultado_final")

    return dados

def main():
    if not TOP_USER or not TOP_PASS:
        raise RuntimeError("TOP_USER e TOP_PASS não definidos nos Secrets.")

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

    consolidados = deduplicar(todos)

    with open("data/pix_doutores.json", "w", encoding="utf-8") as f:
        json.dump(consolidados, f, indent=2, ensure_ascii=False)

    print("✅ Dados coletados:", len(consolidados))

if __name__ == "__main__":
    main()
