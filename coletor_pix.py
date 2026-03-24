import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeoutError
from unidecode import unidecode


# =========================================================
# CONFIG GERAL
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
CREDITOS_PATH = DATA_DIR / "doutores_credito.json"
OUTPUT_PATH = DATA_DIR / "pix_doutores.json"

load_dotenv(BASE_DIR / "bot" / ".env")

TOP_USER = os.getenv("TOP_USER", "")
TOP_PASS = os.getenv("TOP_PASS", "")

if not TOP_USER or not TOP_PASS:
    raise RuntimeError("Preencha TOP_USER e TOP_PASS no arquivo bot/.env")


@dataclass
class Unidade:
    nome: str
    url: str


UNIDADES = [
    Unidade("Caxias", "http://caxias.topesteticabucal.com.br/sistema"),
    Unidade("Farroupilha", "http://farroupilha.topesteticabucal.com.br/sistema"),
    Unidade("Bento", "http://bento.topesteticabucal.com.br/sistema"),
    Unidade("Encantado", "http://encantado.topesteticabucal.com.br/sistema"),
    Unidade("Soledade", "http://soledade.topesteticabucal.com.br/sistema"),
    Unidade("Garibaldi", "http://garibaldi.topesteticabucal.com.br/sistema"),
    Unidade("Veranópolis", "http://veranopolis.topesteticabucal.com.br/sistema"),
    Unidade("Sobradinho", "http://ssdocai.topesteticabucal.com.br/sistema"),
]

# Se existir uma 9ª unidade real, adicione aqui.
# O seu prompt fala em 9, mas os links enviados eram 8.


# =========================================================
# SELETORES
# AJUSTE ESTES CAMPOS UMA VEZ CONFORME O HTML REAL
# =========================================================

SELECTORS = {
    # Login
    "login_user": 'input[name="usuario"], input[name="login"], input[type="text"]',
    "login_pass": 'input[name="senha"], input[type="password"]',
    "login_button": 'button[type="submit"], input[type="submit"]',

    # Navegação
    "menu_financas": 'text="Finanças"',
    "submenu_demonstrativo": 'text="Demonstrativo de Resultados"',

    # Filtros
    "metodo_pagamento_select": 'select',
    "data_inicial": 'input[name*="data"], input[placeholder*="Data"], input[id*="data"]',
    "data_final": 'input[name*="data"], input[placeholder*="Data"], input[id*="data"]',
    "botao_buscar": 'button:has-text("Buscar"), input[value="Buscar"]',

    # Resultado
    "tabela_resultado": "table",
    "linhas_resultado": "table tbody tr",

    # Se a tabela tiver td fixos, ajuste estes índices no parse_linha
}

# Se houver 2 campos de data separados, o script usa os dois primeiros encontrados.
# Se houver um datepicker customizado, me mande o HTML e eu adapto.


# =========================================================
# MAPEAMENTO DE NOMES
# =========================================================

