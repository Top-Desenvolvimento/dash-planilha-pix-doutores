const SUPABASE_URL = "https://dgmqwcbjbluoplczfflo.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRnbXF3Y2JqYmx1b3BsY3pmZmxvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUxMjk4MzYsImV4cCI6MjA5MDcwNTgzNn0.qCBdP9nabXepmPxwFnUgPrhMofpR5vmPWAgdOJmHeEs";

let supabaseClient = null;

(function iniciarSupabase() {
  try {
    if (
      !window.supabase ||
      !window.supabase.createClient ||
      !SUPABASE_URL ||
      SUPABASE_URL.includes("COLE_AQUI") ||
      !SUPABASE_ANON_KEY ||
      SUPABASE_ANON_KEY.includes("COLE_AQUI")
    ) {
      console.error("Supabase não configurado corretamente.");
      window.supabaseClient = null;
      return;
    }

    supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
    window.supabaseClient = supabaseClient;
    console.log("Supabase inicializado com sucesso.");
  } catch (err) {
    console.error("Erro ao inicializar Supabase:", err);
    window.supabaseClient = null;
  }
})();
