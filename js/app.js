* {
  box-sizing: border-box;
}

:root {
  --bg-main: #071224;
  --bg-secondary: #0d1830;
  --panel: rgba(19, 31, 58, 0.92);
  --panel-2: rgba(25, 39, 73, 0.92);
  --line: rgba(255, 255, 255, 0.08);
  --text: #f4f7ff;
  --muted: #aeb9d2;
  --primary: #5f82ff;
  --primary-2: #7396ff;
  --success: #2bd98f;
  --warning: #f4c84d;
  --danger: #ff5d78;
  --shadow: 0 18px 45px rgba(0, 0, 0, 0.28);
  --radius-xl: 24px;
}

html,
body {
  margin: 0;
  min-height: 100%;
  font-family: Inter, Arial, sans-serif;
  color: var(--text);
  background:
    radial-gradient(circle at top right, rgba(59, 111, 255, 0.22), transparent 20%),
    radial-gradient(circle at bottom right, rgba(32, 210, 145, 0.14), transparent 18%),
    linear-gradient(180deg, var(--bg-secondary), var(--bg-main));
}

body {
  min-height: 100vh;
}

.hidden {
  display: none !important;
}

/* LOGIN */
.auth-screen {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.auth-card {
  width: 100%;
  max-width: 540px;
  background: linear-gradient(180deg, rgba(14, 34, 63, 0.98) 0%, rgba(6, 21, 42, 0.98) 100%);
  border: 1px solid rgba(55, 138, 255, 0.25);
  border-radius: 28px;
  padding: 42px 36px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.45);
}

.auth-card h1 {
  font-size: 56px;
  line-height: 1;
  margin: 0 0 18px;
  font-weight: 800;
}

.auth-subtitle {
  margin: 0 0 28px;
  font-size: 18px;
  color: #90a7cc;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.auth-form label {
  font-size: 16px;
  font-weight: 700;
  color: #ffffff;
  margin-top: 4px;
}

.auth-form input {
  width: 100%;
  height: 58px;
  border-radius: 18px;
  border: none;
  background: #d9e2ee;
  color: #111827;
  padding: 0 18px;
  font-size: 20px;
  outline: none;
}

.auth-actions {
  display: flex;
  gap: 14px;
  margin-top: 18px;
}

.link-button {
  background: transparent;
  border: 0;
  color: #74d7ff;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  padding: 0;
  margin-top: 18px;
}

.auth-message {
  margin-top: 18px;
  min-height: 20px;
  color: #82f7c2;
  font-size: 14px;
}

.auth-message.error {
  color: #ff9cae;
}

/* DASH */
.layout {
  display: flex;
  min-height: 100vh;
  width: 100%;
}

.sidebar {
  width: 290px;
  min-width: 290px;
  background: rgba(5, 12, 26, 0.9);
  border-right: 1px solid rgba(255, 255, 255, 0.05);
  padding: 22px;
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 24px;
}

.brand-icon {
  width: 48px;
  height: 48px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #7f9cff, #5f82ff);
  color: #fff;
  font-size: 22px;
  font-weight: 800;
  box-shadow: 0 10px 24px rgba(95, 130, 255, 0.32);
}

.brand-text h1 {
  margin: 0;
  font-size: 17px;
  font-weight: 800;
}

.brand-text p {
  margin: 4px 0 0;
  color: var(--muted);
  font-size: 13px;
}

.sidebar-card {
  background: rgba(32, 42, 72, 0.72);
  border: 1px solid var(--line);
  border-radius: 20px;
  padding: 18px;
  margin-bottom: 18px;
  backdrop-filter: blur(12px);
  box-shadow: var(--shadow);
}

.sidebar-card h2 {
  margin: 0 0 14px;
  font-size: 18px;
}

.sidebar-card label {
  display: block;
  margin: 14px 0 8px;
  color: var(--muted);
  font-size: 14px;
}

select,
input[type="text"],
input[type="number"] {
  width: 100%;
  height: 46px;
  border-radius: 14px;
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.08);
  color: var(--text);
  padding: 0 14px;
  outline: none;
}

select option {
  color: #111827;
}

