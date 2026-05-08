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
  document.body.classList.add("modo-inicio-limpo");

  if (dashboardData) {
    atualizarDashboard();
  }
}

function mostrarAdmin() {
  if (!currentUserIsAdmin) return;

  byId("dashboardView")?.classList.add("hidden");
  byId("adminView")?.classList.remove("hidden");
  byId("filtrosSidebar")?.classList.add("hidden");
  document.body.classList.remove("modo-inicio-limpo");

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
