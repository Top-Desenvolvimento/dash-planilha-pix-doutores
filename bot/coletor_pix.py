from playwright.sync_api import sync_playwright
import json
import os
from datetime import datetime, date
from pathlib import Path

TOP_USER = os.getenv("TOP_USER")
TOP_PASS = os.getenv("TOP_PASS")

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
OUTPUT_PATH = DATA_DIR / "pix_doutores.json"

UNIDADES = [
    ("Caxias", "http://caxias.topesteticabucal.com.br/sistema"),
    # Descomente depois:
    # ("Farroupilha", "http://farroupilha.topesteticabucal.com.br/sistema"),
    # ("Bento", "http://bento.topesteticabucal.com.br/sistema"),
    # ("Encantado", "http://encantado.topesteticabucal.com.br/sistema"),
    # ("Soledade", "http://soledade.topesteticabucal.com.br/sistema"),
    # ("Garibaldi", "http://garibaldi.topesteticabucal.com.br/sistema"),
    # ("Veranópolis", "http://veranopolis.topesteticabucal.com.br/sistema"),
    # ("Sobradinho", "http://ssdocai.topesteticabucal.com.br/sistema"),
]

def salvar_debug(page, nome):
    try:
        with open(f"debug_{nome}.html", "w", encoding="utf-8") as f:
            f.write(page.content())
        page.screenshot(path=f"debug_{nome}.png", full_page=True)
        print(f"[DEBUG] Salvos: debug_{nome}.html e debug_{nome}.png")
    except Exception as e:
        print(f"[WARN] Falha ao salvar debug {nome}: {e}")

def periodo_mes_atual():
    hoje = date.today()
    inicio = hoje.replace(day=1)

    if hoje.month == 12:
        prox = date(hoje.year + 1, 1, 1)
    else:
        prox = date(hoje.year, hoje.month + 1, 1)

    fim = date.fromordinal(prox.toordinal() - 1)
    return inicio.strftime("%d/%m/%Y"), fim.strftime("%d/%m/%Y")

def parse_valor_brl(txt: str) -> float:
    txt = txt.replace("R$", "").replace(".", "").replace(",", ".")
    txt = txt.replace("C", "").replace("D", "").strip()
    return float(txt)

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

    clicou = False
    for seletor in botoes:
        try:
            if page.locator(seletor).first.count() > 0:
                page.locator(seletor).first.click(timeout=5000)
                print(f"[DEBUG] Clique no login com seletor: {seletor}")
                clicou = True
                break
        except Exception:
            continue

    if not clicou:
        page.locator('input[type="password"]').first.press("Enter")
        print("[DEBUG] Login via Enter")

    page.wait_for_timeout(5000)

def navegar_para_demonstrativo(page):
    page.locator("text=FINANÇAS").first.click(timeout=10000)
    print("[DEBUG] Clique em FINANÇAS")
    page.wait_for_timeout(2000)

    opcoes = [
        "text=Demonstrativo de Resultado",
        "text=Demonstrativo de Resultados",
        "a:has-text('Demonstrativo de Resultado')",
        "a:has-text('Demonstrativo de Resultados')"
    ]

    abriu = False
    for seletor in opcoes:
        try:
            if page.locator(seletor).first.count() > 0:
                page.locator(seletor).first.click(timeout=10000)
                print(f"[DEBUG] Clique no demonstrativo com: {seletor}")
                abriu = True
                break
        except Exception:
            continue

    if not abriu:
        raise RuntimeError("Não encontrou 'Demonstrativo de Resultado'.")

    page.wait_for_timeout(4000)

def preencher_periodo(page):
    data_ini, data_fim = periodo_mes_atual()

    preenchidos = 0
    inputs = page.locator("input")
    total = inputs.count()
    print(f"[DEBUG] Quantidade de inputs: {total}")

    for i in range(total):
        try:
            loc = inputs.nth(i)
            tipo = (loc.get_attribute("type") or "").lower()
            valor = ""
            try:
                valor = loc.input_value(timeout=1000)
            except Exception:
                pass

            if tipo in ["text", "date"] or "/" in valor:
                if preenchidos == 0:
                    loc.fill(data_ini)
                    preenchidos += 1
                    print(f"[DEBUG] Data inicial preenchida: {data_ini}")
                elif preenchidos == 1:
                    loc.fill(data_fim)
                    preenchidos += 1
                    print(f"[DEBUG] Data final preenchida: {data_fim}")
                    break
        except Exception:
            continue

    if preenchidos < 2:
        raise RuntimeError("Não conseguiu preencher as datas do período.")

