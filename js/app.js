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

function getBaseAppUrl() {
  const { origin, pathname } = window.location;

  if (pathname.endsWith("/reset.html")) {
    return `${origin}${pathname.replace(/reset\.html$/, "")}`;
  }

  if (pathname.endsWith("/index.html")) {
    return `${origin}${pathname.replace(/index\.html$/, "")}`;
  }

  return `${origin}${pathname.endsWith("/") ? pathname : pathname + "/"}`;
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

async function emailPodeCadastrar(email) {
  const { data, error } = await supabaseClient.rpc("email_pode_cadastrar", {
    p_email: email
  });
  if (error) throw error;
  return data === true;
}

async function loginSupabase(email, password) {
  const { error } = await supabaseClient.auth.signInWithPassword({
    email,
    password
  });

  if (error) throw error;

  const autorizado = await validarUsuarioAutorizado();
  if (!autorizado) {
    await supabaseClient.auth.signOut();
    throw new Error("Seu usuário não está autorizado para acessar esta dashboard.");
  }
}

async function criarAcessoSupabase(email, password) {
  const permitido = await emailPodeCadastrar(email);

  if (!permitido) {
    throw new Error("Este e-mail não está autorizado para criar acesso.");
  }

  const redirectTo = getBaseAppUrl();

  const { error } = await supabaseClient.auth.signUp({
    email,
    password,
    options: {
      emailRedirectTo: redirectTo
    }
  });

  if (error) throw error;
}

async function logoutSupabase() {
  await supabaseClient.auth.signOut();
}

async function enviarRecuperacaoSenha(email) {
  const redirectTo = `${getBaseAppUrl()}reset.html`;

  const { error } = await supabaseClient.auth.resetPasswordForEmail(email, {
    redirectTo
  });

  if (error) throw error;
}

function preencherBadgeUsuario() {
  const badge = document.getElementById("badgeUsuario");
  if (badge) badge.textContent = currentUser?.email || "Usuário";
}

function getCompetenciaAtual() {
  return document.getElementById("filtroMes")?.value || dashboardData?.competencia_padrao || "2026-01";
}

function getCidadeAtual() {
  return document.getElementById("filtroCidade")?.value || "";
}

function getDoutorAtual() {
  return document.getElementById("filtroDoutor")?.value || "";
}

function getRegistrosCompetencia(competencia) {
  if (dashboardData?.registros_por_competencia?.[competencia]) {
    return [...dashboardData.registros_por_competencia[competencia]];
  }

  const registros = Array.isArray(dashboardData?.registros) ? dashboardData.registros : [];
  return registros.filter(item => String(item.competencia || "") === competencia);
}

function getSaldosCompetencia(competencia) {
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

function preencherFiltroCidade() {
  const filtroCidade = document.getElementById("filtroCidade");
  if (!filtroCidade) return;

  const cidadeSelecionada = filtroCidade.value;
  const competencia = getCompetenciaAtual();
  const registros = getRegistrosCompetencia(competencia);

  const cidades = [...new Set(registros.map(item => item.unidade).filter(Boolean))].sort();

  filtroCidade.innerHTML =
    `<option value="">Todas</option>` +
    cidades.map(item => `<option value="${escapeHtml(item)}">${escapeHtml(item)}</option>`).join("");

  if (cidades.includes(cidadeSelecionada)) {
    filtroCidade.value = cidadeSelecionada;
  }
}

function preencherFiltroDoutor() {
  const filtroDoutor = document.getElementById("filtroDoutor");
  if (!filtroDoutor) return;

  const selecionado = filtroDoutor.value;
  const competencia = getCompetenciaAtual();

  const registros = getRegistrosCompetencia(competencia);
  const saldos = getSaldosCompetencia(competencia);

  const nomesRegistros = registros.map(item => item.doutor_final).filter(Boolean);
  const nomesSaldos = saldos.map(item => item.doutor).filter(Boolean);

  const doutores = [...new Set([...nomesRegistros, ...nomesSaldos])].sort((a, b) =>
    a.localeCompare(b, "pt-BR")
  );

  filtroDoutor.innerHTML =
    `<option value="">Todos</option>` +
    doutores.map(item => `<option value="${escapeHtml(item)}">${escapeHtml(item)}</option>`).join("");

  if (doutores.includes(selecionado)) {
    filtroDoutor.value = selecionado;
  }
}

function getRegistrosFiltrados() {
  const competencia = getCompetenciaAtual();
  const cidade = getCidadeAtual();
  const doutor = getDoutorAtual();

  let registros = getRegistrosCompetencia(competencia);

  if (cidade) {
    registros = registros.filter(item => String(item.unidade || "") === cidade);
  }

  if (doutor) {
    registros = registros.filter(item => String(item.doutor_final || "") === doutor);
  }

  return registros;
}

function getSaldosFiltrados() {
  const competencia = getCompetenciaAtual();
  const doutor = getDoutorAtual();

  let saldos = getSaldosCompetencia(competencia);

  if (doutor) {
    saldos = saldos.filter(item => String(item.doutor || "") === doutor);
  }

  return saldos;
}

function obterPercentual(utilizado, creditoInicial) {
  const credito = Number(creditoInicial || 0);
  if (credito <= 0) return 0;
  return (Number(utilizado || 0) / credito) * 100;
}

function obterStatus(percentual) {
  if (percentual >= 100) return { classe: "status-red", texto: "Bloqueado", dot: "dot-red" };
  if (percentual >= 50) return { classe: "status-yellow", texto: "Atenção", dot: "dot-yellow" };
  return { classe: "status-green", texto: "Controlado", dot: "dot-green" };
}

function renderCards(registros) {
  const alvo = document.getElementById("cardsResumo");
  if (!alvo) return;

  const totalLancamentos = registros.length;
  const totalValor = registros.reduce((acc, item) => acc + Number(item.valor || 0), 0);
  const totalDescontado = registros.reduce((acc, item) => acc + Number(item.valor_descontado || 0), 0);
  const totalPendente = registros.reduce((acc, item) => acc + Number(item.pendente || 0), 0);
  const totalCidades = new Set(registros.map(item => item.unidade).filter(Boolean)).size;

  alvo.innerHTML = `
    <div class="stat-card"><div class="stat-title">Lançamentos</div><div class="stat-value">${totalLancamentos}</div></div>
    <div class="stat-card"><div class="stat-title">Valor total</div><div class="stat-value">${formatarMoeda(totalValor)}</div></div>
    <div class="stat-card"><div class="stat-title">Descontado</div><div class="stat-value">${formatarMoeda(totalDescontado)}</div></div>
    <div class="stat-card"><div class="stat-title">Pendente</div><div class="stat-value">${formatarMoeda(totalPendente)}</div></div>
    <div class="stat-card"><div class="stat-title">Cidades</div><div class="stat-value">${totalCidades}</div></div>
  `;
}

function montarResumoDoutores(_registros, saldos) {
  return saldos
    .map(item => {
      const creditoInicial = Number(item.credito_inicial || 0);
      const utilizado = Number(item.utilizado || 0);
      const creditoDisponivel = Number(item.credito_disponivel || 0);
      const percentual = obterPercentual(utilizado, creditoInicial);
      const status = obterStatus(percentual);

      return {
        doutor_id: item.doutor_id,
        doutor: item.doutor,
        creditoInicial,
        utilizado,
        creditoDisponivel,
        percentual,
        status
      };
    })
    .sort((a, b) => a.doutor.localeCompare(b.doutor, "pt-BR"));
}

function renderTabelaResumoDoutores(registros, saldos) {
  const tbody = document.getElementById("tabelaResumoDoutores");
  if (!tbody) return;

  const linhas = montarResumoDoutores(registros, saldos);

  if (!linhas.length) {
    tbody.innerHTML = `<tr><td colspan="6" class="empty-state">Sem doutores cadastrados para a competência</td></tr>`;
    return;
  }

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

function renderTabelaAtencao(registros, saldos) {
  const tbody = document.getElementById("tabelaAtencao");
  if (!tbody) return;

  const linhas = montarResumoDoutores(registros, saldos)
    .filter(item => item.percentual >= 50 && item.percentual < 100);

  if (!linhas.length) {
    tbody.innerHTML = `<tr><td colspan="6" class="empty-state">Sem doutores em atenção</td></tr>`;
    return;
  }

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

function renderTabelaBloqueados(registros, saldos) {
  const tbody = document.getElementById("tabelaBloqueados");
  if (!tbody) return;

  const linhas = montarResumoDoutores(registros, saldos)
    .filter(item => item.percentual >= 100);

  if (!linhas.length) {
    tbody.innerHTML = `<tr><td colspan="6" class="empty-state">Sem doutores bloqueados</td></tr>`;
    return;
  }

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

function renderTabelaPixMes(registros) {
  const tbody = document.getElementById("tabelaPixMes");
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
        <td class="${Number(item.pendente || 0) > 0 ? "text-warning" : "text-success"}">${formatarMoeda(item.pendente)}</td>
      </tr>
    `).join("");
}

function atualizarDashboard() {
  const competencia = getCompetenciaAtual();
  const registros = getRegistrosFiltrados();
  const saldos = getSaldosFiltrados();

  renderCards(registros);
  renderTabelaResumoDoutores(registros, saldos);
  renderTabelaAtencao(registros, saldos);
  renderTabelaBloqueados(registros, saldos);
  renderTabelaPixMes(registros);

  const badgeCompetencia = document.getElementById("badgeCompetencia");
  if (badgeCompetencia) badgeCompetencia.textContent = formatarCompetenciaLabel(competencia);
}

function exportarCSV() {
  const competencia = getCompetenciaAtual();
  const registros = getRegistrosFiltrados();

  if (!registros.length) {
    alert("Não há dados para exportar.");
    return;
  }

  const headers = [
    "competencia", "data", "cidade", "responsavel_fiscal",
    "doutor_final", "paciente", "valor", "valor_descontado", "pendente"
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
  link.download = `pix_doutores_${competencia}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

async function carregarDashboardInterno() {
  const resposta = await fetch("./data/dashboard_data.json", { cache: "no-store" });
  if (!resposta.ok) throw new Error(`Arquivo não encontrado: ${resposta.status}`);

  dashboardData = await resposta.json();

  document.getElementById("tituloDashboard").textContent = dashboardData.titulo_dashboard || "PIX Doutores";
  document.getElementById("subtituloDashboard").textContent = "Lista mensal de PIX Doutores com alertas de limite";
  document.getElementById("badgeArquivo").textContent = dashboardData?.arquivo_origem
    ? `Base: ${dashboardData.arquivo_origem}`
    : "Base não informada";

  preencherBadgeUsuario();
  preencherFiltroMes();
  preencherFiltroCidade();
  preencherFiltroDoutor();
  atualizarDashboard();
}

async function carregarDoutoresAdmin() {
  const tbody = document.getElementById("tabelaAdminDoutores");
  if (!tbody) return;

  tbody.innerHTML = `<tr><td colspan="10" class="empty-state">Carregando...</td></tr>`;
  const competencia = getCompetenciaAtual();

  try {
    const { data: doutores, error: errorDoutores } = await supabaseClient
      .from("doutores_config")
      .select("*")
      .order("nome", { ascending: true });

    if (errorDoutores) throw errorDoutores;

    const { data: saldos, error: errorSaldos } = await supabaseClient
      .from("doutores_saldos_mensais")
      .select("*")
      .eq("competencia", competencia);

    if (errorSaldos) throw errorSaldos;

    const saldoPorDoutor = {};
    for (const item of saldos || []) {
      saldoPorDoutor[item.doutor_id] = item;
    }

    if (!doutores || !doutores.length) {
      tbody.innerHTML = `<tr><td colspan="10" class="empty-state">Nenhum doutor cadastrado</td></tr>`;
      return;
    }

    tbody.innerHTML = doutores.map(item => {
      const saldo = saldoPorDoutor[item.id] || {};

      return `
        <tr>
          <td><input data-id="${item.id}" data-field="nome" type="text" value="${escapeHtml(item.nome)}" /></td>
          <td><input data-id="${item.id}" data-field="credito" type="number" step="0.01" value="${Number(item.credito || 0)}" /></td>
          <td>${formatarMoeda(saldo.credito_inicial ?? item.credito ?? 0)}</td>
          <td>${formatarMoeda(saldo.utilizado ?? 0)}</td>
          <td>${formatarMoeda(saldo.credito_final ?? item.credito ?? 0)}</td>
          <td><input data-id="${item.id}" data-field="pix_key" type="text" value="${escapeHtml(item.pix_key || "")}" /></td>
          <td>
            <select data-id="${item.id}" data-field="ativo">
              <option value="true" ${item.ativo ? "selected" : ""}>Ativo</option>
              <option value="false" ${!item.ativo ? "selected" : ""}>Inativo</option>
            </select>
          </td>
          <td><input data-id="${item.id}" data-field="observacao" type="text" value="${escapeHtml(saldo.observacao || "")}" /></td>
          <td>${escapeHtml(saldo.updated_by_email || item.updated_by_email || "")}</td>
          <td>
            <button class="btn btn-primary btn-small" onclick="salvarDoutor('${item.id}')">Salvar</button>
            <button class="btn btn-secondary btn-small" onclick="removerDoutor('${item.id}')">Excluir</button>
          </td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    console.error(err);
    tbody.innerHTML = `<tr><td colspan="10" class="empty-state">Erro ao carregar doutores</td></tr>`;
  }
}

async function salvarDoutor(id) {
  try {
    mostrarMensagemAdmin("");
    const competencia = getCompetenciaAtual();

    const nome = document.querySelector(`[data-id="${id}"][data-field="nome"]`)?.value.trim() || "";
    const credito = parseFloat(document.querySelector(`[data-id="${id}"][data-field="credito"]`)?.value || "0");
    const pixKey = document.querySelector(`[data-id="${id}"][data-field="pix_key"]`)?.value.trim() || "";
    const ativo = document.querySelector(`[data-id="${id}"][data-field="ativo"]`)?.value === "true";
    const observacao = document.querySelector(`[data-id="${id}"][data-field="observacao"]`)?.value.trim() || null;

    if (!nome) {
      mostrarMensagemAdmin("Nome é obrigatório.", true);
      return;
    }

    const { data: userData } = await supabaseClient.auth.getUser();
    const emailAtual = userData?.user?.email || null;

    const { error: errorDoutor } = await supabaseClient
      .from("doutores_config")
      .update({
        nome,
        nome_normalizado: normalizarNome(nome),
        credito,
        pix_key: pixKey || null,
        ativo,
        updated_by_email: emailAtual
      })
      .eq("id", id);

    if (errorDoutor) throw errorDoutor;

    const { data: saldoExistente, error: errorBuscaSaldo } = await supabaseClient
      .from("doutores_saldos_mensais")
      .select("*")
      .eq("competencia", competencia)
      .eq("doutor_id", id)
      .maybeSingle();

    if (errorBuscaSaldo) throw errorBuscaSaldo;

    if (saldoExistente) {
      const { error: errorSaldo } = await supabaseClient
        .from("doutores_saldos_mensais")
        .update({
          observacao,
          updated_by_email: emailAtual
        })
        .eq("id", saldoExistente.id);

      if (errorSaldo) throw errorSaldo;
    } else {
      const { error: errorInsertSaldo } = await supabaseClient
        .from("doutores_saldos_mensais")
        .insert({
          competencia,
          doutor_id: id,
          credito_inicial: credito,
          utilizado: 0,
          credito_final: credito,
          observacao,
          updated_by_email: emailAtual
        });

      if (errorInsertSaldo) throw errorInsertSaldo;
    }

    mostrarMensagemAdmin("Doutor salvo com sucesso.");
    await carregarDoutoresAdmin();
    await carregarDashboardInterno();
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

    const { data: userData } = await supabaseClient.auth.getUser();
    const emailAtual = userData?.user?.email || null;

    const { data: novoDoutor, error } = await supabaseClient
      .from("doutores_config")
      .insert({
        nome,
        nome_normalizado: normalizarNome(nome),
        credito,
        pix_key: pixKey || null,
        ativo,
        updated_by_email: emailAtual
      })
      .select()
      .single();

    if (error) throw error;

    const competencia = getCompetenciaAtual();

    const { error: errorSaldo } = await supabaseClient
      .from("doutores_saldos_mensais")
      .insert({
        competencia,
        doutor_id: novoDoutor.id,
        credito_inicial: credito,
        utilizado: 0,
        credito_final: credito,
        observacao: null,
        updated_by_email: emailAtual
      });

    if (errorSaldo) throw errorSaldo;

    document.getElementById("novoNome").value = "";
    document.getElementById("novoCredito").value = "";
    document.getElementById("novaPixKey").value = "";
    document.getElementById("novoAtivo").value = "true";

    mostrarMensagemAdmin
