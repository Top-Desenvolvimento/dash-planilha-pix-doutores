from __future__ import annotations

import calendar
import json
import re
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from regras_doutores import montar_mapa_creditos, aplicar_desconto, listar_saldos_finais


USUARIO = "MANUS"
SENHA = "MANUS2026"

SISTEMAS = [
    {"unidade": "Caxias", "url": "http://caxias.topesteticabucal.com.br/sistema"},
    {"unidade": "Farroupilha", "url": "http://farroupilha.topesteticabucal.com.br/sistema"},
    {"unidade": "Bento", "url": "http://bento.topesteticabucal.com.br/sistema"},
    {"unidade": "Encantado", "url": "http://encantado.topesteticabucal.com.br/sistema"},
    {"unidade": "Soledade", "url": "http://soledade.topesteticabucal.com.br/sistema"},
    {"unidade": "Garibaldi", "url": "http://garibaldi.topesteticabucal.com.br/sistema"},
    {"unidade": "Veranopolis", "url": "http://veranopolis.topesteticabucal.com.br/sistema"},
    {"unidade": "Ssdocai", "url": "http://ssdocai.topesteticabucal.com.br/sistema"},
    {"unidade": "FloresDaCunha", "url": "http://flores.topesteticabucal.com.br/sistema"},
]

PASTA_DATA = Path("data")
ARQUIVO_PIX = PASTA_DATA / "pix_doutores.json"
ARQUIVO_SALDOS = PASTA_DATA / "saldos_doutores.json"
ARQUIVO_RESUMO = PASTA_DATA / "resumo_pix_doutores.json"


def parse_valor(texto: str) -> float:
    texto = (texto or "").strip()

    if not texto:
        return 0.0

    texto = texto.replace("R$", "").replace(".", "").replace(",", ".")
    texto = re.sub(r"[^\d.\-]", "", texto)

    try:
        return round(float(texto), 2)
    except ValueError:
        return 0.0


