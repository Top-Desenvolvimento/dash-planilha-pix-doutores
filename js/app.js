let dashboardData = null;
let currentUser = null;
let currentUserIsAdmin = false;

function byId(id) {
  return document.getElementById(id);
}

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
  const base = String(nome || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/\s+/g, " ")
    .trim();

  const aliases = {
    "cir.dionathan paim pohlmann": "dionathan pohlmann",
    "cir dionathan paim pohlmann": "dionathan pohlmann",
    "dionathan paim pohlmann": "dionathan pohlmann",
    "cir.dionathan pohlmann": "dionathan pohlmann",
    "cir dionathan pohlmann": "dionathan pohlmann",
    "dionathan pohlmann": "dionathan pohlmann"
  };

  return aliases[base] || base;
}

function obterNomeResponsavelAtual(user) {
  const meta = user?.user_metadata || {};
  const nome =
    meta.nome ||
    meta.name ||
    meta.full_name ||
    meta.display_name ||
    "";

  if (String(nome).trim()) {
    return String(nome).trim();
  }

  const email = user?.email || "";
  if (email.includes("@")) {
    return email.split("@")[0];
  }

  return "Não informado";
}

function calcularSaldoMensalAdmin(creditoInicial, utilizado, saldoDigitado = null) {
  const credito = Number(creditoInicial || 0);
  const uso = Number(utilizado || 0);

  if (saldoDigitado !== null && saldoDigitado !== undefined && saldoDigitado !== "") {
    return Number(saldoDigitado || 0);
  }

  return Number((credito - uso).toFixed(2));
}

function mostrarMensagemAuth(texto, erro = false) {
  const el = byId("authMessage");
  if (!el) return;
  el.textContent = texto || "";
  el.className = erro ? "auth-message error" : "auth-message";
}

function mostrarMensagemAdmin(texto, erro = false) {
  const el = byId("adminMessage");
  if (!el) return;
  el.textContent = texto || "";
  el.className = erro ? "auth-message error" : "auth-message";
}

function mostrarTelaLogin() {
  byId("authScreen")?.classList.remove("hidden");
  byId("appRoot")?.classList.add("hidden");
}

function mostrarApp() {
  byId("authScreen")?.classList.add("hidden");
  byId("appRoot")?.classList.remove("hidden");
}

function mostrarDashboard() {
  byId("dashboardView")?.classList.remove("hidden");
  byId("adminView")?.classList.add("hidden");
  byId("filtrosSidebar")?.classList.remove("hidden");
}

function mostrarAdmin() {
  byId("dashboardView")?.classList.add("hidden");
  byId("adminView")?.classList.remove("hidden");
  byId("filtrosSidebar")?.classList.add("hidden");
}

function getBaseAppUrl() {
  const { origin, pathname } = window.location;

  if (pathname.endsWith("/reset.html")) {
    return `${origin}${pathname.replace(/reset\.html$/, "")}`;
  }

  if (pathname.endsWith("/index.html")) {
    return `${origin}${pathname.replace(/index\.html$/, "")}`;
  }

  return `${origin}${pathname.endsWith("/") ? pathname : `${pathname}/`}`;
}

function validarSupabasePronto() {
  if (!window.supabaseClient) {
    throw new Error("Supabase não configurado. Verifique js/supabase-config.js.");
  }
  return window.supabaseClient;
}

async function validarUsuarioAutorizado() {
  const client = validarSupabasePronto();
  const { data, error } = await client.rpc("usuario_esta_autorizado");
  if (error) throw error;
  return data === true;
}

async function validarUsuarioAdmin() {
  const client = validarSupabasePronto();
  const { data, error } = await client.rpc("usuario_eh_admin");
  if (error) throw error;
  return data === true;
}

async function emailPodeCadastrar(email) {
  const client = validarSupabasePronto();
  const { data, error } = await client.rpc("email_pode_cadastrar", {
    p_email: email
  });
  if (error) throw error;
  return data === true;
}

