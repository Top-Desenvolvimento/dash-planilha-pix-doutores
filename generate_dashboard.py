from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


ARQUIVO_PIX = Path("data/pix_doutores.json")
ARQUIVO_SALDOS = Path("data/saldos_doutores.json")
ARQUIVO_RESUMO = Path("data/resumo_pix_doutores.json")
ARQUIVO_HTML = Path("data/dashboard.html")


def carregar_json(caminho: Path, padrao: Any) -> Any:
    if not caminho.exists():
        return padrao

    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def formatar_moeda(valor: Any) -> str:
    try:
        numero = float(valor or 0)
    except Exception:
        numero = 0.0

    texto = f"{numero:,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def escape_html(texto: Any) -> str:
    texto = str(texto or "")
    return (
        texto.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def garantir_lista(valor: Any) -> List[Any]:
    if isinstance(valor, list):
        return valor
    if isinstance(valor, dict):
        return list(valor.values())
    return []


def garantir_dict(valor: Any) -> Dict[str, Any]:
    if isinstance(valor, dict):
        return valor
    return {}


def normalizar_saldos(saldos: Any) -> List[Dict[str, Any]]:
    """
    Normaliza o conteúdo de saldos_doutores.json para evitar quebra quando:
    - vier lista de dicionários
    - vier lista de strings
    - vier dict
    - vier dict com chave 'saldos'
    """
    if isinstance(saldos, dict):
        if isinstance(saldos.get("saldos"), list):
            origem = saldos.get("saldos", [])
        else:
            origem = list(saldos.values())
    elif isinstance(saldos, list):
        origem = saldos
    else:
        origem = []

    saida: List[Dict[str, Any]] = []

    for item in origem:
        if isinstance(item, dict):
            doutor = item.get("doutor") or item.get("nome") or item.get("doutor_final") or "Não informado"
            credito_inicial = item.get("credito_inicial", item.get("credito", 0.0))
            credito_disponivel = item.get("credito_disponivel", item.get("credito_final", 0.0))
            utilizado = item.get("utilizado", 0.0)

            try:
                credito_inicial = float(credito_inicial or 0)
            except Exception:
                credito_inicial = 0.0

            try:
                credito_disponivel = float(credito_disponivel or 0)
            except Exception:
                credito_disponivel = 0.0

            try:
                utilizado = float(utilizado or 0)
            except Exception:
                utilizado = 0.0

            saida.append({
                "doutor": doutor,
                "credito_inicial": credito_inicial,
                "credito_disponivel": credito_disponivel,
                "utilizado": utilizado,
            })

        elif isinstance(item, str):
            saida.append({
                "doutor": item,
                "credito_inicial": 0.0,
                "credito_disponivel": 0.0,
                "utilizado": 0.0,
            })

    return saida


def normalizar_registros(registros: Any) -> List[Dict[str, Any]]:
    origem = garantir_lista(registros)
    saida: List[Dict[str, Any]] = []

    for item in origem:
        if isinstance(item, dict):
            saida.append(item)
        elif isinstance(item, str):
            saida.append({
                "unidade": "",
                "data": "",
                "doutor_final": "",
                "paciente": item,
                "valor": 0.0,
                "valor_descontado": 0.0,
                "pendente": 0.0,
            })

    return saida


def normalizar_resumo(resumo: Any) -> Dict[str, Any]:
    resumo = garantir_dict(resumo)
    return {
        "quantidade_total": resumo.get("quantidade_total", 0),
        "valor_total": resumo.get("valor_total", 0.0),
        "valor_total_descontado": resumo.get("valor_total_descontado", 0.0),
        "valor_total_pendente": resumo.get("valor_total_pendente", 0.0),
        "competencia": resumo.get("competencia", "-"),
        "gerado_em": resumo.get("gerado_em", "-"),
        "por_unidade": garantir_lista(resumo.get("por_unidade", [])),
        "por_doutor": garantir_lista(resumo.get("por_doutor", [])),
    }


def montar_cards_resumo(resumo: Dict[str, Any]) -> str:
    quantidade_total = resumo.get("quantidade_total", 0)
    valor_total = resumo.get("valor_total", 0.0)
    valor_total_descontado = resumo.get("valor_total_descontado", 0.0)
    valor_total_pendente = resumo.get("valor_total_pendente", 0.0)
    competencia = resumo.get("competencia", "-")
    gerado_em = resumo.get("gerado_em", "-")

    return f"""
    <div class="cards">
      <div class="card">
        <div class="card-title">Competência</div>
        <div class="card-value">{escape_html(competencia)}</div>
      </div>
      <div class="card">
        <div class="card-title">Linhas coletadas</div>
        <div class="card-value">{quantidade_total}</div>
      </div>
      <div class="card">
        <div class="card-title">Valor total</div>
        <div class="card-value">{formatar_moeda(valor_total)}</div>
      </div>
      <div class="card">
        <div class="card-title">Total descontado</div>
        <div class="card-value positivo">{formatar_moeda(valor_total_descontado)}</div>
      </div>
      <div class="card">
        <div class="card-title">Total pendente</div>
        <div class="card-value alerta">{formatar_moeda(valor_total_pendente)}</div>
      </div>
      <div class="card">
        <div class="card-title">Gerado em</div>
        <div class="card-value small">{escape_html(gerado_em)}</div>
      </div>
    </div>
    """


def montar_tabela_unidades(resumo: Dict[str, Any]) -> str:
    linhas = garantir_lista(resumo.get("por_unidade", []))
    trs = []

    for item in linhas:
        if not isinstance(item, dict):
            continue

        trs.append(f"""
        <tr>
          <td>{escape_html(item.get("unidade", ""))}</td>
          <td>{item.get("quantidade", 0)}</td>
          <td>{formatar_moeda(item.get("valor", 0.0))}</td>
          <td>{formatar_moeda(item.get("descontado", 0.0))}</td>
          <td>{formatar_moeda(item.get("pendente", 0.0))}</td>
        </tr>
        """)

    return f"""
    <section class="bloco">
      <h2>Resumo por unidade</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Unidade</th>
              <th>Qtd.</th>
              <th>Valor</th>
              <th>Descontado</th>
              <th>Pendente</th>
            </tr>
          </thead>
          <tbody>
            {''.join(trs) if trs else '<tr><td colspan="5">Sem dados</td></tr>'}
          </tbody>
        </table>
      </div>
    </section>
    """


def montar_tabela_doutores(resumo: Dict[str, Any]) -> str:
    linhas = garantir_lista(resumo.get("por_doutor", []))
    trs = []

    for item in linhas:
        if not isinstance(item, dict):
            continue

        trs.append(f"""
        <tr>
          <td>{escape_html(item.get("doutor", ""))}</td>
          <td>{item.get("quantidade", 0)}</td>
          <td>{formatar_moeda(item.get("valor", 0.0))}</td>
          <td>{formatar_moeda(item.get("descontado", 0.0))}</td>
          <td>{formatar_moeda(item.get("pendente", 0.0))}</td>
        </tr>
        """)

    return f"""
    <section class="bloco">
      <h2>Resumo por doutor</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Doutor</th>
              <th>Qtd.</th>
              <th>Valor</th>
              <th>Descontado</th>
              <th>Pendente</th>
            </tr>
          </thead>
          <tbody>
            {''.join(trs) if trs else '<tr><td colspan="5">Sem dados</td></tr>'}
          </tbody>
        </table>
      </div>
    </section>
    """


def montar_tabela_saldos(saldos: Any) -> str:
    linhas = normalizar_saldos(saldos)
    trs = []

    for item in linhas:
        credito_disponivel = float(item.get("credito_disponivel", 0.0))
        classe = "zerado" if credito_disponivel <= 0 else "normal"

        trs.append(f"""
        <tr>
          <td>{escape_html(item.get("doutor", ""))}</td>
          <td>{formatar_moeda(item.get("credito_inicial", 0.0))}</td>
          <td>{formatar_moeda(item.get("utilizado", 0.0))}</td>
          <td class="{classe}">{formatar_moeda(credito_disponivel)}</td>
        </tr>
        """)

    return f"""
    <section class="bloco">
      <h2>Saldos finais dos doutores</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Doutor</th>
              <th>Crédito inicial</th>
              <th>Utilizado</th>
              <th>Crédito disponível</th>
            </tr>
          </thead>
          <tbody>
            {''.join(trs) if trs else '<tr><td colspan="4">Sem dados</td></tr>'}
          </tbody>
        </table>
      </div>
    </section>
    """


def montar_tabela_registros(registros: List[Dict[str, Any]]) -> str:
    trs = []

    for item in registros:
        if not isinstance(item, dict):
            continue

        pendente = float(item.get("pendente", 0.0) or 0.0)
        classe_pendente = "alerta" if pendente > 0 else "ok"

        trs.append(f"""
        <tr>
          <td>{escape_html(item.get("unidade", ""))}</td>
          <td>{escape_html(item.get("data", ""))}</td>
          <td>{escape_html(item.get("doutor_final", ""))}</td>
          <td>{escape_html(item.get("paciente", ""))}</td>
          <td>{formatar_moeda(item.get("valor", 0.0))}</td>
          <td>{formatar_moeda(item.get("valor_descontado", 0.0))}</td>
          <td class="{classe_pendente}">{formatar_moeda(pendente)}</td>
        </tr>
        """)

    return f"""
    <section class="bloco">
      <h2>Registros detalhados</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Unidade</th>
              <th>Data</th>
              <th>Doutor</th>
              <th>Paciente</th>
              <th>Valor</th>
              <th>Descontado</th>
              <th>Pendente</th>
            </tr>
          </thead>
          <tbody>
            {''.join(trs) if trs else '<tr><td colspan="7">Sem dados</td></tr>'}
          </tbody>
        </table>
      </div>
    </section>
    """


def montar_tabela_erros(registros: List[Dict[str, Any]]) -> str:
    erros = [r for r in registros if isinstance(r, dict) and "erro" in r]

    trs = []
    for item in erros:
        trs.append(f"""
        <tr>
          <td>{escape_html(item.get("unidade", ""))}</td>
          <td>{escape_html(item.get("erro", ""))}</td>
          <td>{escape_html(item.get("coletado_em", ""))}</td>
        </tr>
        """)

    return f"""
    <section class="bloco">
      <h2>Erros</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Unidade</th>
              <th>Erro</th>
              <th>Data/Hora</th>
            </tr>
          </thead>
          <tbody>
            {''.join(trs) if trs else '<tr><td colspan="3">Sem erros</td></tr>'}
          </tbody>
        </table>
      </div>
    </section>
    """


def gerar_html(resumo: Dict[str, Any], saldos: Any, registros: List[Dict[str, Any]]) -> str:
    registros_validos = [r for r in registros if isinstance(r, dict) and "erro" not in r]

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Dashboard PIX Doutores</title>
  <style>
    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      font-family: Arial, sans-serif;
      background: #f4f6f8;
      color: #1f2937;
    }}

    .container {{
      max-width: 1400px;
      margin: 0 auto;
      padding: 24px;
    }}

    h1 {{
      margin: 0 0 8px;
      font-size: 30px;
    }}

    .sub {{
      margin-bottom: 24px;
      color: #6b7280;
    }}

    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }}

    .card {{
      background: #fff;
      border-radius: 12px;
      padding: 18px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    }}

    .card-title {{
      color: #6b7280;
      font-size: 14px;
      margin-bottom: 10px;
    }}

    .card-value {{
      font-size: 24px;
      font-weight: bold;
      color: #111827;
    }}

    .card-value.small {{
      font-size: 16px;
      word-break: break-word;
    }}

    .positivo {{
      color: #047857;
    }}

    .alerta {{
      color: #b45309;
      font-weight: bold;
    }}

    .ok {{
      color: #047857;
      font-weight: bold;
    }}

    .zerado {{
      color: #b91c1c;
      font-weight: bold;
    }}

    .normal {{
      color: #111827;
      font-weight: bold;
    }}

    .bloco {{
      background: #fff;
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 24px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    }}

    .bloco h2 {{
      margin-top: 0;
      margin-bottom: 16px;
      font-size: 20px;
    }}

    .table-wrap {{
      overflow-x: auto;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      min-width: 900px;
    }}

    thead {{
      background: #111827;
      color: #fff;
    }}

    th, td {{
      padding: 12px 10px;
      border-bottom: 1px solid #e5e7eb;
      text-align: left;
      font-size: 14px;
      vertical-align: top;
    }}

    tbody tr:hover {{
      background: #f9fafb;
    }}
  </style>
</head>
<body>
  <div class="container">
    <h1>Dashboard PIX Doutores</h1>
    <div class="sub">Relatório gerado automaticamente com base nos arquivos da pasta data.</div>

    {montar_cards_resumo(resumo)}
    {montar_tabela_unidades(resumo)}
    {montar_tabela_doutores(resumo)}
    {montar_tabela_saldos(saldos)}
    {montar_tabela_registros(registros_validos)}
    {montar_tabela_erros(registros)}
  </div>
</body>
</html>
"""


def main() -> None:
    registros_brutos = carregar_json(ARQUIVO_PIX, [])
    saldos_brutos = carregar_json(ARQUIVO_SALDOS, [])
    resumo_bruto = carregar_json(ARQUIVO_RESUMO, {})

    registros = normalizar_registros(registros_brutos)
    saldos = normalizar_saldos(saldos_brutos)
    resumo = normalizar_resumo(resumo_bruto)

    html = gerar_html(resumo, saldos, registros)

    ARQUIVO_HTML.parent.mkdir(parents=True, exist_ok=True)
    with open(ARQUIVO_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[OK] Dashboard gerado em: {ARQUIVO_HTML}")


if __name__ == "__main__":
    main()