.sidebar-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 16px;
}

.btn {
  height: 44px;
  border: 0;
  border-radius: 14px;
  cursor: pointer;
  font-weight: 700;
  font-size: 14px;
  transition: transform 0.15s ease, opacity 0.15s ease;
}

.btn:hover {
  transform: translateY(-1px);
  opacity: 0.96;
}

.btn-primary {
  background: linear-gradient(135deg, var(--primary-2), var(--primary));
  color: #fff;
  box-shadow: 0 10px 24px rgba(95, 130, 255, 0.28);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.08);
  color: var(--text);
  border: 1px solid var(--line);
}

.btn-small {
  height: 34px;
  padding: 0 12px;
  font-size: 12px;
}

.main {
  flex: 1;
  min-width: 0;
  padding: 28px 24px 40px;
}

.hero {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 22px;
}

.hero h2 {
  margin: 0;
  font-size: 34px;
  font-weight: 800;
}

.hero p {
  margin: 8px 0 0;
  color: var(--muted);
  font-size: 16px;
}

.hero-badges {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.badge {
  border-radius: 999px;
  padding: 10px 16px;
  font-weight: 700;
  font-size: 13px;
  color: #e6eeff;
  background: rgba(95, 130, 255, 0.16);
  border: 1px solid rgba(95, 130, 255, 0.26);
}

.badge-muted {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.08);
}

.panel {
  background: linear-gradient(180deg, var(--panel-2), var(--panel));
  border: 1px solid var(--line);
  border-radius: var(--radius-xl);
  padding: 18px;
  margin-bottom: 18px;
  box-shadow: var(--shadow);
  backdrop-filter: blur(14px);
}

.panel-head {
  margin-bottom: 16px;
}

.panel-head h3 {
  margin: 0;
  font-size: 22px;
}

.panel-head p {
  margin: 6px 0 0;
  color: var(--muted);
  font-size: 14px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
}

.stat-card {
  border-radius: 18px;
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.04);
  padding: 16px;
}

.stat-title {
  color: var(--muted);
  font-size: 13px;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 26px;
  font-weight: 800;
  line-height: 1.1;
}

.table-wrap {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  min-width: 980px;
}

thead th {
  background: rgba(255, 255, 255, 0.06);
  color: #eef3ff;
  text-align: left;
  padding: 14px 12px;
  font-size: 14px;
  font-weight: 700;
}

tbody td {
  padding: 14px 12px;
  border-top: 1px solid var(--line);
  color: #e8edff;
  font-size: 14px;
  vertical-align: top;
}

tbody tr:hover {
  background: rgba(255, 255, 255, 0.03);
}

.text-success {
  color: #8df3c7;
  font-weight: 700;
}

.text-warning {
  color: #ffe18c;
  font-weight: 700;
}

.text-danger {
  color: #ff9eb0;
  font-weight: 700;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 7px 11px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
}

.status-green {
  background: rgba(43, 217, 143, 0.14);
  color: #99ffd6;
}

.status-yellow {
  background: rgba(244, 200, 77, 0.16);
  color: #ffe594;
}

.status-red {
  background: rgba(255, 93, 120, 0.16);
  color: #ffb4c1;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  display: inline-block;
}

.dot-green {
  background: var(--success);
}

.dot-yellow {
  background: var(--warning);
}

.dot-red {
  background: var(--danger);
}

.empty-state {
  text-align: center;
  color: var(--muted);
  padding: 24px !important;
}

.admin-form-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(160px, 1fr));
  gap: 12px;
}

@media (max-width: 1100px) {
  .layout {
    flex-direction: column;
  }

  .sidebar {
    width: 100%;
    min-width: 100%;
    position: relative;
    height: auto;
    border-right: 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  }

  .main {
    padding: 20px;
  }

  .hero {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 640px) {
  .auth-card {
    padding: 28px 22px;
  }

  .auth-card h1 {
    font-size: 40px;
  }

  .auth-form input {
    font-size: 17px;
  }

  .auth-actions {
    flex-direction: column;
  }

  .admin-form-grid {
    grid-template-columns: 1fr;
  }
}
