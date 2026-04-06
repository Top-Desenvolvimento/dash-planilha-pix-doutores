let dashboardData = null;
let currentUser = null;
let currentUserIsAdmin = false;

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

function normalizarNome(nome) {
  return String(nome || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/\s+/g, " ")
    .trim();
}

function mostrarMensagemAuth(texto, erro = false) {
  const el = document.getElementById("authMessage");
  if (!el) return;
  el.textContent = texto || "";
  el.className = erro ? "auth-message error" : "auth-message";
}

function mostrarMensagemAdmin(texto, erro = false) {
  const el = document.getElementById("adminMessage");
  if (!el) return;
  el.textContent = texto || "";
  el.className = erro ? "auth-message error" : "auth-message";
}

function mostrarTelaLogin() {
  document.getElementById("authScreen")?.classList.remove("hidden");
  document.getElementById("appRoot")?.classList.add("hidden");
}

function mostrarApp() {
  document.getElementById("authScreen")?.classList.add("hidden");
  document.getElementById("appRoot")?.classList.remove("hidden");
}

function mostrarDashboard() {
  document.getElementById("dashboardView")?.classList.remove("hidden");
  document.getElementById("adminView")?.classList.add("hidden");
  document.getElementById("filtrosSidebar")?.classList.remove("hidden");
}

function mostrarAdmin() {
  document.getElementById("dashboardView")?.classList.add("hidden");
  document.getElementById("adminView")?.classList.remove("hidden");
  document.getElementById("filtrosSidebar")?.classList.add("hidden");
}

async function validarUsuarioAutorizado() {
  const { data, error } = await supabaseClient.rpc("usuario_esta_autorizado");
  if (error) throw error;
  return data === true;
}

async function validarUsuarioAdmin() {
  const { data, error } = await supabaseClient.rpc("usuario_eh_admin");
  if (error) throw error;
  return data === true;
}

async function loginSupabase(email, password) {
  const { error } = await supabaseClient.auth.signInWithPassword({ email, password });
  if (error) throw error;

  const autorizado = await validarUsuarioAutorizado();
  if (!autorizado) {
    await supabaseClient.auth.signOut();
    throw new Error("Seu usuário não está autorizado para acessar esta dashboard.");
  }
}

async function logoutSupabase() {
  await supabaseClient.auth.signOut();
}

async function enviarRecuperacaoSenha(email) {
  const base = window.location.origin + window.location.pathname.replace(/\/index\.html$/, "");
  const redirectTo = `${base}/reset.html`;

  const { error } = await supabaseClient.auth.resetPasswordForEmail(email, { redirectTo });
  if (error) throw error;
}

function preencherBadgeUsuario() {
  const badge = document.getElementById("badgeUsuario");
  if (!badge) return;
  badge.textContent = currentUser?.email || "Usuário";
}

function getCompetenciaAtual() {
  const filtroMes = document.getElementById("filtroMes");
  return filtroMes?.value || dashboardData?.competencia_padrao || "2026-01";
}

function getRegistrosDaCompetencia(competencia) {
  if (dashboardData?.registros_por_competencia?.[competencia]) {
    return [...dashboardData.registros_por_competencia[competencia]];
  }

  const registros = Array.isArray(dashboardData?.registros) ? dashboardData.registros : [];
  return registros.filter(item => String(item.competencia || "") === competencia);
}

function getErrosDaCompetencia(competencia) {
  if (dashboardData?.erros_por_competencia?.[competencia]) {
    return [...dashboardData.erros_por_competencia[competencia]];
  }

  const erros = Array.isArray(dashboardData?.erros) ? dashboardData.erros : [];
  return erros.filter(item => String(item.competencia || "") === competencia);
}

function getSaldosDaCompetencia(competencia) {
  const saldos = dashboardData?.saldos_por_competencia?.[competencia];
  return Array.isArray(saldos) ? [...saldos] : [];
}

