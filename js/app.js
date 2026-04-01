let dashboardData = null;

function formatarMoeda(valor) {
  return Number(valor || 0).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL"
  });
}

function escapeHtml(valor) {
  return String(valor ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function formatarCompetenciaLabel(competencia) {
  const mapa = {
    "01": "Jan",
    "02": "Fev",
    "03": "Mar",
    "04": "Abr",
    "05": "Mai",
    "06": "Jun",
    "07": "Jul",
    "08": "Ago",
    "09": "Set",
    "10": "Out",
    "11": "Nov",
    "12": "Dez"
  };

  const [ano, mes] = String(competencia || "").split("-");
  return `${mapa[mes] || mes}/${ano || ""}`;
}

function obterPercentual(utilizado, creditoInicial) {
  const credito = Number(creditoInicial || 0);
  if (credito <= 0) return 0;
  return (Number(utilizado || 0) / credito) * 100;
}

function obterStatus(percentual) {
  if (percentual >= 100) {
    return { classe: "status-red", texto: "Limite atingido", dot: "dot-red" };
  }

  if (percentual >= 50) {
    return { classe: "status-yellow", texto: "Atenção", dot: "dot-yellow" };
  }

  return { classe: "status-green", texto: "Controlado", dot: "dot-green" };
}

function preencherFiltros(data) {
  const filtroMes = document.getElementById("filtroMes");
  const filtroUnidade = document.getElementById("filtroUnidade");
  const filtroDoutor = document.getElementById("filtroDoutor");

  const meses = data?.meses_disponiveis || [];
  const competenciaPadrao = data?.competencia_padrao || "";

  filtroMes.innerHTML = meses
    .map(item => `<option value="${escapeHtml(item)}">${escapeHtml(formatarCompetenciaLabel(item))}</option>`)
    .join("");

  if (competenciaPadrao) {
    filtroMes.value = competenciaPadrao;
  }

  const unidades = [...new Set((data.registros || []).map(item => item.unidade).filter(Boolean))].sort();
  const doutores = [...new Set((data.registros || []).map(item => item.doutor_final).filter(Boolean))].sort();

  filtroUnidade.innerHTML =
    `<option value="">Todas</option>` +
    unidades.map(item => `<option value="${escapeHtml(item)}">${escapeHtml(item)}</option>`).join("");

  filtroDoutor.innerHTML =
    `<option value="">Todos</option>` +
    doutores.map(item => `<option value="${escapeHtml(item)}">${escapeHtml(item)}</option>`).join("");
}

function obterDadosFiltrados() {
  const competencia = document.getElementById("filtroMes").value;
  const filtroUnidade = document.getElementById("filtroUnidade").value;
  const filtroDoutor = document.getElementById("filtroDoutor").value;

  let registros = [...(dashboardData?.registros || [])];
  let erros = [...(dashboardData?.erros || [])];
  let saldos = [...(dashboardData?.saldos_por_competencia?.[competencia] || [])];
  const resumo = dashboardData?.resumos_por_competencia?.[competencia] || {
    quantidade_total: 0,
    valor_total: 0,
    valor_total_descontado: 0,
    valor_total_pendente: 0,
    por_unidade: [],
    por_doutor: []
  };

  registros = registros.filter(item => String(item.competencia || "") === competencia);
  erros = erros.filter(item => String(item.competencia || "") === competencia);

  if (filtroUnidade) {
    registros = registros.filter(item => String(item.unidade || "") === filtroUnidade);
    erros = erros.filter(item => String(item.unidade || "") === filtroUnidade);
  }

  if (filtroDoutor) {
    registros = registros.filter(item => String(item.doutor_final || "") === filtroDoutor);
    saldos = saldos.filter(item => String(item.doutor || "") === filtroDoutor);
  } else {
    const doutoresVisiveis = new Set(registros.map(item => item.doutor_final));
    saldos = saldos.filter(item => doutoresVisiveis.has(item.doutor));
  }

  return { competencia, resumo, registros, erros, saldos };
}

function renderCards(registros, competencia) {
  const alvo = document.getElementById("cardsResumo");

  const totalLancamentos = registros.length;
  const totalValor = registros.reduce((acc, item) => acc + Number(item.valor || 0), 0);
  const totalDescontado = registros.reduce((acc, item) => acc + Number(item.valor_descontado || 0), 0);
  const totalPendente = registros.reduce((acc, item) => acc + Number(item.pendente || 0), 0);
  const totalUnidades = new Set(registros.map(item => item.unidade).filter(Boolean)).size;
  const totalDoutores = new Set(registros.map(item => item.doutor_final).filter(Boolean)).size;

  alvo.innerHTML = `
    <div class="stat-card">
      <div class="stat-title">Competência</div>
      <div class="stat-value">${escapeHtml(formatarCompetenciaLabel(competencia))}</div>
    </div>
    <div class="stat-card">
      <div class="stat-title">Lançamentos</div>
      <div class="stat-value">${totalLancamentos}</div>
    </div>
    <div class="stat-card">
      <div class="stat-title">Valor total</div>
      <div class="stat-value">${formatarMoeda(totalValor)}</div>
    </div>
    <div class="stat-card">
      <div class="stat-title">Total descontado</div>
      <div class="stat-value">${formatarMoeda(totalDescontado)}</div>
    </div>
    <div class="stat-card">
      <div class="stat-title">Total pendente</div>
      <div class="stat-value">${formatarMoeda(totalPendente)}</div>
    </div>
    <div class="stat-card">
      <div class="stat-title">Unidades / Doutores</div>
      <div class="stat-value">${totalUnidades} / ${totalDoutores}</div>
    </div>
  `;
}

function renderResumoDoutor(registros, saldos) {
  const tbody = document.getElementById("tabelaResumoDoutor");

  if (!saldos.length) {
    tbody.innerHTML = `<tr><td colspan="6" class="empty-state">Sem dados</td></tr>`;
    return;
  }

  const utilizadoPorDoutor = {};

  for (const item of registros) {
    const chave = item.doutor_final || "Não informado";
    utilizadoPorDoutor[chave] = (utilizadoPorDoutor[chave] || 0) + Number(item.valor_descontado || 0);
  }

  const linhas = saldos
    .map(item => {
      const creditoInicial = Number(item.credito_inicial || 0);
      const creditoDisponivel = Number(item.credito_disponivel || 0);
      const utilizado = Number(utilizadoPorDoutor[item.doutor] || 0);
      const percentual = obterPercentual(utilizado, creditoInicial);
      const status = obterStatus(percentual);

      return {
        doutor: item.doutor,
        creditoInicial,
        utilizado,
        creditoDisponivel,
        percentual,
        status
      };
    })
    .sort((a, b) => b.percentual - a.percentual);

  tbody.innerHTML = linhas.map(item => `
    <tr>
      <td>${escapeHtml(item.doutor)}</td>
      <td>${formatarMoeda(item.creditoInicial)}</td>
      <td>${formatarMoeda(item.utilizado)}</td>
      <td>${formatarMoeda(item.creditoDisponivel)}</td>
      <td>${item.percentual.toFixed(1)}%</td>
      <td>
        <span class="status-pill ${item.status.classe}">
          <span class="dot ${item.status.dot}"></span>
          ${item.status.texto}
        </span>
      </td>
    </tr>
  `).join("");
}

function renderUnidades(registros) {
  const tbody = document.getElementById("tabelaUnidades");

  if (!registros.length) {
    tbody.innerHTML = `<tr><td colspan="5" class="empty-state">Sem dados</td></tr>`;
    return;
  }

  const mapa = {};

  for (const item of registros) {
    const unidade = item.unidade || "Sem unidade";

    if (!mapa[unidade]) {
      mapa[unidade] = {
        unidade,
        quantidade: 0,
        valor: 0,
        descontado: 0,
        pendente: 0
      };
    }

    mapa[unidade].quantidade += 1;
    mapa[unidade].valor += Number(item.valor || 0);
    mapa[unidade].descontado += Number(item.valor_descontado || 0);
    mapa[unidade].pendente += Number(item.pendente || 0);
  }

  tbody.innerHTML = Object.values(mapa)
    .sort((a, b) => a.unidade.localeCompare(b.unidade))
    .map(item => `
      <tr>
        <td>${escapeHtml(item.unidade)}</td>
        <td>${item.quantidade}</td>
        <td>${formatarMoeda(item.valor)}</td>
        <td>${formatarMoeda(item.descontado)}</td>
        <td class="${item.pendente > 0 ? 'text-warning' : 'text-success'}">${formatarMoeda(item.pendente)}</td>
      </tr>
    `).join("");
}

function renderRegistros(registros) {
  const tbody = document.getElementById("tabelaRegistros");

  if (!registros.length) {
    tbody.innerHTML = `<tr><td colspan="7" class="empty-state">Sem dados</td></tr>`;
    return;
  }

  tbody.innerHTML = registros
    .slice()
    .sort((a, b) => String(b.data || "").localeCompare(String(a.data || "")))
    .map(item => `
      <tr>
        <td>${escapeHtml(item.data)}</td>
        <td>${escapeHtml(item.unidade)}</td>
        <td>${escapeHtml(item.doutor_final)}</td>
        <td>${escapeHtml(item.paciente)}</td>
        <td>${formatarMoeda(item.valor)}</td>
        <td>${formatarMoeda(item.valor_descontado)}</td>
        <td class="${Number(item.pendente || 0) > 0 ? 'text-warning' : 'text-success'}">
          ${formatarMoeda(item.pendente)}
        </td>
      </tr>
    `).join("");
}

function renderErros(erros) {
  const tbody = document.getElementById("tabelaErros");

  if (!erros.length) {
    tbody.innerHTML = `<tr><td colspan="3" class="empty-state">Sem erros</td></tr>`;
    return;
  }

  tbody.innerHTML = erros.map(item => `
    <tr>
      <td>${escapeHtml(item.unidade)}</td>
      <td class="text-danger">${escapeHtml(item.erro)}</td>
      <td>${escapeHtml(item.coletado_em)}</td>
    </tr>
  `).join("");
}

function atualizarTela() {
  const { competencia, registros, erros, saldos } = obterDadosFiltrados();

  renderCards(registros, competencia);
  renderResumoDoutor(registros, saldos);
  renderUnidades(registros);
  renderRegistros(registros);
  renderErros(erros);

  document.getElementById("badgeCompetencia").textContent = formatarCompetenciaLabel(competencia);
}

function exportarCSV() {
  const { registros, competencia } = obterDadosFiltrados();

  if (!registros.length) {
    alert("Não há dados para exportar.");
    return;
  }

  const headers = [
    "competencia",
    "data",
    "unidade",
    "responsavel_fiscal",
    "doutor_final",
    "paciente",
    "valor",
    "valor_descontado",
    "pendente"
  ];

  const rows = registros.map(item => [
    item.competencia ?? "",
    item.data ?? "",
    item.unidade ?? "",
    item.responsavel_fiscal_lido ?? "",
    item.doutor_final ?? "",
    item.paciente ?? "",
    item.valor ?? 0,
    item.valor_descontado ?? 0,
    item.pendente ?? 0
  ]);

  const csv = [headers, ...rows]
    .map(row => row.map(value => `"${String(value).replace(/"/g, '""')}"`).join(";"))
    .join("\n");

  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `pix_doutores_${competencia || "2026"}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

async function carregarDashboard() {
  try {
    const resposta = await fetch("./data/dashboard_data.json", { cache: "no-store" });

    if (!resposta.ok) {
      throw new Error(`Arquivo não encontrado: ${resposta.status}`);
    }

    dashboardData = await resposta.json();

    document.getElementById("tituloDashboard").textContent =
      dashboardData.titulo_dashboard || "Painel Gerencial";

    document.getElementById("subtituloDashboard").textContent =
      `Acompanhamento mensal de crédito PIX por doutor - ano ${dashboardData.ano_referencia || 2026}`;

    document.getElementById("badgeArquivo").textContent =
      dashboardData?.arquivo_origem
        ? `Base: ${dashboardData.arquivo_origem}`
        : "Base não informada";

    preencherFiltros(dashboardData);
    atualizarTela();

    document.getElementById("filtroMes").addEventListener("change", atualizarTela);
    document.getElementById("filtroUnidade").addEventListener("change", atualizarTela);
    document.getElementById("filtroDoutor").addEventListener("change", atualizarTela);

    document.getElementById("btnLimpar").addEventListener("click", () => {
      document.getElementById("filtroMes").value = dashboardData?.competencia_padrao || "2026-01";
      document.getElementById("filtroUnidade").selectedIndex = 0;
      document.getElementById("filtroDoutor").selectedIndex = 0;
      atualizarTela();
    });

    document.getElementById("btnExportar").addEventListener("click", exportarCSV);
  } catch (erro) {
    console.error("Erro ao carregar dashboard:", erro);

    document.getElementById("cardsResumo").innerHTML = `
      <div class="error-box">
        <strong>Erro ao carregar dados</strong><br />
        Não foi possível carregar <code>data/dashboard_data.json</code>.<br /><br />
        Rode:
        <br /><code>python coletor_pix.py</code>
        <br /><code>python generate_data.py</code>
      </div>
    `;
  }
}

carregarDashboard();
