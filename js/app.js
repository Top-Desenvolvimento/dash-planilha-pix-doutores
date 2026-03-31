function formatarMoeda(valor) {
  const numero = Number(valor || 0);
  return numero.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}

function escapeHtml(texto) {
  return String(texto ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function criarCardsResumo(resumo) {
  const cards = document.getElementById("cardsResumo");

  const quantidadeTotal = resumo?.quantidade_total ?? 0;
  const valorTotal = resumo?.valor_total ?? 0;
  const totalDescontado = resumo?.valor_total_descontado ?? 0;
  const totalPendente = resumo?.valor_total_pendente ?? 0;
  const competencia = resumo?.competencia ?? "-";
  const geradoEm = resumo?.gerado_em ?? "-";

  cards.innerHTML = `
    <div class="card">
      <div class="card-titulo">Competência</div>
      <div class="card-valor">${escapeHtml(competencia)}</div>
    </div>
    <div class="card">
      <div class="card-titulo">Linhas coletadas</div>
      <div class="card-valor">${quantidadeTotal}</div>
    </div>
    <div class="card">
      <div class="card-titulo">Valor total</div>
      <div class="card-valor">${formatarMoeda(valorTotal)}</div>
    </div>
    <div class="card">
      <div class="card-titulo">Total descontado</div>
      <div class="card-valor positivo">${formatarMoeda(totalDescontado)}</div>
    </div>
    <div class="card">
      <div class="card-titulo">Total pendente</div>
      <div class="card-valor alerta">${formatarMoeda(totalPendente)}</div>
    </div>
    <div class="card">
      <div class="card-titulo">Gerado em</div>
      <div class="card-valor pequeno">${escapeHtml(geradoEm)}</div>
    </div>
  `;
}

function preencherTabelaUnidades(lista) {
  const tbody = document.getElementById("tabelaUnidades");

  if (!lista || !lista.length) {
    tbody.innerHTML = `<tr><td colspan="5" class="texto-centro">Sem dados</td></tr>`;
    return;
  }

  tbody.innerHTML = lista.map(item => `
    <tr>
      <td>${escapeHtml(item.unidade)}</td>
      <td>${item.quantidade ?? 0}</td>
      <td>${formatarMoeda(item.valor)}</td>
      <td>${formatarMoeda(item.descontado)}</td>
      <td>${formatarMoeda(item.pendente)}</td>
    </tr>
  `).join("");
}

function preencherTabelaDoutores(lista) {
  const tbody = document.getElementById("tabelaDoutores");

  if (!lista || !lista.length) {
    tbody.innerHTML = `<tr><td colspan="5" class="texto-centro">Sem dados</td></tr>`;
    return;
  }

  tbody.innerHTML = lista.map(item => `
    <tr>
      <td>${escapeHtml(item.doutor)}</td>
      <td>${item.quantidade ?? 0}</td>
      <td>${formatarMoeda(item.valor)}</td>
      <td>${formatarMoeda(item.descontado)}</td>
      <td>${formatarMoeda(item.pendente)}</td>
    </tr>
  `).join("");
}

function preencherTabelaSaldos(lista) {
  const tbody = document.getElementById("tabelaSaldos");

  if (!lista || !lista.length) {
    tbody.innerHTML = `<tr><td colspan="3" class="texto-centro">Sem dados</td></tr>`;
    return;
  }

  tbody.innerHTML = lista.map(item => {
    const credito = Number(item.credito_disponivel || 0);
    const classe = credito <= 0 ? "texto-zerado" : "texto-ok";

    return `
      <tr>
        <td>${escapeHtml(item.doutor)}</td>
        <td>${formatarMoeda(item.credito_inicial)}</td>
        <td class="${classe}">${formatarMoeda(item.credito_disponivel)}</td>
      </tr>
    `;
  }).join("");
}

function preencherTabelaRegistros(lista) {
  const tbody = document.getElementById("tabelaRegistros");

  if (!lista || !lista.length) {
    tbody.innerHTML = `<tr><td colspan="7" class="texto-centro">Sem dados</td></tr>`;
    return;
  }

  tbody.innerHTML = lista.map(item => {
    const pendente = Number(item.pendente || 0);
    const classePendente = pendente > 0 ? "texto-alerta" : "texto-ok";

    return `
      <tr>
        <td>${escapeHtml(item.unidade)}</td>
        <td>${escapeHtml(item.data)}</td>
        <td>${escapeHtml(item.doutor_final)}</td>
        <td>${escapeHtml(item.paciente)}</td>
        <td>${formatarMoeda(item.valor)}</td>
        <td>${formatarMoeda(item.valor_descontado)}</td>
        <td class="${classePendente}">${formatarMoeda(item.pendente)}</td>
      </tr>
    `;
  }).join("");
}

function preencherTabelaErros(lista) {
  const tbody = document.getElementById("tabelaErros");

  if (!lista || !lista.length) {
    tbody.innerHTML = `<tr><td colspan="3" class="texto-centro">Sem erros</td></tr>`;
    return;
  }

  tbody.innerHTML = lista.map(item => `
    <tr>
      <td>${escapeHtml(item.unidade)}</td>
      <td>${escapeHtml(item.erro)}</td>
      <td>${escapeHtml(item.coletado_em)}</td>
    </tr>
  `).join("");
}

async function carregarDashboard() {
  try {
    const resposta = await fetch("data/dashboard_data.json");
    const data = await resposta.json();

    criarCardsResumo(data.resumo || {});
    preencherTabelaUnidades(data.resumo?.por_unidade || []);
    preencherTabelaDoutores(data.resumo?.por_doutor || []);
    preencherTabelaSaldos(data.saldos_doutores || []);
    preencherTabelaRegistros(data.registros || []);
    preencherTabelaErros(data.erros || []);
  } catch (erro) {
    console.error("Erro ao carregar dashboard:", erro);

    document.getElementById("cardsResumo").innerHTML = `
      <div class="card">
        <div class="card-titulo">Erro</div>
        <div class="card-valor pequeno">Não foi possível carregar data/dashboard_data.json</div>
      </div>
    `;
  }
}

carregarDashboard();