function preencherFiltroMes() {
  const filtroMes = document.getElementById("filtroMes");
  if (!filtroMes) return;

  const meses = dashboardData?.meses_disponiveis || [];
  const competenciaPadrao = dashboardData?.competencia_padrao || "";

  filtroMes.innerHTML = meses
    .map(item => `<option value="${escapeHtml(item)}">${escapeHtml(formatarCompetenciaLabel(item))}</option>`)
    .join("");

  if (competenciaPadrao && meses.includes(competenciaPadrao)) {
    filtroMes.value = competenciaPadrao;
  } else if (meses.length) {
    filtroMes.value = meses[0];
  }
}

function preencherFiltrosSecundarios() {
  const filtroUnidade = document.getElementById("filtroUnidade");
  const filtroDoutor = document.getElementById("filtroDoutor");
  if (!filtroUnidade || !filtroDoutor) return;

  const unidadeSelecionada = filtroUnidade.value;
  const doutorSelecionado = filtroDoutor.value;

  const competencia = getCompetenciaAtual();
  const registrosMes = getRegistrosDaCompetencia(competencia);

  const unidades = [...new Set(registrosMes.map(item => item.unidade).filter(Boolean))].sort();
  const doutores = [...new Set(registrosMes.map(item => item.doutor_final).filter(Boolean))].sort();

  filtroUnidade.innerHTML =
    `<option value="">Todas</option>` +
    unidades.map(item => `<option value="${escapeHtml(item)}">${escapeHtml(item)}</option>`).join("");

  filtroDoutor.innerHTML =
    `<option value="">Todos</option>` +
    doutores.map(item => `<option value="${escapeHtml(item)}">${escapeHtml(item)}</option>`).join("");

  if (unidades.includes(unidadeSelecionada)) {
    filtroUnidade.value = unidadeSelecionada;
  }

  if (doutores.includes(doutorSelecionado)) {
    filtroDoutor.value = doutorSelecionado;
  }
}

function obterDadosFiltrados() {
  const competencia = getCompetenciaAtual();
  const filtroUnidade = document.getElementById("filtroUnidade")?.value || "";
  const filtroDoutor = document.getElementById("filtroDoutor")?.value || "";

  let registros = getRegistrosDaCompetencia(competencia);
  let erros = getErrosDaCompetencia(competencia);
  let saldos = getSaldosDaCompetencia(competencia);

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

  return { competencia, registros, erros, saldos };
}

function obterPercentual(utilizado, creditoInicial) {
  const credito = Number(creditoInicial || 0);
  if (credito <= 0) return 0;
  return (Number(utilizado || 0) / credito) * 100;
}

function obterStatus(percentual) {
  if (percentual >= 100) return { classe: "status-red", texto: "Limite atingido", dot: "dot-red" };
  if (percentual >= 50) return { classe: "status-yellow", texto: "Atenção", dot: "dot-yellow" };
  return { classe: "status-green", texto: "Controlado", dot: "dot-green" };
}

function renderCards(registros, competencia) {
  const alvo = document.getElementById("cardsResumo");
  if (!alvo) return;

  const totalLancamentos = registros.length;
  const totalValor = registros.reduce((acc, item) => acc + Number(item.valor || 0), 0);
  const totalDescontado = registros.reduce((acc, item) => acc + Number(item.valor_descontado || 0), 0);
  const totalPendente = registros.reduce((acc, item) => acc + Number(item.pendente || 0), 0);
  const totalUnidades = new Set(registros.map(item => item.unidade).filter(Boolean)).size;
  const totalDoutores = new Set(registros.map(item => item.doutor_final).filter(Boolean)).size;

  alvo.innerHTML = `
    <div class="stat-card"><div class="stat-title">Competência</div><div class="stat-value">${escapeHtml(formatarCompetenciaLabel(competencia))}</div></div>
    <div class="stat-card"><div class="stat-title">Lançamentos</div><div class="stat-value">${totalLancamentos}</div></div>
    <div class="stat-card"><div class="stat-title">Valor total</div><div class="stat-value">${formatarMoeda(totalValor)}</div></div>
    <div class="stat-card"><div class="stat-title">Total descontado</div><div class="stat-value">${formatarMoeda(totalDescontado)}</div></div>
    <div class="stat-card"><div class="stat-title">Total pendente</div><div class="stat-value">${formatarMoeda(totalPendente)}</div></div>
    <div class="stat-card"><div class="stat-title">Unidades / Doutores</div><div class="stat-value">${totalUnidades} / ${totalDoutores}</div></div>
  `;
}

