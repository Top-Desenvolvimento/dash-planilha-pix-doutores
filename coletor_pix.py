from playwright.sync_api import sync_playwright
import json
import os
import re
from datetime import datetime, date
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
    # Depois que validar, adicione as demais:
    # ("Farroupilha", "http://farroupilha.topesteticabucal.com.br/sistema"),
    # ("Bento", "http://bento.topesteticabucal.com.br/sistema"),
    # ("Encantado", "http://encantado.topesteticabucal.com.br/sistema"),
    # ("Soledade", "http://soledade.topesteticabucal.com.br/sistema"),
    # ("Garibaldi", "http://garibaldi.topesteticabucal.com.br/sistema"),
    # ("Veranópolis", "http://veranopolis.topesteticabucal.com.br/sistema"),
    # ("Sobradinho", "http://ssdocai.topesteticabucal.com.br/sistema"),
]

def sem_acento(txt: str) -> str:
    return normalize("NFKD", txt).encode("ASCII", "ignore").decode("ASCII")

def normalizar_nome(txt: str) -> str:
    txt = txt or ""
    txt = sem_acento(txt).lower()
    txt = re.sub(r"\b(dr|dra|cir)\.?\b", "", txt)
    txt = re.sub(r"[^a-z0-9\s]", " ", txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt

def carregar_doutores_oficiais():
    if not CREDITOS_PATH.exists():
        return []

    with open(CREDITOS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    return [x["doutor"] for x in data if x.get("ativo", True)]

def mapear_nome_doutor(nome_extraido: str, doutores_oficiais: list[str]) -> str:
    alvo = normalizar_nome(nome_extraido)

    if not alvo:
        return ""

    for oficial in doutores_oficiais:
        if normalizar_nome(oficial) == alvo:
            return oficial

    candidatos = []
    alvo_tokens = set(alvo.split())

    for oficial in doutores_oficiais:
        norm_oficial = normalizar_nome(oficial)
        tokens_oficial = set(norm_oficial.split())

        if tokens_oficial and tokens_oficial.issubset(alvo_tokens):
            candidatos.append((len(tokens_oficial), oficial))

    if candidatos:
        candidatos.sort(reverse=True)
        return candidatos[0][1]

    candidatos = []
    for oficial in doutores_oficiais:
        norm_oficial = normalizar_nome(oficial)
        partes = norm_oficial.split()

        if len(partes) >= 2:
            nome = partes[0]
            sobrenome = partes[-1]
            if nome in alvo_tokens and sobrenome in alvo_tokens:
                candidatos.append((len(partes), oficial))

    if candidatos:
        candidatos.sort(reverse=True)
        return candidatos[0][1]

    return ""

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

def salvar_debug(page, nome):
    try:
        with open(f"debug_{nome}.html", "w", encoding="utf-8") as f:
            f.write(page.content())
        page.screenshot(path=f"debug_{nome}.png", full_page=True)
        print(f"[DEBUG] Salvos: debug_{nome}.html e debug_{nome}.png")
    except Exception as e:
        print(f"[WARN] Falha ao salvar debug {nome}: {e}")

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

def garantir_pix_doutores(page):
    try:
        texto_pagina = page.content().lower()
        if "pix doutores" in texto_pagina:
            print("[DEBUG] Método Pix Doutores encontrado na tela")
            return
    except Exception:
        pass

    raise RuntimeError("Não encontrei 'Pix Doutores' na tela do filtro.")

def configurar_filtros(page):
    data_ini, data_fim = periodo_mes_atual()

    # =========================
    # 1. LIMPAR MÉTODO
    # =========================
    try:
        # clica no X do campo método
        if page.locator("text=Pix Doutores >> xpath=.. >> button").count() > 0:
            page.locator("text=Pix Doutores >> xpath=.. >> button").click()
            print("[DEBUG] Método limpo")
    except:
        pass

    # =========================
    # 2. ABRIR SELECT DE MÉTODO
    # =========================
    try:
        page.locator("text=Método").locator("..").click()
        page.wait_for_timeout(1000)
    except:
        pass

    # =========================
    # 3. SELECIONAR PIX DOUTORES
    # =========================
    try:
        page.locator("text=Pix Doutores").last.click()
        print("[DEBUG] Pix Doutores selecionado")
    except Exception as e:
        print("[ERRO] Não conseguiu selecionar Pix Doutores:", e)

    # =========================
    # 4. PREENCHER DATAS
    # =========================
    inputs = page.locator("input")
    preenchidos = 0

    for i in range(inputs.count()):
        try:
            loc = inputs.nth(i)
            valor = loc.input_value(timeout=1000)

            if "/" in valor or loc.get_attribute("type") in ["text", "date"]:
                if preenchidos == 0:
                    loc.fill(data_ini)
                    preenchidos += 1
                elif preenchidos == 1:
                    loc.fill(data_fim)
                    break
        except:
            continue

    print(f"[DEBUG] Período: {data_ini} até {data_fim}")
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

def extrair_nome_vermelho(col_metodo, doutores_oficiais):
    """
    Usa as linhas da célula Mét. Pag.
    Exemplo esperado:
      Pix Doutores
      CIR.Dionathan Paim Pohlmann
    Só aceita se conseguir mapear para um doutor oficial.
    """
    try:
        bruto = col_metodo.inner_text().strip()
    except Exception:
        return ""

    linhas = [x.strip() for x in bruto.splitlines() if x.strip()]

    linhas_sem_pix = [
        linha for linha in linhas
        if "pix doutores" not in linha.lower()
    ]

    for linha in linhas_sem_pix:
        nome_limpo = re.sub(r"^(CIR\.?|DRA\.?|DR\.?)\s*", "", linha, flags=re.I)
        nome_limpo = re.sub(r"\s+", " ", nome_limpo).strip()

        invalido = [
            "dinheiro", "saldo total", "maquina", "máquina",
            "cartao", "cartão", "pix", "debito", "débito",
            "credito", "crédito", "boleto", "transferencia",
            "transferência", "deposito", "depósito"
        ]
        if any(p in nome_limpo.lower() for p in invalido):
            continue

        nome_mapeado = mapear_nome_doutor(nome_limpo, doutores_oficiais)
        if nome_mapeado:
            return nome_mapeado

    return ""

def ler_tabela_resultado(page, unidade, doutores_oficiais):
    dados = []

    linhas = page.locator("table tr")
    total_linhas = linhas.count()
    print(f"[DEBUG] Linhas encontradas: {total_linhas}")

    for i in range(total_linhas):
        try:
            linha = linhas.nth(i)
            cols = linha.locator("td")
            qtd = cols.count()

            if qtd < 4:
                continue

            data_txt = cols.nth(0).inner_text().strip()
            if "/" not in data_txt:
                continue

            col_metodo = cols.nth(1)
            col_origem = cols.nth(2)
            col_valor = cols.nth(3)

            metodo_txt = col_metodo.inner_text().strip()
            origem_txt = col_origem.inner_text().strip()
            valor_txt = col_valor.inner_text().strip()

            if "pix doutores" not in metodo_txt.lower():
                continue

            doutor = extrair_nome_vermelho(col_metodo, doutores_oficiais)
            if not doutor:
                print(f"[DEBUG] Linha ignorada sem doutor válido: {metodo_txt}")
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
                "doutor": doutor,
                "metodo": "PIX Doutores",
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
            r["doutor"],
            r["origem"],
            round(float(r["valor"]), 2),
        )
        if chave not in vistos:
            vistos.add(chave)
            saida.append(r)

    saida.sort(key=lambda x: (x["data"], x["unidade"], x["doutor"], x["valor"]))
    return saida

def coletar_unidade(page, nome_unidade, url, doutores_oficiais):
    print(f"[INFO] Acessando {nome_unidade}")
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(3000)
    salvar_debug(page, f"{nome_unidade}_01_abertura")

    fazer_login(page)
    print("[DEBUG] URL após login:", page.url)
    salvar_debug(page, f"{nome_unidade}_02_pos_login")

    navegar_para_demonstrativo(page)
    salvar_debug(page, f"{nome_unidade}_03_demonstrativo")

    garantir_pix_doutores(page)
    preencher_periodo(page)
    clicar_buscar(page)
    salvar_debug(page, f"{nome_unidade}_04_resultado")

    dados = ler_tabela_resultado(page, nome_unidade, doutores_oficiais)
    print(f"[INFO] {nome_unidade}: {len(dados)} registros válidos")
    return dados

def main():
    if not TOP_USER or not TOP_PASS:
        raise RuntimeError("TOP_USER e TOP_PASS não definidos nos Secrets.")

    doutores_oficiais = carregar_doutores_oficiais()
    todos = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for nome_unidade, url in UNIDADES:
            try:
                dados = coletar_unidade(page, nome_unidade, url, doutores_oficiais)
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
