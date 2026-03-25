from playwright.sync_api import sync_playwright
import json
import os
from datetime import datetime
from pathlib import Path

TOP_USER = os.getenv("TOP_USER")
TOP_PASS = os.getenv("TOP_PASS")

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
OUTPUT_PATH = DATA_DIR / "pix_doutores.json"

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

# Período fixo solicitado
DATA_INICIAL = "01/03/2026"
DATA_FINAL = "31/03/2026"


def salvar_debug(page, nome):
    try:
        with open(f"debug_{nome}.html", "w", encoding="utf-8") as f:
            f.write(page.content())
        page.screenshot(path=f"debug_{nome}.png", full_page=True)
        print(f"[DEBUG] Salvos: debug_{nome}.html e debug_{nome}.png")
    except Exception as e:
        print(f"[WARN] Falha ao salvar debug {nome}: {e}")


def parse_valor_brl(txt: str) -> float:
    txt = txt.replace("R$", "").replace(".", "").replace(",", ".")
    txt = txt.replace("C", "").replace("D", "").strip()
    return float(txt)


def classificar_metodo(metodo_raw: str) -> str:
    txt = (metodo_raw or "").lower()

    if "pix doutores" in txt:
        return "PIX Doutores"
    if "pix" in txt:
        return "PIX"
    if "cart" in txt or "credito" in txt or "crédito" in txt or "debito" in txt or "débito" in txt:
        return "Cartão"
    if "dinheiro" in txt:
        return "Dinheiro"
    if "boleto" in txt:
        return "Boleto"
    if "transfer" in txt or "deposito" in txt or "depósito" in txt:
        return "Transferência/Depósito"

    return "Outros"


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


def selecionar_pix_doutores(page):
    """
    Tenta selecionar PIX Doutores no campo Método.
    Como esse campo costuma ser multiselect custom, a estratégia é:
    - abrir o campo
    - digitar Pix Doutores
    - Enter
    """
    print("[DEBUG] Tentando selecionar PIX Doutores no campo Método")

    tentativas_abertura = [
        'text=Selecione um ou mais métodos',
        'text=Selecione um ou mais metodos',
        'text=Método',
        'text=Metodo',
        'text=Pix Doutores'
    ]

    abriu = False
    for seletor in tentativas_abertura:
        try:
            if page.locator(seletor).count() > 0:
                page.locator(seletor).last.click(timeout=4000)
                page.wait_for_timeout(800)
                print(f"[DEBUG] Campo Método aberto com: {seletor}")
                abriu = True
                break
        except Exception:
            continue

    if not abriu:
        print("[WARN] Não consegui abrir claramente o campo Método; tentando digitação mesmo assim")

    # tenta usar algum input visível do multiselect
    inputs = page.locator("input")
    total_inputs = inputs.count()

    for i in range(total_inputs):
        try:
            campo = inputs.nth(i)
            campo.click(timeout=2000)
            page.wait_for_timeout(300)
            campo.fill("Pix Doutores")
            page.wait_for_timeout(800)
            page.keyboard.press("Enter")
            page.wait_for_timeout(1000)
            print(f"[DEBUG] Tentativa de seleção PIX Doutores no input {i}")
            return
        except Exception:
            continue

    print("[WARN] Não consegui forçar a seleção de PIX Doutores. O robô vai seguir com o filtro visual atual da tela.")


def preencher_periodo(page):
    inputs = page.locator("input")
    total = inputs.count()
    print(f"[DEBUG] Quantidade de inputs: {total}")

    preenchidos = 0
    for i in range(total):
        try:
            loc = inputs.nth(i)
            tipo = (loc.get_attribute("type") or "").lower()

            valor_atual = ""
            try:
                valor_atual = loc.input_value(timeout=1000)
            except Exception:
                pass

            if tipo in ["text", "date"] or "/" in valor_atual:
                if preenchidos == 0:
                    loc.fill(DATA_INICIAL)
                    preenchidos += 1
                    print(f"[DEBUG] Data inicial preenchida: {DATA_INICIAL}")
                elif preenchidos == 1:
                    loc.fill(DATA_FINAL)
                    preenchidos += 1
                    print(f"[DEBUG] Data final preenchida: {DATA_FINAL}")
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
                valor_num = parse_valor_brl(valor_txt)
            except Exception:
                continue

            dados.append({
                "data": data_obj.strftime("%Y-%m-%d"),
                "unidade": unidade,
                "metodo_raw": metodo_txt,
                "metodo_categoria": classificar_metodo(metodo_txt),
                "origem": origem_txt,
                "valor": valor_num,
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

    selecionar_pix_doutores(page)
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
