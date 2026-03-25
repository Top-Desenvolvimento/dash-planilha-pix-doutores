const state = {
  creditos: [],
  lancamentos: [],
  mesSelecionado: null,
  unidadeSelecionada: "Todos",
  doutorSelecionado: "Todos",
  metodoSelecionado: "Todos"
};

document.addEventListener("DOMContentLoaded", async () => {
  await carregarDados();
  montarFiltrosExtras();
  montarFiltros();
  aplicarFiltros();
  registrarEventos();
});

async function carregarDados() {
  const [creditosRes, lancamentosRes] = await Promise.all([
    fetch(`data/doutores_credito.json?v=${Date.now()}`),
    fetch(`data/pix_doutores.json?v=${Date.now()}`)
  ]);

  state.creditos = await creditosRes.json();
  state.lancamentos = await lancamentosRes.json();

  const meses = [...new Set(state.lancamentos.map(l => `${l.ano}-${String(l.mes).padStart(2, "0")}`))].sort();
  state.mesSelecionado = meses[meses.length - 1] || null;
}

function normalizarNome(txt) {
  return (txt || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/\b(dr|dra|cir)\.?\b/g, "")
    .replace(/[^a-z0-9\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function classificarMetodo(metodoRaw) {
  const txt = (metodoRaw || "").toLowerCase();

  if (txt.includes("pix doutores")) return "PIX Doutores";
  if (txt.includes("pix")) return "PIX";
  if (txt.includes("cart") || txt.includes("credito") || txt.includes("crédito") || txt.includes("debito") || txt.includes("débito")) return "Cartão";
  if (txt.includes("dinheiro")) return "Dinheiro";
  if (txt.includes("boleto")) return "Boleto";
  if (txt.includes("transfer") || txt.includes("deposito") || txt.includes("depósito")) return "Transferência/Depósito";

  return "Outros";
}

function extrairDoutorDoMetodo(metodoRaw, creditos) {
  if (!metodoRaw) return null;

  const linhas = metodoRaw
    .split("\n")
    .map(x => x.trim())
    .filter(Boolean);

  const linhasSemPix = linhas.filter(l => !l.toLowerCase().includes("pix doutores"));

  const invalidos = [
    "dinheiro", "saldo total", "maquina", "máquina",
    "cartao", "cartão", "pix", "debito", "débito",
    "credito", "crédito", "boleto", "transferencia",
    "transferência", "deposito", "depósito"
  ];

  for (let linha of linhasSemPix) {
    linha = linha.replace(/^(cir\.?|dra\.?|dr\.?)/i, "").trim();

    const linhaNorm = normalizarNome(linha);
    if (!linhaNorm) continue;
    if (invalidos.some(x => linhaNorm.includes(normalizarNome(x)))) continue;

    for (const c of creditos) {
      const oficial = c.doutor;
      const oficialNorm = normalizarNome(oficial);

      if (!oficialNorm) continue;
      if (oficialNorm === linhaNorm) return oficial;

      const tokensLinha = new Set(linhaNorm.split(" "));
      const tokensOficial = oficialNorm.split(" ");
      const todosContidos = tokensOficial.every(t => tokensLinha.has(t));
      if (todosContidos) return oficial;

      if (tokensOficial.length >= 2) {
        const primeiro = tokensOficial[0];
        const ultimo = tokensOficial[tokensOficial.length - 1];
        if (tokensLinha.has(primeiro) && tokensLinha.has(ultimo)) {
          return oficial;
        }
      }
    }
  }

  return null;
}

function transformarLancamentosBrutos(lancamentos, creditos) {
  return lancamentos.map(l => {
    const metodoCategoria = l.metodo_categoria || classificarMetodo(l.metodo_raw || "");
    const doutor = metodoCategoria === "PIX Doutores"
      ? extrairDoutorDoMetodo(l.metodo_raw, creditos)
      : null;

    return {
      ...l,
      metodo: metodoCategoria,
      doutor
    };
  });
}

function montarFiltrosExtras() {
  const sidebar = document.querySelector(".side-card");
  if (!sidebar || document.getElementById("filtroMetodo")) return;

  const label = document.createElement("label");
  label.textContent = "Método";

  const select = document.createElement("select");
  select.id = "filtroMetodo";
  select.innerHTML = `
    <option value="Todos">Todos</option>
    <option value="PIX Doutores">PIX Doutores</option>
    <option value="PIX">PIX</option>
    <option value="Cartão">Cartão</option>
    <option value="Dinheiro">Dinheiro</option>
    <option value="Boleto">Boleto</option>
    <option value="Transferência/Depósito">Transferência/Depósito</option>
    <option value="Outros">Outros</option>
  `;

  const unidadeLabel = [...sidebar.querySelectorAll("label")].find(l => l.textContent.trim() === "Unidade");
  if (unidadeLabel) {
    sidebar.insertBefore(label, unidadeLabel);
    sidebar.insertBefore(select, unidadeLabel);
  } else {
    sidebar.appendChild(label);
    sidebar.appendChild(select);
  }
}

function montarFiltros() {
  const filtroMes = document.getElementById("filtroMes");
  const filtroUnidade = document.getElementById("filtroUnidade");
  const filtroDoutor = document.getElementById("filtroDoutor");

  const lancamentosTratados = transformarLancamentosBrutos(state.lancamentos, state.creditos);

  const meses = [...new Set(lancamentosTratados.map(l => `${l.ano}-${String(l.mes).padStart(2, "0")}`))].sort();
  filtroMes.innerHTML = meses
    .map(m => `<option value="${m}" ${m === state.mesSelecionado ? "selected" : ""}>${formatarCompetencia(m)}</option>`)
    .join("");

  const unidades = [...new Set(lancamentosTratados.map(l => l.unidade))].sort();
  filtroUnidade.innerHTML = `<option value="Todos">Todas</option>` + unidades.map(u => `<option value="${u}">${u}</option>`).join("");

  const doutores = [...new Set(state.creditos.filter(d => d.ativo).map(d => d.doutor))].sort();
  filtroDoutor.innerHTML = `<option value="Todos">Todos</option>` + doutores.map(d => `<option value="${d}">${d}</option>`).join("");
}

function registrarEventos() {
  document.getElementById("filtroMes").addEventListener("change", e => {
    state.mesSelecionado = e.target.value;
    aplicarFiltros();
  });

  document.getElementById("filtroUnidade").addEventListener("change", e => {
    state.unidadeSelecionada = e.target.value;
    aplicarFiltros();
  });

  document.getElementById("filtroDoutor").addEventListener("change", e => {
    state.doutorSelecionado = e.target.value;
    aplicarFiltros();
  });

  const filtroMetodo = document.getElementById("filtroMetodo");
  if (filtroMetodo) {
    filtroMetodo.addEventListener("change", e => {
      state.metodoSelecionado = e.target.value;
      aplicarFiltros();
    });
  }

  document.getElementById("btnLimpar").addEventListener("click", () => {
    state.unidadeSelecionada = "Todos";
    state.doutorSelecionado = "Todos";
    state.metodoSelecionado = "Todos";

    document.getElementById("filtroUnidade").value = "Todos";
    document.getElementById("filtroDoutor").value = "Todos";

    const fm = document.getElementById("filtroMetodo");
    if (fm) fm.value = "Todos";

    aplicarFiltros();
  });

  document.getElementById("btnExportar").addEventListener("click", exportarCSV);
}

function aplicarFiltros() {
  const lancamentosTratados = transformarLancamentosBrutos(state.lancamentos, state.creditos);

  const dadosMes = lancamentosTratados.filter(l => {
    const comp = `${l.ano}-${String(l.mes).padStart(2, "0")}`;
    return comp === state.mesSelecionado;
  });

  const filtrados = dadosMes.filter(l => {
    const okUnidade = state.unidadeSelecionada === "Todos" || l.unidade === state.unidadeSelecionada;
    const okMetodo = state.metodoSelecionado === "Todos" || l.metodo === state.metodoSelecionado;
    const okDoutor =
      state.doutorSelecionado === "Todos" ||
      l.doutor === state.doutorSelecionado;

    return okUnidade && okMetodo && okDoutor;
  });

  const apenasPixDoutoresValidos = filtrados.filter(l => l.metodo === "PIX Doutores" && l.doutor);
  const resumo = calcularResumo(apenasPixDoutoresValidos, state.creditos);

  renderCards(resumo, filtrados);
  renderAlerta(resumo);
  renderTabelaResumo(resumo);
  renderTabelaLancamentos(filtrados);
  renderGrafico(resumo);

  const periodo = state.mesSelecionado ? formatarCompetencia(state.mesSelecionado) : "Sem dados";
  document.getElementById("periodoAtual").textContent = `Competência: ${periodo}`;
}

function calcularResumo(lancamentos, creditos) {
  const mapa = {};

  creditos
    .filter(c => c.ativo)
    .forEach(c => {
      mapa[c.doutor] = {
        doutor: c.doutor,
        credito: Number(c.credito || 0),
        utilizado: 0,
        saldo: Number(c.credito || 0),
        percentual: 0,
        status: "verde"
      };
    });

  lancamentos.forEach(l => {
    if (mapa[l.doutor]) {
      mapa[l.doutor].utilizado += Number(l.valor || 0);
    }
  });

  Object.values(mapa).forEach(item => {
    item.saldo = item.credito - item.utilizado;
    item.percentual = item.credito > 0 ? (item.utilizado / item.credito) * 100 : 0;

    if (item.percentual >= 100) item.status = "vermelho";
    else if (item.percentual >= 50) item.status = "amarelo";
    else item.status = "verde";
  });

  return Object.values(mapa).sort((a, b) => b.percentual - a.percentual);
}

function renderCards(resumo, lancamentosFiltrados) {
  const totalAutorizado = resumo.reduce((s, r) => s + r.credito, 0);
  const totalUtilizado = resumo.reduce((s, r) => s + r.utilizado, 0);
  const saldoTotal = resumo.reduce((s, r) => s + r.saldo, 0);
  const verdes = resumo.filter(r => r.percentual === 0).length;
  const amarelos = resumo.filter(r => r.percentual >= 50 && r.percentual < 100).length;
  const vermelhos = resumo.filter(r => r.percentual >= 100).length;
  const totalMonitorados = resumo.length;
  const qtdLancamentos = lancamentosFiltrados.length;

  const cards = [
    { label: "Doutores monitorados", value: totalMonitorados, mini: "Cadastro ativo no mês" },
    { label: "Lançamentos filtrados", value: qtdLancamentos, mini: "Tabela inferior" },
    { label: "Total autorizado", value: formatarMoeda(totalAutorizado), mini: "Crédito mensal consolidado" },
    { label: "Total utilizado", value: formatarMoeda(totalUtilizado), mini: "Só PIX Doutores com doutor válido" },
    { label: "Saldo total", value: formatarMoeda(saldoTotal), mini: "Disponível remanescente" },
    { label: "Sem utilização", value: verdes, mini: "Status verde" },
    { label: "Em atenção", value: amarelos, mini: "50% ou mais" },
    { label: "Sem limite", value: vermelhos, mini: "100% ou mais" }
  ];

  document.getElementById("cardsGrid").innerHTML = cards.map(card => `
    <div class="metric-card">
      <div class="label">${card.label}</div>
      <div class="value">${card.value}</div>
      <div class="mini">${card.mini}</div>
    </div>
  `).join("");
}

function renderAlerta(resumo) {
  const criticos = resumo.filter(r => r.percentual >= 100);
  const box = document.getElementById("alertaCritico");

  if (!criticos.length) {
    box.classList.add("hidden");
    box.innerHTML = "";
    return;
  }

  box.classList.remove("hidden");
  box.innerHTML = `
    <h3>🚨 Doutores sem limite disponível</h3>
    ${criticos.map(c => `
      <p><strong>${c.doutor}</strong> — utilizado ${formatarMoeda(c.utilizado)} de ${formatarMoeda(c.credito)} (${c.percentual.toFixed(1)}%)</p>
    `).join("")}
  `;
}

function renderTabelaResumo(resumo) {
  const tbody = document.querySelector("#tabelaResumo tbody");

  tbody.innerHTML = resumo.map(r => {
    const classeLinha = r.status === "vermelho" ? "row-red" : r.status === "amarelo" ? "row-yellow" : "row-green";
    const statusClass = r.status === "vermelho" ? "status-red" : r.status === "amarelo" ? "status-yellow" : "status-green";
    const fillClass = r.status === "vermelho" ? "fill-red" : r.status === "amarelo" ? "fill-yellow" : "fill-green";

    return `
      <tr class="${classeLinha}">
        <td>${r.doutor}</td>
        <td>${formatarMoeda(r.credito)}</td>
        <td>${formatarMoeda(r.utilizado)}</td>
        <td>${formatarMoeda(r.saldo)}</td>
        <td>
          <div style="display:flex; align-items:center; gap:10px;">
            <div class="progress-bar">
              <div class="progress-fill ${fillClass}" style="width:${Math.min(r.percentual, 100)}%"></div>
            </div>
            <span>${r.percentual.toFixed(1)}%</span>
          </div>
        </td>
        <td>
          <span class="status-pill ${statusClass}">
            ${textoStatus(r.status, r.percentual)}
          </span>
        </td>
      </tr>
    `;
  }).join("");
}

function renderTabelaLancamentos(lancamentos) {
  const tbody = document.querySelector("#tabelaLancamentos tbody");
  const ordenados = [...lancamentos].sort((a, b) => new Date(a.data) - new Date(b.data));

  tbody.innerHTML = ordenados.map(l => `
    <tr>
      <td>${formatarData(l.data)}</td>
      <td>${l.unidade}</td>
      <td>${l.doutor || "-"}</td>
      <td>${l.metodo}</td>
      <td>${l.origem}</td>
      <td>${formatarMoeda(l.valor)}</td>
    </tr>
  `).join("");
}

function renderGrafico(resumo) {
  const chartDom = document.getElementById("graficoConsumo");
  const chart = echarts.init(chartDom);

  const topResumo = [...resumo].sort((a, b) => b.utilizado - a.utilizado);

  const option = {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      valueFormatter: value => formatarMoeda(value)
    },
    legend: {
      top: 0,
      textStyle: { color: "#dce5ff" }
    },
    grid: {
      left: 10,
      right: 10,
      bottom: 20,
      top: 50,
      containLabel: true
    },
    xAxis: {
      type: "value",
      axisLabel: {
        color: "#b9c5e3",
        formatter: value => `R$ ${value}`
      },
      splitLine: {
        lineStyle: { color: "rgba(255,255,255,0.08)" }
      }
    },
    yAxis: {
      type: "category",
      data: topResumo.map(r => r.doutor),
      axisLabel: { color: "#e6edff" },
      axisLine: { lineStyle: { color: "rgba(255,255,255,0.15)" } }
    },
    series: [
      {
        name: "Crédito",
        type: "bar",
        data: topResumo.map(r => r.credito),
        itemStyle: { color: "rgba(108,140,255,0.85)", borderRadius: [0, 8, 8, 0] }
      },
      {
        name: "Utilizado",
        type: "bar",
        data: topResumo.map(r => r.utilizado),
        itemStyle: {
          color: params => {
            const item = topResumo[params.dataIndex];
            if (item.percentual >= 100) return "#ff5f70";
            if (item.percentual >= 50) return "#f6c445";
            return "#1ec97f";
          },
          borderRadius: [0, 8, 8, 0]
        }
      }
    ]
  };

  chart.setOption(option);
  window.addEventListener("resize", () => chart.resize());
}

function exportarCSV() {
  const lancamentosTratados = transformarLancamentosBrutos(state.lancamentos, state.creditos);

  const dadosMes = lancamentosTratados.filter(l => {
    const comp = `${l.ano}-${String(l.mes).padStart(2, "0")}`;
    return comp === state.mesSelecionado;
  }).filter(l => {
    const okUnidade = state.unidadeSelecionada === "Todos" || l.unidade === state.unidadeSelecionada;
    const okMetodo = state.metodoSelecionado === "Todos" || l.metodo === state.metodoSelecionado;
    const okDoutor = state.doutorSelecionado === "Todos" || l.doutor === state.doutorSelecionado;
    return okUnidade && okMetodo && okDoutor;
  });

  const resumo = calcularResumo(
    dadosMes.filter(l => l.metodo === "PIX Doutores" && l.doutor),
    state.creditos
  );

  const resumoMap = Object.fromEntries(resumo.map(r => [r.doutor, r]));

  const header = [
    "Data",
    "Unidade",
    "Doutor",
    "Metodo",
    "Origem",
    "Valor",
    "Credito autorizado",
    "Total utilizado no mes",
    "Saldo restante",
    "Status"
  ];

  const linhas = dadosMes.map(d => {
    const r = d.doutor ? resumoMap[d.doutor] : null;
    return [
      formatarData(d.data),
      d.unidade,
      d.doutor || "",
      d.metodo,
      d.origem,
      d.valor,
      r?.credito ?? "",
      r?.utilizado ?? "",
      r?.saldo ?? "",
      r ? textoStatus(r.status, r.percentual) : ""
    ];
  });

  const csv = [header, ...linhas]
    .map(l => l.map(valor => `"${String(valor).replace(/"/g, '""')}"`).join(";"))
    .join("\n");

  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `lancamentos_${state.mesSelecionado}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

function formatarMoeda(valor) {
  return Number(valor || 0).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL"
  });
}

function formatarData(dataISO) {
  const [ano, mes, dia] = dataISO.split("-");
  return `${dia}/${mes}/${ano}`;
}

function formatarCompetencia(comp) {
  const [ano, mes] = comp.split("-");
  const nomes = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"];
  return `${nomes[Number(mes) - 1]}/${ano}`;
}

function textoStatus(status, percentual) {
  if (status === "vermelho") return `Crítico (${percentual.toFixed(1)}%)`;
  if (status === "amarelo") return `Atenção (${percentual.toFixed(1)}%)`;
  if (percentual === 0) return "Sem utilização";
  return `Dentro do limite (${percentual.toFixed(1)}%)`;
}