async function loginSupabase(email, password) {
  const client = validarSupabasePronto();

  const { error } = await client.auth.signInWithPassword({
    email,
    password
  });

  if (error) throw error;

  const autorizado = await validarUsuarioAutorizado();

  if (!autorizado) {
    await client.auth.signOut();
    throw new Error("Seu usuário não está autorizado para acessar esta dashboard.");
  }
}

async function criarAcessoSupabase(email, password) {
  const permitido = await emailPodeCadastrar(email);

  if (!permitido) {
    throw new Error("Este e-mail não está autorizado para criar acesso.");
  }

  const client = validarSupabasePronto();
  const redirectTo = getBaseAppUrl();

  const { error } = await client.auth.signUp({
    email,
    password,
    options: {
      emailRedirectTo: redirectTo
    }
  });

  if (error) throw error;
}

async function logoutSupabase() {
  const client = validarSupabasePronto();
  await client.auth.signOut();
}

async function enviarRecuperacaoSenha(email) {
  const client = validarSupabasePronto();
  const redirectTo = `${getBaseAppUrl()}reset.html`;

  const { error } = await client.auth.resetPasswordForEmail(email, {
    redirectTo
  });

  if (error) throw error;
}

function preencherBadgeUsuario() {
  const badge = byId("badgeUsuario");
  if (badge) {
    badge.textContent = currentUser?.email || "Usuário";
  }
}

function getCompetenciaAtual() {
  return byId("filtroMes")?.value || dashboardData?.competencia_padrao || "2026-01";
}

function getCidadeAtual() {
  return byId("filtroCidade")?.value || "";
}

function getDoutorAtual() {
  return byId("filtroDoutor")?.value || "";
}

function getRegistrosCompetencia(competencia) {
  if (dashboardData?.registros_por_competencia?.[competencia]) {
    return [...dashboardData.registros_por_competencia[competencia]];
  }

  const registros = Array.isArray(dashboardData?.registros) ? dashboardData.registros : [];
  return registros.filter(item => String(item.competencia || "") === competencia);
}

function obterDoutoresFallbackDoDashboard() {
  const mapa = new Map();
  const meses = dashboardData?.meses_disponiveis || [];

  for (const competencia of meses) {
    const saldos = dashboardData?.saldos_por_competencia?.[competencia] || [];
    for (const item of saldos) {
      const id = item.doutor_id || normalizarNome(item.doutor || "");
      if (!id) continue;

      if (!mapa.has(id)) {
        mapa.set(id, {
          id,
          nome: item.doutor || "",
          credito: Number(item.credito_inicial || 0),
          pix_key: item.pix_key || "",
          ativo: true,
          updated_by_email: item.updated_by_email || null,
          updated_by_nome: item.updated_by_nome || null
        });
      }
    }
  }

  return Array.from(mapa.values()).sort((a, b) =>
    String(a.nome || "").localeCompare(String(b.nome || ""), "pt-BR")
  );
}

function getSaldosCompetencia(competencia) {
  const saldos = dashboardData?.saldos_por_competencia?.[competencia];
  return Array.isArray(saldos) ? [...saldos] : [];
}