def salvar_json(dados: Any, caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def obter_periodo_mes_referencia() -> Tuple[str, str, str]:
    hoje = date.today()
    ano = hoje.year
    mes = hoje.month

    primeiro_dia = f"01/{mes:02d}/{ano}"
    ultimo_dia_num = calendar.monthrange(ano, mes)[1]
    ultimo_dia = f"{ultimo_dia_num:02d}/{mes:02d}/{ano}"
    competencia = f"{ano}-{mes:02d}"

    return primeiro_dia, ultimo_dia, competencia


def obter_competencia() -> str:
    _, _, competencia = obter_periodo_mes_referencia()
    return competencia


def preencher_primeiro_seletor_existente(page, seletores: List[str], valor: str) -> bool:
    for seletor in seletores:
        try:
            locator = page.locator(seletor)
            if locator.count() > 0 and locator.first.is_visible():
                locator.first.fill(valor)
                return True
        except Exception:
            continue
    return False


def clicar_primeiro_existente(page, seletores: List[str]) -> bool:
    for seletor in seletores:
        try:
            locator = page.locator(seletor)
            if locator.count() > 0 and locator.first.is_visible():
                locator.first.click()
                return True
        except Exception:
            continue
    return False


def setar_valor_input(locator, valor: str) -> None:
    locator.scroll_into_view_if_needed()
    locator.click(timeout=5000)

    try:
        locator.press("Control+A")
        locator.press("Backspace")
    except Exception:
        pass

    try:
        locator.fill(valor)
    except Exception:
        pass

    locator.evaluate(
        """(el, value) => {
            el.removeAttribute('readonly');
            el.value = value;
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
            el.dispatchEvent(new Event('blur', { bubbles: true }));
        }""",
        valor,
    )


def obter_inputs_visiveis_texto(page):
    inputs = page.locator("input")
    visiveis = []

    for i in range(inputs.count()):
        try:
            loc = inputs.nth(i)
            if not loc.is_visible():
                continue

            tipo = (loc.get_attribute("type") or "text").lower()
            if tipo in ["hidden", "submit", "button", "checkbox", "radio", "file"]:
                continue

            visiveis.append(loc)
        except Exception:
            continue

    return visiveis


def preencher_periodo_mes(page) -> str:
    data_inicio, data_fim, competencia = obter_periodo_mes_referencia()

    visiveis = obter_inputs_visiveis_texto(page)

    if len(visiveis) < 2:
        raise RuntimeError("Campos de data do período não encontrados.")

    # no sistema, os dois últimos campos visíveis do filtro são o período
    campo_inicio = visiveis[-2]
    campo_fim = visiveis[-1]

    setar_valor_input(campo_inicio, data_inicio)
    setar_valor_input(campo_fim, data_fim)

    page.wait_for_timeout(700)

    return competencia


def fazer_login(page, url: str) -> None:
    page.goto(url, wait_until="domcontentloaded", timeout=60000)

    preenchido_usuario = preencher_primeiro_seletor_existente(page, [
        'input[name="login"]',
        'input[name="usuario"]',
        '#login',
        '#usuario',
        'input[type="text"]',
    ], USUARIO)

    if not preenchido_usuario:
        raise RuntimeError("Campo de usuário não encontrado.")

    preenchido_senha = preencher_primeiro_seletor_existente(page, [
        'input[name="senha"]',
        '#senha',
        'input[type="password"]',
    ], SENHA)

    if not preenchido_senha:
        raise RuntimeError("Campo de senha não encontrado.")

    clicou = clicar_primeiro_existente(page, [
        'button[type="submit"]',
        'input[type="submit"]',
        'button:has-text("Entrar")',
        'button:has-text("Login")',
        'a:has-text("Entrar")',
    ])

    if not clicou:
        raise RuntimeError("Botão de login não encontrado.")

    page.wait_for_load_state("networkidle", timeout=60000)
    page.wait_for_timeout(1500)


def acessar_demonstrativo(page) -> str:
    clicou_financas = clicar_primeiro_existente(page, [
        'text="FINANÇAS"',
        'text="Finanças"',
        'a:has-text("FINANÇAS")',
        'a:has-text("Finanças")',
    ])
    if not clicou_financas:
        raise RuntimeError("Menu Finanças não encontrado.")

    page.wait_for_timeout(1200)

    clicou_demonstrativo = clicar_primeiro_existente(page, [
        'text="Demonstrativo de Resultado"',
        'text="Demonstrativo de Resultados"',
        'a:has-text("Demonstrativo de Resultado")',
        'a:has-text("Demonstrativo de Resultados")',
    ])
    if not clicou_demonstrativo:
        raise RuntimeError("Tela Demonstrativo de Resultado não encontrada.")

    page.wait_for_load_state("networkidle", timeout=60000)
    page.wait_for_timeout(2500)

    competencia = preencher_periodo_mes(page)

    clicou_buscar = clicar_primeiro_existente(page, [
        'button:has-text("Buscar")',
        'input[value="Buscar"]',
        'text="Buscar"',
    ])

    if not clicou_buscar:
        raise RuntimeError("Botão Buscar não encontrado.")

    page.wait_for_load_state("networkidle", timeout=60000)
    page.wait_for_timeout(4000)

    return competencia


def linha_eh_pix_doutores(metodo_raw: str) -> bool:
    return "pix doutores" in (metodo_raw or "").lower()


def extrair_responsavel_fiscal_do_metodo(metodo_raw: str) -> str:
    linhas = [l.strip() for l in (metodo_raw or "").split("\n") if l.strip()]

    if not linhas:
        return ""

    ignorar_prefixos = [
        "pix doutores",
        "maquina",
    ]

    candidatos = []
    for linha in linhas:
        linha_lower = linha.lower()
        if any(linha_lower.startswith(prefixo) for prefixo in ignorar_prefixos):
            continue
        candidatos.append(linha)

    if candidatos:
        return candidatos[0]

    if len(linhas) > 1:
        return linhas[1]

    return ""


def extrair_info_origem(origem_raw: str) -> Dict[str, Any]:
    texto = (origem_raw or "").strip()

    paciente = texto
    parcela = ""
    codigo = ""

    match_codigo = re.search(r"\((\d+)\)", texto)
    if match_codigo:
        codigo = match_codigo.group(1)

    match_parcela = re.search(r"\(Parcela\s+([^)]+)\)", texto, flags=re.IGNORECASE)
    if match_parcela:
        parcela = match_parcela.group(1)

    paciente = re.sub(r"\(\d+\)", "", paciente).strip()
    paciente = re.sub(r"\(Parcela\s+[^)]+\)", "", paciente, flags=re.IGNORECASE).strip()
    paciente = re.sub(r"\s+", " ", paciente).strip()

    return {
        "origem_completa": texto,
        "paciente": paciente,
        "codigo_origem": codigo,
        "parcela": parcela,
    }


def interpretar_linha(
    linha,
    unidade: str,
    mapa_creditos: Dict[str, Dict[str, Any]],
    competencia: str
) -> Optional[Dict[str, Any]]:
    colunas = linha.locator("td")
    qtd_colunas = colunas.count()

    if qtd_colunas < 5:
        return None

    try:
        data = colunas.nth(0).inner_text().strip()
        metodo_raw = colunas.nth(1).inner_text().strip()
        origem_raw = colunas.nth(2).inner_text().strip()
        valor_texto = colunas.nth(3).inner_text().strip()
        valor_desc_texto = colunas.nth(4).inner_text().strip()
        linha_original = linha.inner_text().strip()
    except Exception:
        return None

    if not linha_eh_pix_doutores(metodo_raw):
        return None

    responsavel_fiscal = extrair_responsavel_fiscal_do_metodo(metodo_raw)
    valor = parse_valor(valor_texto)
    valor_com_descontos = parse_valor(valor_desc_texto)
    info_origem = extrair_info_origem(origem_raw)
    desconto = aplicar_desconto(mapa_creditos, responsavel_fiscal, valor)

    return {
        "unidade": unidade,
        "data": data,
        "competencia": competencia,
        "metodo_pagamento": "Pix Doutores",
        "responsavel_fiscal_lido": responsavel_fiscal,
        "doutor_lido": responsavel_fiscal,
        "doutor_final": desconto["nome_padronizado"],
        "doutor_encontrado": desconto["doutor_encontrado"],
        "paciente": info_origem["paciente"],
        "codigo_origem": info_origem["codigo_origem"],
        "parcela": info_origem["parcela"],
        "origem": info_origem["origem_completa"],
        "valor": valor,
        "valor_com_descontos": valor_com_descontos,
        "credito_antes": desconto["credito_antes"],
        "valor_descontado": desconto["valor_descontado"],
        "credito_depois": desconto["credito_depois"],
        "pendente": desconto["pendente"],
        "linha_original": linha_original,
        "coletado_em": datetime.now().isoformat(),
    }


def extrair_linhas_pix(
    page,
    unidade: str,
    mapa_creditos: Dict[str, Dict[str, Any]],
    competencia: str
) -> List[Dict[str, Any]]:
    resultados: List[Dict[str, Any]] = []
    tabelas = page.locator("table")

    total_tabelas = tabelas.count()
    if total_tabelas == 0:
        raise RuntimeError("Nenhuma tabela encontrada na tela.")

    for i in range(total_tabelas):
        tabela = tabelas.nth(i)
        linhas = tabela.locator("tr")
        qtd_linhas = linhas.count()

        for j in range(qtd_linhas):
            linha = linhas.nth(j)
            registro = interpretar_linha(linha, unidade, mapa_creditos, competencia)
            if registro:
                resultados.append(registro)

    return resultados


def processar_unidade(
    browser,
    sistema: Dict[str, str],
    mapa_creditos: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    unidade = sistema["unidade"]
    url = sistema["url"]
    print(f"[INFO] Processando unidade: {unidade}")

    context = browser.new_context()
    page = context.new_page()
    page.set_default_timeout(30000)

    try:
        fazer_login(page, url)
        competencia = acessar_demonstrativo(page)
        resultados = extrair_linhas_pix(page, unidade, mapa_creditos, competencia)
        print(f"[INFO] {unidade}: {len(resultados)} linha(s) PIX DOUTORES encontrada(s).")
        return resultados

    except PlaywrightTimeoutError:
        print(f"[ERRO] Timeout na unidade {unidade}")
        return [{
            "unidade": unidade,
            "competencia": obter_competencia(),
            "erro": "Timeout ao acessar sistema",
            "coletado_em": datetime.now().isoformat(),
        }]
    except Exception as e:
        print(f"[ERRO] Falha na unidade {unidade}: {e}")
        return [{
            "unidade": unidade,
            "competencia": obter_competencia(),
            "erro": str(e),
            "coletado_em": datetime.now().isoformat(),
        }]
    finally:
        context.close()


def gerar_resumo(dados: List[Dict[str, Any]]) -> Dict[str, Any]:
    validos = [d for d in dados if "erro" not in d]
    competencia = obter_competencia()

    if validos:
        competencia = validos[0].get("competencia", competencia)

    total_valor = round(sum(float(d.get("valor", 0.0)) for d in validos), 2)
    total_descontado = round(sum(float(d.get("valor_descontado", 0.0)) for d in validos), 2)
    total_pendente = round(sum(float(d.get("pendente", 0.0)) for d in validos), 2)

    por_unidade: Dict[str, Dict[str, Any]] = {}
    por_doutor: Dict[str, Dict[str, Any]] = {}

    for item in validos:
        unidade = item["unidade"]
        doutor = item["doutor_final"]

        por_unidade.setdefault(unidade, {
            "unidade": unidade,
            "quantidade": 0,
            "valor": 0.0,
            "descontado": 0.0,
            "pendente": 0.0,
        })
        por_unidade[unidade]["quantidade"] += 1
        por_unidade[unidade]["valor"] = round(por_unidade[unidade]["valor"] + float(item["valor"]), 2)
        por_unidade[unidade]["descontado"] = round(por_unidade[unidade]["descontado"] + float(item["valor_descontado"]), 2)
        por_unidade[unidade]["pendente"] = round(por_unidade[unidade]["pendente"] + float(item["pendente"]), 2)

        por_doutor.setdefault(doutor, {
            "doutor": doutor,
            "quantidade": 0,
            "valor": 0.0,
            "descontado": 0.0,
            "pendente": 0.0,
        })
        por_doutor[doutor]["quantidade"] += 1
        por_doutor[doutor]["valor"] = round(por_doutor[doutor]["valor"] + float(item["valor"]), 2)
        por_doutor[doutor]["descontado"] = round(por_doutor[doutor]["descontado"] + float(item["valor_descontado"]), 2)
        por_doutor[doutor]["pendente"] = round(por_doutor[doutor]["pendente"] + float(item["pendente"]), 2)

    return {
        "competencia": competencia,
        "gerado_em": datetime.now().isoformat(),
        "quantidade_total": len(validos),
        "valor_total": total_valor,
        "valor_total_descontado": total_descontado,
        "valor_total_pendente": total_pendente,
        "por_unidade": sorted(por_unidade.values(), key=lambda x: x["unidade"].lower()),
        "por_doutor": sorted(por_doutor.values(), key=lambda x: x["doutor"].lower()),
    }


def salvar_arquivos_mensais(
    resultados: List[Dict[str, Any]],
    saldos_finais: List[Dict[str, Any]],
    resumo: Dict[str, Any]
) -> None:
    competencia = resumo.get("competencia", obter_competencia())

    arquivo_pix_mes = PASTA_DATA / f"pix_doutores_{competencia}.json"
    arquivo_saldos_mes = PASTA_DATA / f"saldos_doutores_{competencia}.json"
    arquivo_resumo_mes = PASTA_DATA / f"resumo_pix_doutores_{competencia}.json"

    salvar_json(resultados, arquivo_pix_mes)
    salvar_json(saldos_finais, arquivo_saldos_mes)
    salvar_json(resumo, arquivo_resumo_mes)

    print(f"[OK] Arquivo mensal gerado: {arquivo_pix_mes}")
    print(f"[OK] Arquivo mensal gerado: {arquivo_saldos_mes}")
    print(f"[OK] Arquivo mensal gerado: {arquivo_resumo_mes}")


def main() -> None:
    mapa_creditos = montar_mapa_creditos()
    todos_resultados: List[Dict[str, Any]] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for sistema in SISTEMAS:
            resultados = processar_unidade(browser, sistema, mapa_creditos)
            todos_resultados.extend(resultados)

        browser.close()

    resumo = gerar_resumo(todos_resultados)
    saldos_finais = listar_saldos_finais(mapa_creditos)

    salvar_json(todos_resultados, ARQUIVO_PIX)
    salvar_json(saldos_finais, ARQUIVO_SALDOS)
    salvar_json(resumo, ARQUIVO_RESUMO)

    salvar_arquivos_mensais(todos_resultados, saldos_finais, resumo)

    print(f"[OK] Arquivo gerado: {ARQUIVO_PIX}")
    print(f"[OK] Arquivo gerado: {ARQUIVO_SALDOS}")
    print(f"[OK] Arquivo gerado: {ARQUIVO_RESUMO}")


if __name__ == "__main__":
    main()