def carregar_creditos() -> List[dict]:
    with open(CREDITOS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def normalizar(texto: str) -> str:
    return re.sub(r"\s+", " ", unidecode((texto or "").strip().lower()))


def montar_mapa_doutores(creditos: List[dict]) -> Dict[str, str]:
    """
    Cria um mapa com nome normalizado -> nome oficial.
    """
    mapa = {}
    for item in creditos:
        oficial = item["doutor"].strip()
        chave = normalizar(oficial)
        mapa[chave] = oficial

    # Apelidos/variações conhecidas
    aliases = {
        "leticia cauzzi": "Letícia Cauzzi",
        "jessica barreto": "Jéssica Barreto",
        "joao augusto keler": "João Augusto Keler",
        "leticia canabarro sol": "Leticia Canabarro (SOL)",
        "nelson vaccari": "Nelson Vaccari",
        "gustavo lourenco ongaratto": "Gustavo Lourenço Ongaratto",
        "evalda baldissera": "Evalda Baldissera",
    }

    for alias, oficial in aliases.items():
        mapa[normalizar(alias)] = oficial

    return mapa


def identificar_doutor(texto_metodo: str, mapa_doutores: Dict[str, str]) -> Optional[str]:
    """
    Procura o nome do doutor dentro do texto do método.
    A lógica prioriza o maior nome encontrado.
    """
    texto_norm = normalizar(texto_metodo)

    candidatos = []
    for chave_norm, nome_oficial in mapa_doutores.items():
        if chave_norm and chave_norm in texto_norm:
            candidatos.append((len(chave_norm), nome_oficial))

    if not candidatos:
        return None

    candidatos.sort(reverse=True)
    return candidatos[0][1]


# =========================================================
# AUXILIARES DE DATA E VALOR
# =========================================================

def periodo_mes_atual() -> tuple[str, str]:
    hoje = date.today()
    inicio = hoje.replace(day=1)
    if hoje.month == 12:
        fim = hoje.replace(day=31)
    else:
        prox_mes = date(hoje.year + (1 if hoje.month == 12 else 0), 1 if hoje.month == 12 else hoje.month + 1, 1)
        fim = prox_mes.fromordinal(prox_mes.toordinal() - 1)
    return inicio.strftime("%d/%m/%Y"), fim.strftime("%d/%m/%Y")


def parse_data_br(texto: str) -> str:
    texto = texto.strip()
    return datetime.strptime(texto, "%d/%m/%Y").strftime("%Y-%m-%d")


def parse_valor_br(texto: str) -> float:
    texto = texto.replace("R$", "").replace(".", "").replace(",", ".").strip()
    return float(texto)


# =========================================================
# PLAYWRIGHT
# =========================================================

def fazer_login(page: Page, unidade: Unidade) -> None:
    page.goto(unidade.url, wait_until="networkidle", timeout=60000)

    page.locator(SELECTORS["login_user"]).first.fill(TOP_USER)
    page.locator(SELECTORS["login_pass"]).first.fill(TOP_PASS)
    page.locator(SELECTORS["login_button"]).first.click()

    page.wait_for_load_state("networkidle", timeout=60000)


def navegar_para_relatorio(page: Page) -> None:
    page.locator(SELECTORS["menu_financas"]).first.click()
    page.locator(SELECTORS["submenu_demonstrativo"]).first.click()
    page.wait_for_load_state("networkidle", timeout=60000)


def aplicar_filtros(page: Page) -> None:
    data_ini, data_fim = periodo_mes_atual()

    # Método de pagamento
    selects = page.locator(SELECTORS["metodo_pagamento_select"])
    total_selects = selects.count()

    encontrou_pix = False
    for i in range(total_selects):
        try:
            select = selects.nth(i)
            opcoes = select.locator("option").all_inner_texts()
            if any("pix doutores" in normalizar(op) for op in opcoes):
                for op in opcoes:
                    if "pix doutores" in normalizar(op):
                        select.select_option(label=op)
                        encontrou_pix = True
                        break
                if encontrou_pix:
                    break
        except Exception:
            continue

    if not encontrou_pix:
        raise RuntimeError("Não encontrei o seletor/opção 'PIX Doutores'. Ajuste os seletores.")

    # Datas
    campos_data = page.locator(SELECTORS["data_inicial"])
    qtd_datas = campos_data.count()

    if qtd_datas >= 2:
        campos_data.nth(0).fill(data_ini)
        campos_data.nth(1).fill(data_fim)
    else:
        raise RuntimeError("Não encontrei dois campos de data. Ajuste os seletores.")

    page.locator(SELECTORS["botao_buscar"]).first.click()
    page.wait_for_load_state("networkidle", timeout=60000)
    time.sleep(2)


def parse_linha(page: Page, linha, unidade: str, mapa_doutores: Dict[str, str]) -> Optional[dict]:
    """
    Ajuste este parse conforme a ordem real das colunas.
    Exemplo esperado:
      col[0] = Data
      col[1] = Mét. Pag.
      col[2] = Origem
      col[3] = Valor
    """
    colunas = linha.locator("td")
    qtd = colunas.count()

    if qtd < 4:
        return None

    textos = [colunas.nth(i).inner_text().strip() for i in range(qtd)]

    data_txt = textos[0]
    metodo_txt = textos[1]
    origem_txt = textos[2]
    valor_txt = textos[3]

    # Se o nome estiver dentro de um span vermelho, tenta capturar o HTML inteiro
    try:
        html_metodo = colunas.nth(1).inner_html()
        texto_base = re.sub(r"<[^>]+>", " ", html_metodo)
        metodo_para_identificar = re.sub(r"\s+", " ", texto_base).strip()
    except Exception:
        metodo_para_identificar = metodo_txt

    doutor = identificar_doutor(metodo_para_identificar, mapa_doutores)

    if not doutor:
        # Se não identificou, mantém ignorado por enquanto.
        # Pode trocar para "Desconhecido" se quiser auditar.
        return None

    data_iso = parse_data_br(data_txt)
    data_obj = datetime.strptime(data_iso, "%Y-%m-%d")

    return {
        "data": data_iso,
        "unidade": unidade,
        "doutor": doutor,
        "metodo": metodo_txt,
        "origem": origem_txt,
        "valor": parse_valor_br(valor_txt),
        "mes": data_obj.month,
        "ano": data_obj.year,
    }


def coletar_unidade(page: Page, unidade: Unidade, mapa_doutores: Dict[str, str]) -> List[dict]:
    print(f"[INFO] Coletando unidade: {unidade.nome}")

    fazer_login(page, unidade)
    navegar_para_relatorio(page)
    aplicar_filtros(page)

    try:
        page.locator(SELECTORS["tabela_resultado"]).first.wait_for(timeout=20000)
    except PlaywrightTimeoutError:
        print(f"[WARN] Tabela não encontrada em {unidade.nome}")
        return []

    linhas = page.locator(SELECTORS["linhas_resultado"])
    total_linhas = linhas.count()

    resultados = []
    for i in range(total_linhas):
        try:
            item = parse_linha(page, linhas.nth(i), unidade.nome, mapa_doutores)
            if item:
                resultados.append(item)
        except Exception as e:
            print(f"[WARN] Erro ao ler linha {i+1} de {unidade.nome}: {e}")

    print(f"[INFO] {unidade.nome}: {len(resultados)} lançamentos válidos")
    return resultados


# =========================================================
# CONSOLIDAÇÃO
# =========================================================

def deduplicar(registros: List[dict]) -> List[dict]:
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


def salvar_saida(registros: List[dict]) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(registros, f, ensure_ascii=False, indent=2)
    print(f"[OK] Arquivo salvo em: {OUTPUT_PATH}")


# =========================================================
# MAIN
# =========================================================

def main() -> None:
    creditos = carregar_creditos()
    mapa_doutores = montar_mapa_doutores(creditos)

    todos = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(locale="pt-BR")
        page = context.new_page()

        for unidade in UNIDADES:
            try:
                registros = coletar_unidade(page, unidade, mapa_doutores)
                todos.extend(registros)
            except Exception as e:
                print(f"[ERRO] Falha na unidade {unidade.nome}: {e}")

        browser.close()

    consolidados = deduplicar(todos)
    salvar_saida(consolidados)

    print(f"[FIM] Total consolidado: {len(consolidados)} registros")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Execução interrompida pelo usuário.")
        sys.exit(1)
