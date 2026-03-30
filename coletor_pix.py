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
    # Depois que validar, descomente as demais:
    # ("Farroupilha", "http://farroupilha.topesteticabucal.com.br/sistema"),
    # ("Bento", "http://bento.topesteticabucal.com.br/sistema"),
    # ("Encantado", "http://encantado.topesteticabucal.com.br/sistema"),
    # ("Soledade", "http://soledade.topesteticabucal.com.br/sistema"),
    # ("Garibaldi", "http://garibaldi.topesteticabucal.com.br/sistema"),
    # ("Veranópolis", "http://veranopolis.topesteticabucal.com.br/sistema"),
    # ("Sobradinho", "http://ssdocai.topesteticabucal.com.br/sistema"),
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
        print(f"[DEBUG] Salvos: debug_{nome}.html e debug_{nome}.png")
    except Exception as e:
        print(f"[WARN] Falha ao salvar debug {nome}: {e}")


def parse_valor_brl(txt: str) -> float:
    txt = str(txt).replace("R$", "").replace(".", "").replace(",", ".")
    txt = txt.replace("C", "").replace("D", "").strip()
    return float(txt)


def sem_acento(txt: str) -> str:
    return normalize("NFKD", txt).encode("ASCII", "ignore").decode("ASCII")


def normalizar_nome(txt: str) -> str:
    txt = txt or ""
    txt = sem_acento(txt).lower()
    txt = re.sub(r"\b(dr|dra|cir)\.?\b", "", txt)
    txt = re.sub(r"[^a-z0-9\s]", " ", txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


def carregar_doutores_credito():
    if not CREDITOS_PATH.exists():
        return []

    with open(CREDITOS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def mapear_nome_doutor(nome_extraido: str, creditos: list[dict]) -> str | None:
    """
    Recebe o nome bruto vindo da tela e tenta casar com o nome oficial
    do arquivo doutores_credito.json.
    """
    alvo = normalizar_nome(nome_extraido)
    if not alvo:
        return None

    nomes_oficiais = [c["doutor"] for c in creditos if c.get("ativo", True)]

    # 1) Match exato normalizado
    for oficial in nomes_oficiais:
        if normalizar_nome(oficial) == alvo:
            return oficial

    alvo_tokens = set(alvo.split())

    # 2) Todos os tokens do oficial contidos no nome extraído
    candidatos = []
    for oficial in nomes_oficiais:
        norm_oficial = normalizar_nome(oficial)
        tokens_oficial = set(norm_oficial.split())
        if tokens_oficial and tokens_oficial.issubset(alvo_tokens):
            candidatos.append((len(tokens_oficial), oficial))

    if candidatos:
        candidatos.sort(reverse=True)
        return candidatos[0][1]

    # 3) Primeiro e último nome batendo
    candidatos = []
    for oficial in nomes_oficiais:
        norm_oficial = normalizar_nome(oficial)
        partes = norm_oficial.split()
        if len(partes) >= 2:
            primeiro = partes[0]
            ultimo = partes[-1]
            if primeiro in alvo_tokens and ultimo in alvo_tokens:
                candidatos.append((len(partes), oficial))

    if candidatos:
        candidatos.sort(reverse=True)
        return candidatos[0][1]

    return None


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


def extrair_nome_doutor_do_metodo(metodo_raw: str, creditos: list[dict]) -> tuple[str | None, str | None]:
    """
    Procura dentro do texto do método a linha que contém o nome do doutor.
    """
    if not metodo_raw:
        return None, None

    linhas = [x.strip() for x in metodo_raw.splitlines() if x.strip()]

    linhas_sem_pix = [
        linha for linha in linhas
        if "pix doutores" not in linha.lower()
    ]

    invalidos = [
        "dinheiro", "saldo total", "maquina", "máquina",
        "cartao", "cartão", "pix", "debito", "débito",
        "credito", "crédito", "boleto", "transferencia",
        "transferência", "deposito", "depósito"
    ]

    for linha in linhas_sem_pix:
        nome_limpo = re.sub(r"^(CIR\.?|DRA\.?|DR\.?)\s*", "", linha, flags=re.I)
        nome_limpo = re.sub(r"\s+", " ", nome_limpo).strip()

        if not nome_limpo:
            continue

        if any(inv in nome_limpo.lower() for inv in invalidos):
            continue

        nome_oficial = mapear_nome_doutor(nome_limpo, creditos)
        return nome_oficial, nome_limpo

    return None, None


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


def limpar_multiselect(page, rotulo):
    try:
        linha = page.locator(f"text={rotulo}").first.locator("xpath=ancestor::tr[1] | xpath=ancestor::div[1]")
        botoes_x = linha.locator("text=×")
        total = botoes_x.count()
        for _ in range(total):
            try:
                botoes_x.nth(0).click(timeout=1000)
                page.wait_for_timeout(300)
            except Exception:
                pass
    except Exception:
        pass


def selecionar_pix_doutores(page):
    print("[DEBUG] Selecionando Método = Pix Doutores")

    limpar_multiselect(page, "Método:")
    page.wait_for_timeout(500)

    linha_metodo = None
    tentativas_linha = [
        "text=Método:",
        "text=Metodo:",
        "text=Método",
        "text=Metodo"
    ]

    for t in tentativas_linha:
        try:
            if page.locator(t).count() > 0:
                linha_metodo = page.locator(t).first.locator("xpath=ancestor::tr[1] | xpath=ancestor::div[1]")
                break
        except Exception:
            continue

    if linha_metodo is None:
        print("[WARN] Não encontrei claramente a linha do campo Método. Vou seguir mesmo assim.")
        return

    clicou = False
    candidatos_click = [
        linha_metodo.locator("input").first,
        linha_metodo.locator("div").nth(1),
        linha_metodo.locator("span").last,
        linha_metodo
    ]

    for loc in candidatos_click:
        try:
            loc.click(timeout=3000)
            page.wait_for_timeout(700)
            clicou = True
            print("[DEBUG] Campo Método aberto")
            break
        except Exception:
            continue

    if not clicou:
        print("[WARN] Não consegui abrir o campo Método. Vou seguir mesmo assim.")
        return

    digitou = False
    inputs = page.locator("input")
    total_inputs = inputs.count()

    for i in range(total_inputs):
        try:
            inp = inputs.nth(i)
            if not inp.is_visible():
                continue

            inp.click(timeout=1000)
            page.wait_for_timeout(200)

            try:
                inp.fill("")
            except Exception:
                pass

            inp.type("Pix Doutores", delay=40)
            page.wait_for_timeout(800)
            page.keyboard.press("Enter")
            page.wait_for_timeout(1200)
            digitou = True
            print(f"[DEBUG] Pix Doutores digitado no input {i}")
            break
        except Exception:
            continue

    if not digitou:
        print("[WARN] Não consegui digitar Pix Doutores no campo Método.")
        return

    try:
        html_linha = linha_metodo.inner_text().lower()
        if "pix doutores" in html_linha:
            print("[DEBUG] Método Pix Doutores selecionado com sucesso")
        else:
            print("[WARN] Não consegui confirmar visualmente a seleção de Pix Doutores")
    except Exception:
        pass


def preencher_periodo(page):
    print("[DEBUG] Preenchendo Período")

    linha_periodo = None
    tentativas = [
        "text=Período:",
        "text=Periodo:",
        "text=Período",
        "text=Periodo"
    ]

    for t in tentativas:
        try:
            if page.locator(t).count() > 0:
                linha_periodo = page.locator(t).first.locator("xpath=ancestor::tr[1] | xpath=ancestor::div[1]")
                break
        except Exception:
            continue

    if linha_periodo is None:
        raise RuntimeError("Não encontrei a linha do campo Período.")

    inputs_visiveis = []
    inputs = linha_periodo.locator("input")
    total = inputs.count()

    for i in range(total):
        try:
            inp = inputs.nth(i)
            if inp.is_visible():
                inputs_visiveis.append(inp)
        except Exception:
            continue

    if len(inputs_visiveis) < 2:
        raise RuntimeError(f"Encontrei apenas {len(inputs_visiveis)} input(s) no Período.")

    inp_ini = inputs_visiveis[0]
    inp_fim = inputs_visiveis[1]

    inp_ini.click()
    inp_ini.fill(DATA_INICIAL)
    page.wait_for_timeout(300)

    inp_fim.click()
    inp_fim.fill(DATA_FINAL)
    page.wait_for_timeout(300)

    val_ini = inp_ini.input_value()
    val_fim = inp_fim.input_value()

    print(f"[DEBUG] Data inicial preenchida: {val_ini}")
    print(f"[DEBUG] Data final preenchida: {val_fim}")

    if val_ini != DATA_INICIAL or val_fim != DATA_FINAL:
        raise RuntimeError(f"Período não confirmado. Inicial={val_ini} Final={val_fim}")


def clicar_buscar(page):
    print("[DEBUG] Clicando em Buscar")
    botoes = [
        page.locator("text=Buscar").first,
        page.locator("button:has-text('Buscar')").first,
        page.locator("input[value='Buscar']").first
    ]

    clicou = False
    for botao in botoes:
        try:
            if botao.count() > 0:
                botao.click(timeout=5000)
                clicou = True
                break
        except Exception:
            continue

    if not clicou:
        raise RuntimeError("Não encontrei o botão Buscar.")

    page.wait_for_timeout(5000)
    print("[DEBUG] Busca executada")


def ler_tabela_resultado(page, unidade, creditos):
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

            if "pix doutores" not in metodo_txt.lower():
                continue

            doutor_oficial, doutor_bruto = extrair_nome_doutor_do_metodo(metodo_txt, creditos)

            dados.append({
                "data": data_obj.strftime("%Y-%m-%d"),
                "unidade": unidade,
                "metodo_raw": metodo_txt,
                "metodo_categoria": classificar_metodo(metodo_txt),
                "origem": origem_txt,
                "valor": valor_num,
                "mes": data_obj.month,
                "ano": data_obj.year,
                "doutor": doutor_oficial,
                "doutor_bruto": doutor_bruto,
                "casado_credito": bool(doutor_oficial)
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


def montar_resumo_por_doutor(registros, creditos):
    """
    Usa o crédito do doutores_credito.json como saldo atual/base
    e desconta o total de PIX Doutores do mês.
    """
    creditos_ativos = [c for c in creditos if c.get("ativo", True)]

    totais_pix = {}
    nao_mapeados = []

    for r in registros:
        doutor = r.get("doutor")
        valor = float(r.get("valor", 0) or 0)

        if not doutor:
            nao_mapeados.append({
                "data": r.get("data"),
                "unidade": r.get("unidade"),
                "doutor_bruto": r.get("doutor_bruto"),
                "metodo_raw": r.get("metodo_raw"),
                "origem": r.get("origem"),
                "valor": round(valor, 2)
            })
            continue

        totais_pix[doutor] = totais_pix.get(doutor, 0) + valor

    saldos_ajustados = {}
    for item in creditos_ativos:
        doutor = item["doutor"]
        credito_base = float(item.get("credito", 0) or 0)
        total_pix_mes = float(totais_pix.get(doutor, 0) or 0)
        saldo_ajustado = credito_base - total_pix_mes

        saldos_ajustados[doutor] = {
            "credito_base": round(credito_base, 2),
            "total_pix_mes": round(total_pix_mes, 2),
            "saldo_ajustado": round(saldo_ajustado, 2)
        }

    return totais_pix, saldos_ajustados, nao_mapeados


def coletar_unidade(page, nome_unidade, url, creditos):
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
    salvar_debug(page, f"{nome_unidade}_03b_filtros_preenchidos")

    clicar_buscar(page)
    salvar_debug(page, f"{nome_unidade}_04_resultado")

    dados = ler_tabela_resultado(page, nome_unidade, creditos)
    print(f"[INFO] {nome_unidade}: {len(dados)} linhas PIX Doutores coletadas")
    return dados


def main():
    if not TOP_USER or not TOP_PASS:
        raise RuntimeError("TOP_USER e TOP_PASS não definidos nos Secrets/Variables.")

    creditos = carregar_doutores_credito()
    if not creditos:
        raise RuntimeError(f"Arquivo não encontrado ou vazio: {CREDITOS_PATH}")

    todos = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for nome_unidade, url in UNIDADES:
            try:
                dados = coletar_unidade(page, nome_unidade, url, creditos)
                todos.extend(dados)
            except Exception as e:
                print(f"[ERRO] Unidade {nome_unidade}: {e}")

        browser.close()

    consolidados = deduplicar(todos)
    totais_pix, saldos_ajustados, nao_mapeados = montar_resumo_por_doutor(consolidados, creditos)

    saida = {
        "periodo": {
            "data_inicial": DATA_INICIAL,
            "data_final": DATA_FINAL
        },
        "resumo": {
            "quantidade_lancamentos": len(consolidados),
            "total_geral_pix_doutores": round(sum(float(r["valor"]) for r in consolidados), 2)
        },
        "totais_pix_por_doutor": {
            doutor: round(valor, 2) for doutor, valor in sorted(totais_pix.items())
        },
        "saldos_ajustados": saldos_ajustados,
        "nao_mapeados": nao_mapeados,
        "lancamentos": consolidados
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(saida, f, indent=2, ensure_ascii=False)

    print(f"✅ Dados coletados e resumidos: {len(consolidados)}")
    print(f"[DEBUG] Arquivo salvo em: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