def clicar_buscar(page):
    botoes = [
        "text=Buscar",
        "button:has-text('Buscar')",
        "input[value='Buscar']"
    ]

    for seletor in botoes:
        try:
            if page.locator(seletor).first.count() > 0:
                page.locator(seletor).first.click(timeout=10000)
                print(f"[DEBUG] Clique em Buscar com: {seletor}")
                page.wait_for_timeout(5000)
                return
        except Exception:
            continue

    raise RuntimeError("Não encontrou o botão Buscar.")

def ler_tabela_resultado(page, unidade):
    dados = []

    linhas = page.locator("table tr")
    total_linhas = linhas.count()
    print(f"[DEBUG] Linhas encontradas: {total_linhas}")

    for i in range(total_linhas):
        try:
            linha = linhas.nth(i)
            cols = linha.locator("td")

            if cols.count() < 4:
                continue

            data_txt = cols.nth(0).inner_text().strip()
            metodo_txt = cols.nth(1).inner_text().strip()
            origem_txt = cols.nth(2).inner_text().strip()
            valor_txt = cols.nth(3).inner_text().strip()

            if "/" not in data_txt:
                continue

            try:
                data_obj = datetime.strptime(data_txt, "%d/%m/%Y")
            except Exception:
                continue

            try:
                valor = parse_valor_brl(valor_txt)
            except Exception:
                continue

            dados.append({
                "data": data_obj.strftime("%Y-%m-%d"),
                "unidade": unidade,
                "metodo_raw": metodo_txt,
                "origem": origem_txt,
                "valor": valor,
                "mes": data_obj.month,
                "ano": data_obj.year
            })

        except Exception:
            continue

    return dados

def deduplicar(registros):
    vistos = set()
    saida = []

    for r in registros:
        chave = (
            r["data"],
            r["unidade"],
            r["metodo_raw"],
            r["origem"],
            round(float(r["valor"]), 2),
        )
        if chave not in vistos:
            vistos.add(chave)
            saida.append(r)

    saida.sort(key=lambda x: (x["data"], x["unidade"], x["metodo_raw"], x["valor"]))
    return saida

def coletar_unidade(page, nome_unidade, url):
    print(f"[INFO] Acessando {nome_unidade}")
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(3000)
    salvar_debug(page, f"{nome_unidade}_01_abertura")

    fazer_login(page)
    print("[DEBUG] URL após login:", page.url)
    salvar_debug(page, f"{nome_unidade}_02_pos_login")

    navegar_para_demonstrativo(page)
    salvar_debug(page, f"{nome_unidade}_03_demonstrativo")

    preencher_periodo(page)
    clicar_buscar(page)
    salvar_debug(page, f"{nome_unidade}_04_resultado")

    dados = ler_tabela_resultado(page, nome_unidade)
    print(f"[INFO] {nome_unidade}: {len(dados)} linhas coletadas")
    return dados

def main():
    if not TOP_USER or not TOP_PASS:
        raise RuntimeError("TOP_USER e TOP_PASS não definidos nos Secrets.")

    todos = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for nome_unidade, url in UNIDADES:
            try:
                dados = coletar_unidade(page, nome_unidade, url)
                todos.extend(dados)
            except Exception as e:
                print(f"[ERRO] Unidade {nome_unidade}: {e}")

        browser.close()

    consolidados = deduplicar(todos)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(consolidados, f, indent=2, ensure_ascii=False)

    print(f"✅ Dados coletados: {len(consolidados)}")
    print(f"[DEBUG] Arquivo salvo em: {OUTPUT_PATH}")

    with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
        conteudo = f.read()

    print("[DEBUG] Conteúdo do pix_doutores.json:")
    print(conteudo[:4000])

if __name__ == "__main__":
    main()
