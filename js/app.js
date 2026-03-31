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

  const competencia = data?.resumo?.competencia || "";
  filtroMes.innerHTML = `<option value="">Todos</option>`;
  if (competencia) {
    filtroMes.innerHTML += `<option value="${escapeHtml(competencia)}">${escapeHtml(competencia)}</option>`;
    filtroMes.value = competencia;
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
  const filtroMes = document.getElementById("filtroMes").value;
  const filtroUnidade = document.getElementById("filtroUnidade").value;
  const filtroDoutor = document.getElementById("filtroDoutor").value;

  let registros = [...(dashboardData?.registros || [])];
  let saldos = [...(dashboardData?.saldos_doutores || [])];
  let erros = [...(dashboardData?.erros || [])];

  if (filtroMes) {
    registros = registros.filter(item => String(item.competencia || "") === filtroMes);
  }

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

  return { registros, saldos, erros };
}

function renderCards(registros) {
  const alvo = document.getElementById("cardsResumo");

  const totalLancamentos = registros.length;
  const totalValor = registros.reduce((acc, item) => acc + Number(item.valor || 0), 0);
  const totalDescontado = registros.reduce((acc, item) => acc + Number(item.valor_descontado || 0), 0);
  const totalPendente = registros.reduce((acc, item) => acc + Number(item.pendente || 0), 0);
  const totalUnidades = new Set(registros.map(item => item.unidade).filter(Boolean)).size;
  const totalDoutores = new Set(registros.map(item => item.doutor_final).filter(Boolean)).size;

  alvo.innerHTML = `
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
      <div class="stat-title">Unidades</div>
      <div class="stat-value">${totalUnidades}</div>
    </div>
    <div class="stat-card">
      <div class="stat-title">Doutores</div>
      <div class="stat-value">${totalDoutores}</div>
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
    .sort((a, b) => {
      const da = String(a.data || "");
      const db = String(b.data || "");
      return db.localeCompare(da);
    })
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
  const { registros, saldos, erros } = obterDadosFiltrados();
  renderCards(registros);
  renderResumoDoutor(registros, saldos);
  renderUnidades(registros);
  renderRegistros(registros);
  renderErros(erros);
}

function exportarCSV() {
  const { registros } = obterDadosFiltrados();

  if (!registros.length) {
    alert("Não há dados para exportar.");
    return;
  }

  const headers = [
    "data",
    "unidade",
    "doutor",
    "paciente",
    "valor",
    "valor_descontado",
    "pendente"
  ];

  const rows = registros.map(item => [
    item.data ?? "",
    item.unidade ?? "",
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
  link.download = "pix_doutores.csv";
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
      "Acompanhamento mensal de crédito PIX por doutor";

    document.getElementById("badgeCompetencia").textContent =
      dashboardData?.resumo?.competencia || "Competência";

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
      document.getElementById("filtroMes").selectedIndex = 0;
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
        Não foi possível carregar <code>data/dashboard_data.json</code>.<br />
        Gere os arquivos com:
        <br /><br />
        <code>python coletor_pix.py</code><br />
        <code>python generate_data.py</code>
        <br /><br />
        E abra o projeto via servidor local:
        <br />
        <code>python -m http.server 8000</code>
      </div>
    `;
  }
}

carregarDashboard();