async function sincronizarSaldosAdminNoDashboard() {
  if (!dashboardData) return;
  if (!currentUserIsAdmin) return;

  try {
    const client = validarSupabasePronto();

    const { data: doutores, error: errorDoutores } = await client
      .from("doutores_config")
      .select("id, nome, credito, pix_key, ativo, updated_by_email, updated_by_nome")
      .order("nome", { ascending: true });

    if (errorDoutores) {
      console.warn("Não foi possível carregar doutores da ADM. Mantendo dashboard original.", errorDoutores);
      return;
    }

    // MUITO IMPORTANTE:
    // se não houver doutores cadastrados no Supabase, não apaga os créditos da dashboard
    if (!Array.isArray(doutores) || doutores.length === 0) {
      console.warn("ADM sem doutores cadastrados no Supabase. Mantendo dados originais da dashboard.");
      return;
    }

    const meses = dashboardData?.meses_disponiveis || [];
    if (!meses.length) return;

    const { data: saldos, error: errorSaldos } = await client
      .from("doutores_saldos_mensais")
      .select("*")
      .in("competencia", meses);

    if (errorSaldos) {
      console.warn("Não foi possível carregar saldos da ADM. Mantendo dashboard original.", errorSaldos);
      return;
    }

    const saldoPorMesEDoutor = {};
    for (const item of saldos || []) {
      if (!saldoPorMesEDoutor[item.competencia]) {
        saldoPorMesEDoutor[item.competencia] = {};
      }
      saldoPorMesEDoutor[item.competencia][item.doutor_id] = item;
    }

    for (const competencia of meses) {
      const saldosOriginais = Array.isArray(dashboardData?.saldos_por_competencia?.[competencia])
        ? dashboardData.saldos_por_competencia[competencia]
        : [];

      const originalPorNome = {};
      for (const item of saldosOriginais) {
        originalPorNome[normalizarNome(item.doutor || "")] = item;
      }

      const baseMes = [];

      for (const doutor of doutores) {
        if (doutor.ativo === false) continue;

        const saldo = saldoPorMesEDoutor[competencia]?.[doutor.id] || null;
        const original = originalPorNome[normalizarNome(doutor.nome || "")] || null;

        const creditoBase = Number(doutor.credito ?? original?.credito_inicial ?? 0);
        const creditoInicial = Number(saldo?.credito_inicial ?? original?.credito_inicial ?? creditoBase);
        const utilizado = Number(saldo?.utilizado ?? original?.utilizado ?? 0);
        const creditoFinal = Number(
          saldo?.credito_final ??
          original?.credito_disponivel ??
          Math.max(0, creditoInicial - utilizado)
        );

        baseMes.push({
          doutor_id: doutor.id,
          doutor: doutor.nome,
          credito_inicial: creditoInicial,
          utilizado,
          credito_disponivel: creditoFinal,
          credito_final: creditoFinal,
          pix_key: doutor.pix_key || original?.pix_key || "",
          updated_by_email: saldo?.updated_by_email || doutor.updated_by_email || null,
          updated_by_nome: saldo?.updated_by_nome || doutor.updated_by_nome || null
        });
      }

      // só substitui se realmente montou alguma coisa
      if (baseMes.length > 0) {
        dashboardData.saldos_por_competencia[competencia] = baseMes.sort((a, b) =>
          String(a.doutor || "").localeCompare(String(b.doutor || ""), "pt-BR")
        );
      }
    }
  } catch (err) {
    console.error("Erro ao sincronizar saldos da ADM no dashboard:", err);
  }
}
function preencherFiltroMes() {
  const filtroMes = byId("filtroMes");
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
  const filtroCidade = byId("filtroCidade");
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
  const filtroDoutor = byId("filtroDoutor");
  if (!filtroDoutor) return;

  const doutorSelecionado = filtroDoutor.value;
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

  if (doutores.includes(doutorSelecionado)) {
    filtroDoutor.value = doutorSelecionado;
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

function montarResumoDoutores(saldos) {
  return saldos
    .map(item => {
      const creditoInicial = Number(item.credito_inicial || 0);
      const utilizado = Number(item.utilizado || 0);
      const creditoDisponivel = Number(item.credito_disponivel ?? item.credito_final ?? 0);
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

function renderCards(registros) {
  const alvo = byId("cardsResumo");
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

function renderTabelaResumoDoutores(saldos) {
  const tbody = byId("tabelaResumoDoutores");
  if (!tbody) return;

  const linhas = montarResumoDoutores(saldos);

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

function renderTabelaAtencao(saldos) {
  const tbody = byId("tabelaAtencao");
  if (!tbody) return;

  const linhas = montarResumoDoutores(saldos).filter(item => item.percentual >= 50 && item.percentual < 100);

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

function renderTabelaBloqueados(saldos) {
  const tbody = byId("tabelaBloqueados");
  if (!tbody) return;

  const linhas = montarResumoDoutores(saldos).filter(item => item.percentual >= 100);

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
  const tbody = byId("tabelaPixMes");
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
  renderTabelaResumoDoutores(saldos);
  renderTabelaAtencao(saldos);
  renderTabelaBloqueados(saldos);
  renderTabelaPixMes(registros);

  const badgeCompetencia = byId("badgeCompetencia");
  if (badgeCompetencia) {
    badgeCompetencia.textContent = formatarCompetenciaLabel(competencia);
  }
}

function exportarCSV() {
  const competencia = getCompetenciaAtual();
  const registros = getRegistrosFiltrados();

  if (!registros.length) {
    alert("Não há dados para exportar.");
    return;
  }

  const headers = [
    "competencia",
    "data",
    "cidade",
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
  link.download = `pix_doutores_${competencia}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

async function carregarDashboardInterno() {
  const resposta = await fetch("./data/dashboard_data.json", { cache: "no-store" });

  if (!resposta.ok) {
    throw new Error(`Arquivo não encontrado: ${resposta.status}`);
  }

  dashboardData = await resposta.json();

  if (!dashboardData || typeof dashboardData !== "object") {
    throw new Error("dashboard_data.json inválido.");
  }

  if (byId("tituloDashboard")) {
    byId("tituloDashboard").textContent = dashboardData.titulo_dashboard || "PIX Doutores";
  }

  if (byId("subtituloDashboard")) {
    byId("subtituloDashboard").textContent = "Lista mensal de PIX Doutores com alertas de limite";
  }

  if (byId("badgeArquivo")) {
    byId("badgeArquivo").textContent = dashboardData?.arquivo_origem
      ? `Base: ${dashboardData.arquivo_origem}`
      : "Base não informada";
  }

  preencherBadgeUsuario();
  preencherFiltroMes();
  preencherFiltroCidade();
  preencherFiltroDoutor();

  await sincronizarSaldosAdminNoDashboard();
  atualizarDashboard();
}

async function carregarDoutoresAdmin() {
  const tbody = byId("tabelaAdminDoutores");
  if (!tbody) return;

  tbody.innerHTML = `<tr><td colspan="10" class="empty-state">Carregando...</td></tr>`;

  const competencia = getCompetenciaAtual();
  const client = validarSupabasePronto();

  try {
    const { data: doutores, error: errorDoutores } = await client
      .from("doutores_config")
      .select("*")
      .order("nome", { ascending: true });

    if (errorDoutores) throw errorDoutores;

    const { data: saldos, error: errorSaldos } = await client
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

      const creditoBase = Number(item.credito || 0);
      const creditoInicial = Number(saldo.credito_inicial ?? creditoBase);
      const utilizado = Number(saldo.utilizado ?? 0);
      const saldoFinal = Number(saldo.credito_final ?? creditoInicial);
      const responsavelUltimo =
        saldo.updated_by_nome ||
        saldo.updated_by_email ||
        item.updated_by_nome ||
        item.updated_by_email ||
        "";

      return `
        <tr>
          <td><input data-id="${item.id}" data-field="nome" type="text" value="${escapeHtml(item.nome)}" /></td>
          <td><input data-id="${item.id}" data-field="credito" type="number" step="0.01" value="${creditoBase}" /></td>
          <td><input data-id="${item.id}" data-field="credito_inicial" type="number" step="0.01" value="${creditoInicial}" /></td>
          <td><input data-id="${item.id}" data-field="utilizado" type="number" step="0.01" value="${utilizado}" /></td>
          <td><input data-id="${item.id}" data-field="credito_final" type="number" step="0.01" value="${saldoFinal}" /></td>
          <td><input data-id="${item.id}" data-field="pix_key" type="text" value="${escapeHtml(item.pix_key || "")}" /></td>
          <td>
            <select data-id="${item.id}" data-field="ativo">
              <option value="true" ${item.ativo ? "selected" : ""}>Ativo</option>
              <option value="false" ${!item.ativo ? "selected" : ""}>Inativo</option>
            </select>
          </td>
          <td><input data-id="${item.id}" data-field="observacao" type="text" value="${escapeHtml(saldo.observacao || "")}" /></td>
          <td>${escapeHtml(responsavelUltimo)}</td>
          <td>
            <button class="btn btn-primary btn-small" onclick="salvarDoutor('${item.id}')">Salvar</button>
            <button class="btn btn-secondary btn-small" onclick="removerDoutor('${item.id}')">Excluir</button>
          </td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    console.error("Erro ao carregar doutores:", err);
    tbody.innerHTML = `<tr><td colspan="10" class="empty-state">Erro ao carregar doutores</td></tr>`;
  }
}

async function salvarDoutor(id) {
  try {
    mostrarMensagemAdmin("");
    const competencia = getCompetenciaAtual();
    const client = validarSupabasePronto();

    const nome = document.querySelector(`[data-id="${id}"][data-field="nome"]`)?.value.trim() || "";
    const credito = parseFloat(document.querySelector(`[data-id="${id}"][data-field="credito"]`)?.value || "0");
    const creditoInicial = parseFloat(document.querySelector(`[data-id="${id}"][data-field="credito_inicial"]`)?.value || "0");
    const utilizado = parseFloat(document.querySelector(`[data-id="${id}"][data-field="utilizado"]`)?.value || "0");
    const creditoFinalDigitado = document.querySelector(`[data-id="${id}"][data-field="credito_final"]`)?.value ?? "";
    const creditoFinal = calcularSaldoMensalAdmin(creditoInicial, utilizado, creditoFinalDigitado);
    const pixKey = document.querySelector(`[data-id="${id}"][data-field="pix_key"]`)?.value.trim() || "";
    const ativo = document.querySelector(`[data-id="${id}"][data-field="ativo"]`)?.value === "true";
    const observacao = document.querySelector(`[data-id="${id}"][data-field="observacao"]`)?.value.trim() || null;

    if (!nome) {
      mostrarMensagemAdmin("Nome é obrigatório.", true);
      return;
    }

    const { data: userData } = await client.auth.getUser();
    const userAtual = userData?.user || null;
    const emailAtual = userAtual?.email || null;
    const nomeResponsavel = obterNomeResponsavelAtual(userAtual);

    const { error: errorDoutor } = await client
      .from("doutores_config")
      .update({
        nome,
        nome_normalizado: normalizarNome(nome),
        credito,
        pix_key: pixKey || null,
        ativo,
        updated_by_email: emailAtual,
        updated_by_nome: nomeResponsavel
      })
      .eq("id", id);

    if (errorDoutor) throw errorDoutor;

    const ajusteManual = Number((creditoFinal - (creditoInicial - utilizado)).toFixed(2));

    const { data: saldoExistente, error: errorBuscaSaldo } = await client
      .from("doutores_saldos_mensais")
      .select("*")
      .eq("competencia", competencia)
      .eq("doutor_id", id)
      .maybeSingle();

    if (errorBuscaSaldo) throw errorBuscaSaldo;

    if (saldoExistente) {
      const { error: errorSaldo } = await client
        .from("doutores_saldos_mensais")
        .update({
          credito_inicial: creditoInicial,
          utilizado,
          credito_final: creditoFinal,
          ajuste_manual: ajusteManual,
          observacao,
          updated_by_email: emailAtual,
          updated_by_nome: nomeResponsavel
        })
        .eq("id", saldoExistente.id);

      if (errorSaldo) throw errorSaldo;
    } else {
      const { error: errorInsertSaldo } = await client
        .from("doutores_saldos_mensais")
        .insert({
          competencia,
          doutor_id: id,
          credito_inicial: creditoInicial,
          utilizado,
          credito_final: creditoFinal,
          ajuste_manual: ajusteManual,
          observacao,
          updated_by_email: emailAtual,
          updated_by_nome: nomeResponsavel
        });

      if (errorInsertSaldo) throw errorInsertSaldo;
    }

    await sincronizarSaldosAdminNoDashboard();
    atualizarDashboard();
    await carregarDoutoresAdmin();
    mostrarMensagemAdmin("Doutor salvo com sucesso.");
  } catch (err) {
    console.error("Erro detalhado ao salvar doutor:", err);
    mostrarMensagemAdmin(`Erro ao salvar doutor: ${err.message || "falha no banco de dados"}`, true);
  }
}

async function removerDoutor(id) {
  if (!confirm("Tem certeza que deseja excluir este doutor?")) return;

  try {
    mostrarMensagemAdmin("");
    const client = validarSupabasePronto();

    const { error: errorSaldo } = await client
      .from("doutores_saldos_mensais")
      .delete()
      .eq("doutor_id", id);

    if (errorSaldo) throw errorSaldo;

    const { error: errorDoutor } = await client
      .from("doutores_config")
      .delete()
      .eq("id", id);

    if (errorDoutor) throw errorDoutor;

    await sincronizarSaldosAdminNoDashboard();
    atualizarDashboard();
    await carregarDoutoresAdmin();
    mostrarMensagemAdmin("Doutor removido com sucesso.");
  } catch (err) {
    console.error("Erro detalhado ao remover doutor:", err);
    mostrarMensagemAdmin(`Erro ao remover doutor: ${err.message || "falha no banco de dados"}`, true);
  }
}

async function adicionarDoutor() {
  try {
    mostrarMensagemAdmin("");
    const client = validarSupabasePronto();

    const nome = byId("novoNome")?.value.trim() || "";
    const credito = parseFloat(byId("novoCredito")?.value || "0");
    const pixKey = byId("novaPixKey")?.value.trim() || "";
    const ativo = byId("novoAtivo")?.value === "true";
    const competencia = getCompetenciaAtual();

    if (!nome) {
      mostrarMensagemAdmin("Informe o nome do doutor.", true);
      return;
    }

    if (Number.isNaN(credito) || credito < 0) {
      mostrarMensagemAdmin("Informe um crédito válido.", true);
      return;
    }

    const { data: userData, error: errorUser } = await client.auth.getUser();
    if (errorUser) throw errorUser;

    const userAtual = userData?.user || null;
    const emailAtual = userAtual?.email || null;
    const nomeResponsavel = obterNomeResponsavelAtual(userAtual);

    const payloadDoutor = {
      nome,
      nome_normalizado: normalizarNome(nome),
      credito,
      pix_key: pixKey || null,
      ativo,
      updated_by_email: emailAtual,
      updated_by_nome: nomeResponsavel
    };

    const insertDoutor = await client
      .from("doutores_config")
      .insert(payloadDoutor)
      .select()
      .single();

    if (insertDoutor.error) {
      throw insertDoutor.error;
    }

    const novoDoutor = insertDoutor.data;

    const payloadSaldo = {
      competencia,
      doutor_id: novoDoutor.id,
      credito_inicial: credito,
      utilizado: 0,
      credito_final: credito,
      ajuste_manual: 0,
      observacao: null,
      updated_by_email: emailAtual,
      updated_by_nome: nomeResponsavel
    };

    const insertSaldo = await client
      .from("doutores_saldos_mensais")
      .insert(payloadSaldo);

    if (insertSaldo.error) {
      await client.from("doutores_config").delete().eq("id", novoDoutor.id);
      throw insertSaldo.error;
    }

    if (byId("novoNome")) byId("novoNome").value = "";
    if (byId("novoCredito")) byId("novoCredito").value = "";
    if (byId("novaPixKey")) byId("novaPixKey").value = "";
    if (byId("novoAtivo")) byId("novoAtivo").value = "true";

    await sincronizarSaldosAdminNoDashboard();
    atualizarDashboard();
    await carregarDoutoresAdmin();
    mostrarMensagemAdmin("Doutor adicionado com sucesso.");
  } catch (err) {
    console.error("Erro detalhado ao adicionar doutor:", err);

    const mensagem = [
      err?.message || "Erro desconhecido",
      err?.details ? `Detalhes: ${err.details}` : "",
      err?.hint ? `Dica: ${err.hint}` : "",
      err?.code ? `Código: ${err.code}` : ""
    ].filter(Boolean).join(" | ");

    mostrarMensagemAdmin(mensagem, true);
  }
}

async function iniciarAplicacao() {
  try {
    if (!window.supabaseClient) {
      mostrarTelaLogin();
      mostrarMensagemAuth("Supabase não configurado. Verifique js/supabase-config.js.", true);
      return;
    }

    const client = validarSupabasePronto();
    const { data, error } = await client.auth.getSession();

    if (error) throw error;

    const session = data?.session || null;

    if (!session) {
      mostrarTelaLogin();
      return;
    }

    const autorizado = await validarUsuarioAutorizado();

    if (!autorizado) {
      await client.auth.signOut();
      mostrarTelaLogin();
      mostrarMensagemAuth("Usuário sem permissão de acesso.", true);
      return;
    }

    currentUser = session.user;
    currentUserIsAdmin = await validarUsuarioAdmin();

    if (currentUserIsAdmin) {
      byId("btnTabAdmin")?.classList.remove("hidden");
    } else {
      byId("btnTabAdmin")?.classList.add("hidden");
    }

    mostrarApp();
    mostrarDashboard();
    preencherBadgeUsuario();

    try {
      await carregarDashboardInterno();
    } catch (errDashboard) {
      console.error("Erro ao carregar dashboard:", errDashboard);

      const titulo = byId("tituloDashboard");
      const subtitulo = byId("subtituloDashboard");
      const cards = byId("cardsResumo");
      const tabelaResumo = byId("tabelaResumoDoutores");
      const tabelaAtencao = byId("tabelaAtencao");
      const tabelaBloqueados = byId("tabelaBloqueados");
      const tabelaPixMes = byId("tabelaPixMes");

      if (titulo) titulo.textContent = "PIX Doutores";
      if (subtitulo) subtitulo.textContent = "Erro ao carregar os dados da dashboard.";

      if (cards) {
        cards.innerHTML = `
          <div class="stat-card">
            <div class="stat-title">Status</div>
            <div class="stat-value">Falha ao carregar data/dashboard_data.json</div>
          </div>
        `;
      }

      if (tabelaResumo) tabelaResumo.innerHTML = `<tr><td colspan="6" class="empty-state">Erro ao carregar dados</td></tr>`;
      if (tabelaAtencao) tabelaAtencao.innerHTML = `<tr><td colspan="6" class="empty-state">Erro ao carregar dados</td></tr>`;
      if (tabelaBloqueados) tabelaBloqueados.innerHTML = `<tr><td colspan="6" class="empty-state">Erro ao carregar dados</td></tr>`;
      if (tabelaPixMes) tabelaPixMes.innerHTML = `<tr><td colspan="7" class="empty-state">Erro ao carregar dados</td></tr>`;
    }
  } catch (erro) {
    console.error("Erro ao iniciar app:", erro);
    mostrarTelaLogin();
    mostrarMensagemAuth(erro.message || "Erro ao validar acesso.", true);
  }
}

byId("loginForm")?.addEventListener("submit", async (event) => {
  event.preventDefault();

  const email = byId("email")?.value.trim() || "";
  const password = byId("password")?.value.trim() || "";

  mostrarMensagemAuth("");

  if (!email || !password) {
    mostrarMensagemAuth("Preencha e-mail e senha.", true);
    return;
  }

  try {
    await loginSupabase(email, password);

    const client = validarSupabasePronto();
    const { data } = await client.auth.getUser();
    currentUser = data?.user || null;
    currentUserIsAdmin = await validarUsuarioAdmin();

    if (currentUserIsAdmin) {
      byId("btnTabAdmin")?.classList.remove("hidden");
    } else {
      byId("btnTabAdmin")?.classList.add("hidden");
    }

    mostrarApp();
    mostrarDashboard();
    preencherBadgeUsuario();

    try {
      await carregarDashboardInterno();
    } catch (errDashboard) {
      console.error("Erro ao carregar dashboard após login:", errDashboard);
      mostrarApp();
      mostrarDashboard();
      mostrarMensagemAuth("");
    }
  } catch (erro) {
    console.error(erro);
    mostrarMensagemAuth(erro.message || "Não foi possível entrar.", true);
  }
});

byId("btnCriarAcesso")?.addEventListener("click", async () => {
  const email = byId("email")?.value.trim() || "";
  const password = byId("password")?.value.trim() || "";

  mostrarMensagemAuth("");

  if (!email || !password) {
    mostrarMensagemAuth("Preencha e-mail e senha para criar o acesso.", true);
    return;
  }

  try {
    await criarAcessoSupabase(email, password);
    mostrarMensagemAuth("Acesso criado com sucesso. Confira seu e-mail.");
  } catch (erro) {
    console.error(erro);
    mostrarMensagemAuth(erro.message || "Não foi possível criar o acesso.", true);
  }
});

byId("btnForgotPassword")?.addEventListener("click", async () => {
  const email = byId("email")?.value.trim() || "";

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

byId("btnLogout")?.addEventListener("click", async () => {
  try {
    await logoutSupabase();
  } catch (err) {
    console.error(err);
  }

  currentUser = null;
  currentUserIsAdmin = false;
  dashboardData = null;
  mostrarTelaLogin();
});

byId("btnTabDashboard")?.addEventListener("click", () => {
  mostrarDashboard();
});

byId("btnTabAdmin")?.addEventListener("click", async () => {
  if (!currentUserIsAdmin) return;
  mostrarAdmin();
  await carregarDoutoresAdmin();
});

byId("btnAdicionarDoutor")?.addEventListener("click", adicionarDoutor);

byId("filtroMes")?.addEventListener("change", async () => {
  preencherFiltroCidade();
  preencherFiltroDoutor();
  await sincronizarSaldosAdminNoDashboard();
  atualizarDashboard();

  if (!byId("adminView")?.classList.contains("hidden")) {
    await carregarDoutoresAdmin();
  }
});

byId("filtroCidade")?.addEventListener("change", atualizarDashboard);
byId("filtroDoutor")?.addEventListener("change", atualizarDashboard);

byId("btnLimpar")?.addEventListener("click", async () => {
  const filtroMes = byId("filtroMes");
  const filtroCidade = byId("filtroCidade");
  const filtroDoutor = byId("filtroDoutor");

  if (filtroMes) {
    filtroMes.value = dashboardData?.competencia_padrao || "2026-01";
  }

  preencherFiltroCidade();
  preencherFiltroDoutor();

  if (filtroCidade) filtroCidade.selectedIndex = 0;
  if (filtroDoutor) filtroDoutor.selectedIndex = 0;

  await sincronizarSaldosAdminNoDashboard();
  atualizarDashboard();
});

byId("btnExportar")?.addEventListener("click", exportarCSV);

window.salvarDoutor = salvarDoutor;
window.removerDoutor = removerDoutor;

if (window.supabaseClient) {
  window.supabaseClient.auth.onAuthStateChange(async (_event, session) => {
    if (!session) {
      currentUser = null;
      currentUserIsAdmin = false;
      mostrarTelaLogin();
      return;
    }

    currentUser = session.user;
  });
}

iniciarAplicacao();