function renderResumoDoutor(registros, saldos) {
  const tbody = document.getElementById("tabelaResumoDoutor");
  if (!tbody) return;

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

      return { doutor: item.doutor, creditoInicial, utilizado, creditoDisponivel, percentual, status };
    })
    .sort((a, b) => b.percentual - a.percentual);

  tbody.innerHTML = linhas.map(item => `
    <tr>
      <td>${escapeHtml(item.doutor)}</td>
      <td>${formatarMoeda(item.creditoInicial)}</td>
      <td>${formatarMoeda(item.utilizado)}</td>
      <td>${formatarMoeda(item.creditoDisponivel)}</td>
      <td>${item.percentual.toFixed(1)}%</td>
      <td><span class="status-pill ${item.status.classe}"><span class="dot ${item.status.dot}"></span>${item.status.texto}</span></td>
    </tr>
  `).join("");
}

function renderUnidades(registros) {
  const tbody = document.getElementById("tabelaUnidades");
  if (!tbody) return;

  if (!registros.length) {
    tbody.innerHTML = `<tr><td colspan="5" class="empty-state">Sem dados</td></tr>`;
    return;
  }

  const mapa = {};
  for (const item of registros) {
    const unidade = item.unidade || "Sem unidade";
    if (!mapa[unidade]) mapa[unidade] = { unidade, quantidade: 0, valor: 0, descontado: 0, pendente: 0 };

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
  if (!tbody) return;

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
        <td>${escapeHtml(item.doutor_final || "Sem responsável fiscal")}</td>
        <td>${escapeHtml(item.paciente)}</td>
        <td>${formatarMoeda(item.valor)}</td>
        <td>${formatarMoeda(item.valor_descontado)}</td>
        <td class="${Number(item.pendente || 0) > 0 ? 'text-warning' : 'text-success'}">${formatarMoeda(item.pendente)}</td>
      </tr>
    `).join("");
}

function renderErros(erros) {
  const tbody = document.getElementById("tabelaErros");
  if (!tbody) return;

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

  const badge = document.getElementById("badgeCompetencia");
  if (badge) badge.textContent = formatarCompetenciaLabel(competencia);
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
    "pendente",
    "possui_responsavel_fiscal"
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
    item.pendente ?? 0,
    item.possui_responsavel_fiscal ?? false
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

async function carregarDashboardInterno() {
  const resposta = await fetch("./data/dashboard_data.json", { cache: "no-store" });
  if (!resposta.ok) throw new Error(`Arquivo não encontrado: ${resposta.status}`);

  dashboardData = await resposta.json();

  document.getElementById("tituloDashboard").textContent =
    dashboardData.titulo_dashboard || "Painel Gerencial";

  document.getElementById("subtituloDashboard").textContent =
    `Acompanhamento mensal de crédito PIX por doutor - ano ${dashboardData.ano_referencia || 2026}`;

  document.getElementById("badgeArquivo").textContent =
    dashboardData?.arquivo_origem ? `Base: ${dashboardData.arquivo_origem}` : "Base não informada";

  preencherBadgeUsuario();
  preencherFiltroMes();
  preencherFiltrosSecundarios();
  atualizarTela();
}

async function carregarDoutoresAdmin() {
  const tbody = document.getElementById("tabelaAdminDoutores");
  if (!tbody) return;

  tbody.innerHTML = `<tr><td colspan="7" class="empty-state">Carregando...</td></tr>`;

  const { data, error } = await supabaseClient
    .from("doutores_config")
    .select("*")
    .order("nome", { ascending: true });

  if (error) {
    console.error(error);
    tbody.innerHTML = `<tr><td colspan="7" class="empty-state">Erro ao carregar doutores</td></tr>`;
    return;
  }

  if (!data.length) {
    tbody.innerHTML = `<tr><td colspan="7" class="empty-state">Nenhum doutor cadastrado</td></tr>`;
    return;
  }

  tbody.innerHTML = data.map(item => `
    <tr>
      <td><input data-id="${item.id}" data-field="nome" type="text" value="${escapeHtml(item.nome)}" /></td>
      <td><input data-id="${item.id}" data-field="credito" type="number" step="0.01" value="${Number(item.credito || 0)}" /></td>
      <td><input data-id="${item.id}" data-field="pix_key" type="text" value="${escapeHtml(item.pix_key || "")}" /></td>
      <td>
        <select data-id="${item.id}" data-field="ativo">
          <option value="true" ${item.ativo ? "selected" : ""}>Ativo</option>
          <option value="false" ${!item.ativo ? "selected" : ""}>Inativo</option>
        </select>
      </td>
      <td>${escapeHtml(item.updated_at || "")}</td>
      <td>${escapeHtml(item.updated_by_email || "")}</td>
      <td>
        <button class="btn btn-primary btn-small" onclick="salvarDoutor('${item.id}')">Salvar</button>
        <button class="btn btn-secondary btn-small" onclick="removerDoutor('${item.id}')">Excluir</button>
      </td>
    </tr>
  `).join("");
}

async function salvarDoutor(id) {
  try {
    mostrarMensagemAdmin("");

    const nome = document.querySelector(`[data-id="${id}"][data-field="nome"]`).value.trim();
    const credito = parseFloat(document.querySelector(`[data-id="${id}"][data-field="credito"]`).value || "0");
    const pixKey = document.querySelector(`[data-id="${id}"][data-field="pix_key"]`).value.trim();
    const ativo = document.querySelector(`[data-id="${id}"][data-field="ativo"]`).value === "true";

    if (!nome) {
      mostrarMensagemAdmin("Nome é obrigatório.", true);
      return;
    }

    const payload = {
      nome,
      nome_normalizado: normalizarNome(nome),
      credito,
      pix_key: pixKey || null,
      ativo
    };

    const { error } = await supabaseClient
      .from("doutores_config")
      .update(payload)
      .eq("id", id);

    if (error) throw error;

    mostrarMensagemAdmin("Doutor salvo com sucesso.");
    await carregarDoutoresAdmin();
  } catch (err) {
    console.error(err);
    mostrarMensagemAdmin("Erro ao salvar doutor.", true);
  }
}

async function removerDoutor(id) {
  if (!confirm("Tem certeza que deseja excluir este doutor?")) return;

  try {
    const { error } = await supabaseClient
      .from("doutores_config")
      .delete()
      .eq("id", id);

    if (error) throw error;

    mostrarMensagemAdmin("Doutor removido com sucesso.");
    await carregarDoutoresAdmin();
  } catch (err) {
    console.error(err);
    mostrarMensagemAdmin("Erro ao remover doutor.", true);
  }
}

async function adicionarDoutor() {
  try {
    mostrarMensagemAdmin("");

    const nome = document.getElementById("novoNome")?.value.trim() || "";
    const credito = parseFloat(document.getElementById("novoCredito")?.value || "0");
    const pixKey = document.getElementById("novaPixKey")?.value.trim() || "";
    const ativo = document.getElementById("novoAtivo")?.value === "true";

    if (!nome) {
      mostrarMensagemAdmin("Informe o nome do doutor.", true);
      return;
    }

    const payload = {
      nome,
      nome_normalizado: normalizarNome(nome),
      credito,
      pix_key: pixKey || null,
      ativo
    };

    const { error } = await supabaseClient
      .from("doutores_config")
      .insert(payload);

    if (error) throw error;

    document.getElementById("novoNome").value = "";
    document.getElementById("novoCredito").value = "";
    document.getElementById("novaPixKey").value = "";
    document.getElementById("novoAtivo").value = "true";

    mostrarMensagemAdmin("Doutor adicionado com sucesso.");
    await carregarDoutoresAdmin();
  } catch (err) {
    console.error(err);
    mostrarMensagemAdmin("Erro ao adicionar doutor.", true);
  }
}

async function iniciarAplicacao() {
  try {
    const { data, error } = await supabaseClient.auth.getSession();
    if (error) throw error;

    const session = data?.session || null;

    if (!session) {
      mostrarTelaLogin();
      return;
    }

    const autorizado = await validarUsuarioAutorizado();
    if (!autorizado) {
      await supabaseClient.auth.signOut();
      mostrarTelaLogin();
      mostrarMensagemAuth("Usuário sem permissão de acesso.", true);
      return;
    }

    currentUser = session.user;
    currentUserIsAdmin = await validarUsuarioAdmin();

    if (currentUserIsAdmin) {
      document.getElementById("btnTabAdmin")?.classList.remove("hidden");
    }

    mostrarApp();
    mostrarDashboard();
    await carregarDashboardInterno();
  } catch (erro) {
    console.error("Erro ao iniciar app:", erro);
    mostrarTelaLogin();
    mostrarMensagemAuth("Erro ao validar acesso.", true);
  }
}

document.getElementById("loginForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();

  const email = document.getElementById("email")?.value.trim() || "";
  const password = document.getElementById("password")?.value.trim() || "";

  mostrarMensagemAuth("");

  try {
    await loginSupabase(email, password);

    const { data } = await supabaseClient.auth.getUser();
    currentUser = data?.user || null;
    currentUserIsAdmin = await validarUsuarioAdmin();

    if (currentUserIsAdmin) {
      document.getElementById("btnTabAdmin")?.classList.remove("hidden");
    }

    mostrarApp();
    mostrarDashboard();
    await carregarDashboardInterno();
  } catch (erro) {
    console.error(erro);
    mostrarMensagemAuth(erro.message || "Não foi possível entrar.", true);
  }
});

document.getElementById("btnForgotPassword")?.addEventListener("click", async () => {
  const email = document.getElementById("email")?.value.trim() || "";

  if (!email) {
    mostrarMensagemAuth("Digite seu e-mail para recuperar a senha.", true);
    return;
  }

  try {
    await enviarRecuperacaoSenha(email);
    mostrarMensagemAuth("Enviamos um link de recuperação para seu e-mail.");
  } catch (erro) {
    console.error(erro);
    mostrarMensagemAuth("Não foi possível enviar o e-mail de recuperação.", true);
  }
});

document.getElementById("btnLogout")?.addEventListener("click", async () => {
  await logoutSupabase();
  currentUser = null;
  currentUserIsAdmin = false;
  dashboardData = null;
  mostrarTelaLogin();
});

document.getElementById("btnTabDashboard")?.addEventListener("click", () => {
  mostrarDashboard();
});

document.getElementById("btnTabAdmin")?.addEventListener("click", async () => {
  if (!currentUserIsAdmin) return;
  mostrarAdmin();
  await carregarDoutoresAdmin();
});

document.getElementById("btnAdicionarDoutor")?.addEventListener("click", adicionarDoutor);

document.getElementById("filtroMes")?.addEventListener("change", () => {
  preencherFiltrosSecundarios();
  atualizarTela();
});

document.getElementById("filtroUnidade")?.addEventListener("change", atualizarTela);
document.getElementById("filtroDoutor")?.addEventListener("change", atualizarTela);

document.getElementById("btnLimpar")?.addEventListener("click", () => {
  const filtroMes = document.getElementById("filtroMes");
  if (filtroMes) {
    filtroMes.value = dashboardData?.competencia_padrao || "2026-01";
  }

  preencherFiltrosSecundarios();

  const filtroUnidade = document.getElementById("filtroUnidade");
  const filtroDoutor = document.getElementById("filtroDoutor");

  if (filtroUnidade) filtroUnidade.selectedIndex = 0;
  if (filtroDoutor) filtroDoutor.selectedIndex = 0;

  atualizarTela();
});

document.getElementById("btnExportar")?.addEventListener("click", exportarCSV);

window.salvarDoutor = salvarDoutor;
window.removerDoutor = removerDoutor;

iniciarAplicacao();
