let dashboardData = null;
let currentUser = null;
let currentUserIsAdmin = false;

let cidadesAtuaisCache = {};
let cidadesAtuaisCompetencia = "";

function byId(id) {
  return document.getElementById(id);
}

function toNumber(valor, fallback = 0) {
  const n = Number(valor);
  return Number.isFinite(n) ? n : fallback;
}

function formatarMoeda(valor) {
  return toNumber(valor, 0).toLocaleString("pt-BR", {
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
    .replace(/[^\w\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();

  const aliases = {
    "cir dionathan paim pohlmann": "dionathan pohlmann",
    "cir dionathan pohlmann": "dionathan pohlmann",
    "dionathan paim pohlmann": "dionathan pohlmann",
    "dionathan pohlmann": "dionathan pohlmann",

    "dra andriele da silva": "adriele da silva",
    "dra adriele da silva": "adriele da silva",
    "andriele da silva": "adriele da silva",
    "adriele da silva": "adriele da silva"
  };

  return aliases[base] || base;
}

function obterNomeResponsavelAtual(user) {
  const meta = user?.user_metadata || {};
  const nome = meta.nome || meta.name || meta.full_name || meta.display_name || "";

  if (String(nome).trim()) return String(nome).trim();

  const email = user?.email || "";
  if (email.includes("@")) return email.split("@")[0];

  return "Não informado";
}

function isUuid(valor) {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
    String(valor || "").trim()
  );
}

function calcularCreditoInicialDoMes(creditoBase, saldoSupabase = null, saldoOriginal = null) {
  const base = toNumber(creditoBase, 0);

  if (saldoSupabase) {
    const creditoInicialSalvo = saldoSupabase.credito_inicial;

    if (creditoInicialSalvo !== null && creditoInicialSalvo !== undefined && String(creditoInicialSalvo) !== "") {
      const valorSalvo = toNumber(creditoInicialSalvo, 0);

      if (valorSalvo < 0 && base > 0) {
        return Number((base + valorSalvo).toFixed(2));
      }

      return Number(valorSalvo.toFixed(2));
    }

    const ajusteManual = toNumber(saldoSupabase.ajuste_manual, 0);
    if (ajusteManual !== 0) {
      return Number((base + ajusteManual).toFixed(2));
    }
  }

  if (saldoOriginal && saldoOriginal.credito_inicial !== undefined && saldoOriginal.credito_inicial !== null) {
    return Number(toNumber(saldoOriginal.credito_inicial, base).toFixed(2));
  }

  return Number(base.toFixed(2));
}

function calcularSaldoFinalDoMes(creditoInicial, utilizado) {
  return Number((toNumber(creditoInicial, 0) - toNumber(utilizado, 0)).toFixed(2));
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

  if (dashboardData) atualizarDashboard();
}

function mostrarAdmin() {
  if (!currentUserIsAdmin) return;

  byId("dashboardView")?.classList.add("hidden");
  byId("adminView")?.classList.remove("hidden");
  byId("filtrosSidebar")?.classList.add("hidden");

  if (dashboardData) {
    garantirFiltroMesAdmin();
    const adminMes = byId("filtroMesAdmin");
    if (adminMes) adminMes.value = getCompetenciaAtual();
  }
}

function getBaseAppUrl() {
  const { origin, pathname } = window.location;

  if (pathname.endsWith("/reset.html")) return `${origin}${pathname.replace(/reset\.html$/, "")}`;
  if (pathname.endsWith("/index.html")) return `${origin}${pathname.replace(/index\.html$/, "")}`;

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
  const { data, error } = await client.rpc("email_pode_cadastrar", { p_email: email });
  if (error) throw error;
  return data === true;
}

async function loginSupabase(email, password) {
  const client = validarSupabasePronto();

  const { error } = await client.auth.signInWithPassword({ email, password });
  if (error) throw error;

  const autorizado = await validarUsuarioAutorizado();

  if (!autorizado) {
    await client.auth.signOut();
    throw new Error("Seu usuário não está autorizado para acessar esta dashboard.");
  }
}

async function criarAcessoSupabase(email, password) {
  const permitido = await emailPodeCadastrar(email);

  if (!permitido) throw new Error("Este e-mail não está autorizado para criar acesso.");

  const client = validarSupabasePronto();
  const redirectTo = getBaseAppUrl();

  const { error } = await client.auth.signUp({
    email,
    password,
    options: { emailRedirectTo: redirectTo }
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

  const { error } = await client.auth.resetPasswordForEmail(email, { redirectTo });
  if (error) throw error;
}

function preencherBadgeUsuario() {
  const badge = byId("badgeUsuario");
  if (badge) badge.textContent = currentUser?.email || "Usuário";
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

function getSaldosCompetencia(competencia) {
  const saldos = dashboardData?.saldos_por_competencia?.[competencia];
  return Array.isArray(saldos) ? [...saldos] : [];
}

function obterDoutoresFallbackDoDashboard() {
  const mapa = new Map();
  const meses = dashboardData?.meses_disponiveis || [];

  for (const competencia of meses) {
    const saldos = dashboardData?.saldos_por_competencia?.[competencia] || [];

    for (const item of saldos) {
      const chave = normalizarNome(item.doutor || "");
      if (!chave) continue;

      if (!mapa.has(chave)) {
        mapa.set(chave, {
          id: item.doutor_id || chave,
          nome: item.doutor || "",
          nome_normalizado: chave,
          credito: toNumber(item.credito_inicial, 0),
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

function obterSaldosFallbackDaCompetencia(competencia) {
  const saldos = dashboardData?.saldos_por_competencia?.[competencia] || [];
  const mapa = {};

  for (const item of saldos) {
    const chave = normalizarNome(item.doutor || "");
    if (!chave) continue;
    mapa[chave] = item;
  }

  return mapa;
}

function somarUtilizadoPorNomeNosRegistros(competencia) {
  const registros = getRegistrosCompetencia(competencia);
  const mapa = {};

  for (const item of registros) {
    const nome = normalizarNome(
      item.doutor_final ||
      item.doutor ||
      item.nome_doutor ||
      item.responsavel_fiscal ||
      item.responsavel_fiscal_lido ||
      ""
    );

    if (!nome) continue;

    const valor = toNumber(item.valor, 0);
    mapa[nome] = Number(((mapa[nome] || 0) + valor).toFixed(2));
  }

  return mapa;
}

async function garantirDoutorNoSupabase(idOriginal, payloadBase) {
  const client = validarSupabasePronto();

  if (isUuid(idOriginal)) return idOriginal;

  const { data: existente, error: errorBusca } = await client
    .from("doutores_config")
    .select("id, nome, nome_normalizado")
    .eq("nome_normalizado", payloadBase.nome_normalizado)
    .maybeSingle();

  if (errorBusca) throw errorBusca;
  if (existente?.id) return existente.id;

  const { data: novo, error: errorInsert } = await client
    .from("doutores_config")
    .insert(payloadBase)
    .select("id")
    .single();

  if (errorInsert) throw errorInsert;
  return novo.id;
}

async function sincronizarSaldosAdminNoDashboard() {
  if (!dashboardData) return;

  try {
    const client = validarSupabasePronto();

    const { data: doutoresSupabase, error: errorDoutores } = await client
      .from("doutores_config")
      .select("id, nome, nome_normalizado, credito, pix_key, ativo, updated_by_email, updated_by_nome")
      .order("nome", { ascending: true });

    if (errorDoutores) return;

    const meses = dashboardData?.meses_disponiveis || [];
    if (!meses.length) return;

    const { data: saldosSupabase, error: errorSaldos } = await client
      .from("doutores_saldos_mensais")
      .select("*")
      .in("competencia", meses);

    if (errorSaldos) return;

    const fallbackDoutores = obterDoutoresFallbackDoDashboard();
    const todosPorNome = new Map();

    for (const item of fallbackDoutores) {
      const chave = normalizarNome(item.nome || item.nome_normalizado || "");
      if (!chave) continue;

      todosPorNome.set(chave, {
        id: item.id,
        nome: item.nome,
        nome_normalizado: chave,
        credito: toNumber(item.credito, 0),
        pix_key: item.pix_key || "",
        ativo: item.ativo !== false,
        updated_by_email: item.updated_by_email || null,
        updated_by_nome: item.updated_by_nome || null
      });
    }

    for (const item of doutoresSupabase || []) {
      const chave = normalizarNome(item.nome || item.nome_normalizado || "");
      if (!chave) continue;

      const existente = todosPorNome.get(chave) || {};

      todosPorNome.set(chave, {
        id: item.id || existente.id || chave,
        nome: item.nome || existente.nome || "",
        nome_normalizado: chave,
        credito: toNumber(item.credito ?? existente.credito, 0),
        pix_key: item.pix_key || existente.pix_key || "",
        ativo: item.ativo !== false,
        updated_by_email: item.updated_by_email || existente.updated_by_email || null,
        updated_by_nome: item.updated_by_nome || existente.updated_by_nome || null
      });
    }

    const saldosPorMesEId = {};

    for (const item of saldosSupabase || []) {
      const comp = item.competencia;
      if (!saldosPorMesEId[comp]) saldosPorMesEId[comp] = {};
      saldosPorMesEId[comp][item.doutor_id] = item;
    }

    for (const competencia of meses) {
      const fallbackSaldos = obterSaldosFallbackDaCompetencia(competencia);
      const utilizadoPorNome = somarUtilizadoPorNomeNosRegistros(competencia);
      const baseMes = [];

      for (const doutor of todosPorNome.values()) {
        if (doutor.ativo === false) continue;

        const chaveNome = normalizarNome(doutor.nome || "");
        const original = fallbackSaldos[chaveNome] || null;
        const saldoSupabase = isUuid(doutor.id)
          ? (saldosPorMesEId[competencia]?.[doutor.id] || null)
          : null;

        const creditoBase = toNumber(doutor.credito, 0);
        const creditoInicial = calcularCreditoInicialDoMes(creditoBase, saldoSupabase, original);

        const utilizadoRegistros = toNumber(utilizadoPorNome[chaveNome], 0);
        const utilizadoFallback = toNumber(original?.utilizado, 0);
        const utilizadoSupabase = toNumber(saldoSupabase?.utilizado, 0);

        const utilizado =
          utilizadoRegistros > 0
            ? utilizadoRegistros
            : (utilizadoFallback > 0 ? utilizadoFallback : utilizadoSupabase);

        const creditoFinal = calcularSaldoFinalDoMes(creditoInicial, utilizado);

        baseMes.push({
          doutor_id: doutor.id,
          doutor: doutor.nome,
          credito_inicial: creditoInicial,
          utilizado,
          credito_disponivel: creditoFinal,
          credito_final: creditoFinal,
          pix_key: doutor.pix_key || original?.pix_key || "",
          updated_by_email: saldoSupabase?.updated_by_email || doutor.updated_by_email || null,
          updated_by_nome: saldoSupabase?.updated_by_nome || doutor.updated_by_nome || null
        });
      }

      dashboardData.saldos_por_competencia[competencia] = baseMes.sort((a, b) =>
        String(a.doutor || "").localeCompare(String(b.doutor || ""), "pt-BR")
      );
    }
  } catch (err) {
    console.error("Erro ao sincronizar saldos:", err);
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

  if (competenciaPadrao && meses.includes(competenciaPadrao)) filtroMes.value = competenciaPadrao;
  else if (meses.length) filtroMes.value = meses[0];
}

function preencherFiltroCidade() {
  const filtroCidade = byId("filtroCidade");
  if (!filtroCidade) return;

  const cidadeSelecionada = filtroCidade.value;
  const registros = getRegistrosCompetencia(getCompetenciaAtual());
  const cidades = [...new Set(registros.map(item => item.unidade).filter(Boolean))].sort();

  filtroCidade.innerHTML =
    `<option value="">Todas</option>` +
    cidades.map(item => `<option value="${escapeHtml(item)}">${escapeHtml(item)}</option>`).join("");

  if (cidades.includes(cidadeSelecionada)) filtroCidade.value = cidadeSelecionada;
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

  if (doutores.includes(doutorSelecionado)) filtroDoutor.value = doutorSelecionado;
}

function getRegistrosFiltrados() {
  const competencia = getCompetenciaAtual();
  const cidade = getCidadeAtual();
  const doutor = getDoutorAtual();

  let registros = getRegistrosCompetencia(competencia);
  if (cidade) registros = registros.filter(item => String(item.unidade || "") === cidade);
  if (doutor) registros = registros.filter(item => String(item.doutor_final || "") === doutor);

  return registros;
}

function getSaldosFiltrados() {
  const competencia = getCompetenciaAtual();
  const doutor = getDoutorAtual();

  let saldos = getSaldosCompetencia(competencia);
  if (doutor) saldos = saldos.filter(item => String(item.doutor || "") === doutor);

  return saldos;
}

function obterPercentual(utilizado, creditoInicial) {
  const credito = toNumber(creditoInicial, 0);
  if (credito <= 0) return 0;
  return (toNumber(utilizado, 0) / credito) * 100;
}

function obterStatus(percentual) {
  if (percentual >= 100) return { classe: "status-red", texto: "Bloqueado", dot: "dot-red" };
  if (percentual >= 50) return { classe: "status-yellow", texto: "Atenção", dot: "dot-yellow" };
  return { classe: "status-green", texto: "Controlado", dot: "dot-green" };
}

function montarResumoDoutores(saldos) {
  return saldos
    .map(item => {
      const creditoInicial = toNumber(item.credito_inicial, 0);
      const utilizado = toNumber(item.utilizado, 0);
      const creditoDisponivel = toNumber(item.credito_disponivel ?? item.credito_final, 0);
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
    .sort((a, b) => String(a.doutor || "").localeCompare(String(b.doutor || ""), "pt-BR"));
}

function classificarCardDoutor(item) {
  if (item.percentual >= 100) return "bloqueado";
  if (item.percentual >= 50) return "atencao";
  return "controlado";
}

function tituloStatusCard(tipo) {
  if (tipo === "bloqueado") return "Bloqueado";
  if (tipo === "atencao") return "Atenção";
  return "Controlado";
}

function obterPixKeyDoDoutor(nomeDoutor) {
  const saldos = getSaldosCompetencia(getCompetenciaAtual());
  const chave = normalizarNome(nomeDoutor);
  const item = saldos.find(s => normalizarNome(s.doutor) === chave);
  return item?.pix_key || "";
}

function montarCardDoutorStatus(item) {
  const tipo = classificarCardDoutor(item);
  const saldoClasse = item.creditoDisponivel < 0 ? "negative" : "";
  const chave = normalizarNome(item.doutor);
  const cidadeAtual = cidadesAtuaisCache[chave] || "";
  const pixKey = obterPixKeyDoDoutor(item.doutor);
  const doutorEscapado = escapeHtml(item.doutor);

  return `
    <div class="doctor-status-card ${tipo}">
      <div class="doctor-card-top">
        <div class="doctor-card-name">${doutorEscapado}</div>
        <div class="doctor-card-status ${tipo}">
          ${tituloStatusCard(tipo)}
        </div>
      </div>

      <div class="doctor-card-values">
        <div class="doctor-card-metric">
          <small>Crédito inicial</small>
          <strong>${formatarMoeda(item.creditoInicial)}</strong>
        </div>

        <div class="doctor-card-metric">
          <small>Utilizado</small>
          <strong>${formatarMoeda(item.utilizado)}</strong>
        </div>

        <div class="doctor-card-metric">
          <small>Saldo</small>
          <strong class="${saldoClasse}">${formatarMoeda(item.creditoDisponivel)}</strong>
        </div>

        <div class="doctor-card-metric">
          <small>% utilizado</small>
          <strong>${item.percentual.toFixed(1)}%</strong>
        </div>
      </div>

      <div class="doctor-card-pix">
        <small>Chave PIX</small>
        <strong>${pixKey ? escapeHtml(pixKey) : "Não informada"}</strong>
      </div>

      <div class="doctor-city-box">
        <label>Cidade atual usando a chave PIX</label>
        <input
          class="doctor-city-input"
          list="listaCidadesAtuais"
          value="${escapeHtml(cidadeAtual)}"
          placeholder="Digite ou selecione a cidade"
          onchange="salvarCidadeAtualDoutor(this.dataset.doutor, this.value)"
          data-doutor="${doutorEscapado}"
        />
      </div>
    </div>
  `;
}
