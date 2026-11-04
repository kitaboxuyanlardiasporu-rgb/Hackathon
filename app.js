// Qiymətləndirmə portalı — müştəri tərəfi
"use strict";

// ================================================================ köməkçilər
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
const app = document.getElementById("app");

const ESC = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ESC[c]);

const PATHS = {
  lock: '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
  unlock: '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 7.6-1.8"/>',
  check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
  checkCircle: '<circle cx="12" cy="12" r="9"/><path d="M8 12.5l3 3 5-6"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  alert: '<path d="M12 3.5 2.5 20h19L12 3.5z"/><path d="M12 10v4.5M12 17.3v.1"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5.5M12 7.8v.1"/>',
  x: '<path d="M6 6l12 12M18 6 6 18"/>',
  menu: '<path d="M4 7h16M4 12h16M4 17h16"/>',
  eye: '<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
  eyeOff: '<path d="M3 3l18 18"/><path d="M10.6 5.1A10.8 10.8 0 0 1 12 5c6.4 0 10 7 10 7a17 17 0 0 1-3.2 4.1M6.6 6.6A16.6 16.6 0 0 0 2 12s3.6 7 10 7a10 10 0 0 0 5.4-1.6"/><path d="M9.9 9.9a3 3 0 0 0 4.2 4.2"/>',
  logout: '<path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3"/><path d="M10 17l5-5-5-5M15 12H3"/>',
  download: '<path d="M12 4v11M7 10l5 5 5-5M5 20h14"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  edit: '<path d="M4 20h4L19 9l-4-4L4 16v4z"/><path d="M13.5 6.5l4 4"/>',
  trash: '<path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/>',
  grid: '<rect x="4" y="4" width="7" height="7" rx="1.5"/><rect x="13" y="4" width="7" height="7" rx="1.5"/><rect x="4" y="13" width="7" height="7" rx="1.5"/><rect x="13" y="13" width="7" height="7" rx="1.5"/>',
  sliders: '<path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12"/><circle cx="16" cy="6" r="2"/><circle cx="10" cy="12" r="2"/><circle cx="18" cy="18" r="2"/>',
  users: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><path d="M16 4.5a3.5 3.5 0 0 1 0 7M18 14a6.5 6.5 0 0 1 3.5 6"/>',
  list: '<path d="M9 6h11M9 12h11M9 18h11"/><path d="M4.5 6h.01M4.5 12h.01M4.5 18h.01"/>',
  userCheck: '<circle cx="10" cy="8" r="4"/><path d="M3 20a7 7 0 0 1 12.5-4.3"/><path d="M15.5 18.5l2 2 4-4"/>',
  clipboard: '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4V3h6v1M9 11h6M9 15h4"/>',
  trophy: '<path d="M8 4h8v5a4 4 0 0 1-8 0V4z"/><path d="M8 6H5a3 3 0 0 0 3 4M16 6h3a3 3 0 0 1-3 4M12 13v4M8 21h8M9 17h6"/>',
  history: '<path d="M3 12a9 9 0 1 0 3-6.7"/><path d="M3 4v4h4"/><path d="M12 8v4l3 2"/>',
  key: '<circle cx="8" cy="15" r="4"/><path d="M11 12l9-9M17 6l3 3"/>',
  refresh: '<path d="M20 11a8 8 0 0 0-14.3-4.9L4 8"/><path d="M4 4v4h4"/><path d="M4 13a8 8 0 0 0 14.3 4.9L20 16"/><path d="M20 20v-4h-4"/>',
  shield: '<path d="M12 3 4.5 6v5.5c0 4.6 3.2 8.3 7.5 9.5 4.3-1.2 7.5-4.9 7.5-9.5V6L12 3z"/><path d="M9 12l2 2 4-4"/>',
  layers: '<path d="M12 3 2.5 8 12 13l9.5-5L12 3z"/><path d="M2.5 12.5 12 17.5l9.5-5"/><path d="M2.5 16.5 12 21.5l9.5-5"/>',
  play: '<path d="M7 5l12 7-12 7V5z"/>',
  stop: '<rect x="6" y="6" width="12" height="12" rx="2"/>',
  inbox: '<path d="M3 13h5l1.5 3h5L16 13h5"/><path d="M5 5h14l2 8v6H3v-6l2-8z"/>',
};
const icon = (name, cls = "") => `<svg class="icon ${cls}" viewBox="0 0 24 24" aria-hidden="true" focusable="false">${PATHS[name] || ""}</svg>`;

const fmtTime = (iso) => {
  if (!iso) return "";
  try {
    const parts = new Intl.DateTimeFormat("en-GB", {
      timeZone: "Asia/Baku", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hour12: false,
    }).formatToParts(new Date(iso));
    const p = Object.fromEntries(parts.map((x) => [x.type, x.value]));
    return `${p.day}.${p.month}.${p.year}, ${p.hour}:${p.minute}`;
  } catch { return iso; }
};

const store = {
  get(k) { try { return JSON.parse(localStorage.getItem(k) || "null"); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* yaddaş əlçatan deyil */ } },
  del(k) { try { localStorage.removeItem(k); } catch { /* */ } },
};

// ================================================================ API
class ApiError extends Error {
  constructor(status, message) { super(message); this.status = status; }
}

async function api(method, path, body) {
  const opts = { method, credentials: "same-origin", headers: { Accept: "application/json" } };
  if (method !== "GET") opts.headers["X-Requested-With"] = "qiymetlendirme-portali";
  if (body !== undefined) { opts.headers["Content-Type"] = "application/json"; opts.body = JSON.stringify(body); }
  let res;
  try { res = await fetch(path, opts); } catch {
    throw new ApiError(0, "Serverlə əlaqə qurulmadı. İnternet bağlantısını yoxlayıb yenidən cəhd edin.");
  }
  let data = null;
  try { data = await res.json(); } catch { /* */ }
  if (!res.ok) {
    const msg = (data && data.detail) || (res.status >= 500 ? "Serverdə xəta baş verdi. Bir az sonra yenidən cəhd edin." : "Xəta baş verdi.");
    if (res.status === 401 && path !== "/api/auth/login") { onSessionLost(); }
    throw new ApiError(res.status, msg);
  }
  return data;
}

let ME = null;
function onSessionLost() {
  if (!ME) return;
  ME = null;
  closeAllModals();
  toast("Sessiya bitib. Yenidən daxil olun.", "error");
  renderLogin();
}

// ================================================================ bildiriş
function toast(message, type = "ok") {
  const box = document.getElementById("toasts");
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.innerHTML = `${icon(type === "error" ? "alert" : type === "info" ? "info" : "checkCircle")}<div>${esc(message)}</div>`;
  box.appendChild(el);
  setTimeout(() => { el.classList.add("out"); setTimeout(() => el.remove(), 200); }, type === "error" ? 6000 : 3500);
}

// ================================================================ dialoq
const openModals = new Set();
function closeAllModals() { openModals.forEach((d) => { try { d.close(); d.remove(); } catch { /* */ } }); openModals.clear(); }

/**
 * modal({ title, body, confirmText, cancelText, danger, onConfirm, onOpen })
 * onConfirm(dialog) false qaytararsa və ya xəta atarsa, pəncərə açıq qalır.
 */
function modal({ title, body, confirmText = "Təsdiqlə", cancelText = "Ləğv et", danger = false, onConfirm, onOpen, wide = false }) {
  return new Promise((resolve) => {
    const d = document.createElement("dialog");
    d.className = "modal";
    if (wide) d.style.width = "min(640px, calc(100vw - 32px))";
    const tid = `m${Math.random().toString(36).slice(2)}`;
    d.setAttribute("aria-labelledby", tid);
    d.innerHTML = `
      <form method="dialog" novalidate>
        <div class="modal-body">
          <h2 id="${tid}">${esc(title)}</h2>
          <div class="stack-sm">${body}</div>
          <div class="modal-error" role="alert"></div>
        </div>
        <div class="modal-foot">
          <button type="button" class="btn btn-secondary" data-cancel>${esc(cancelText)}</button>
          ${onConfirm ? `<button type="submit" class="btn ${danger ? "btn-danger" : "btn-primary"}" data-ok>${esc(confirmText)}</button>` : ""}
        </div>
      </form>`;
    document.body.appendChild(d);
    openModals.add(d);
    let result = false;
    let busy = false;
    const finish = () => {
      d.classList.add("closing");
      setTimeout(() => { d.close(); d.remove(); openModals.delete(d); resolve(result); }, 150);
    };
    d.addEventListener("cancel", (e) => { e.preventDefault(); if (!busy) finish(); });
    $("[data-cancel]", d).addEventListener("click", () => { if (!busy) finish(); });
    $("form", d).addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!onConfirm || busy) return;
      const ok = $("[data-ok]", d);
      const errBox = $(".modal-error", d);
      errBox.innerHTML = "";
      busy = true;
      ok.disabled = true;
      $("[data-cancel]", d).disabled = true;
      const label = ok.innerHTML;
      ok.innerHTML = `<span class="spinner" aria-hidden="true"></span> Gözləyin…`;
      try {
        const r = await onConfirm(d);
        if (r === false) { busy = false; ok.disabled = false; $("[data-cancel]", d).disabled = false; ok.innerHTML = label; return; }
        result = r === undefined ? true : r;
        busy = false;
        finish();
      } catch (err) {
        busy = false;
        ok.disabled = false;
        $("[data-cancel]", d).disabled = false;
        ok.innerHTML = label;
        errBox.innerHTML = `<div class="alert alert-error">${icon("alert")}<div>${esc(err.message)}</div></div>`;
      }
    });
    d.showModal();
    if (onOpen) onOpen(d);
  });
}

function setBusy(btn, busy, text = "Gözləyin…") {
  if (busy) {
    btn.dataset.label = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner" aria-hidden="true"></span> ${esc(text)}`;
  } else {
    btn.disabled = false;
    if (btn.dataset.label) btn.innerHTML = btn.dataset.label;
  }
}

function pwField(id, label, { autocomplete = "new-password", hint = "" } = {}) {
  return `
    <div class="field">
      <label for="${id}">${esc(label)}</label>
      <div class="pw-wrap">
        <input class="input" id="${id}" name="${id}" type="password" autocomplete="${autocomplete}" required>
        <button type="button" class="btn btn-ghost btn-icon pw-toggle" data-pw="${id}" aria-label="Parolu göstər" aria-pressed="false">${icon("eye")}</button>
      </div>
      ${hint ? `<span class="hint">${esc(hint)}</span>` : ""}
    </div>`;
}

document.addEventListener("click", (e) => {
  const b = e.target.closest("[data-pw]");
  if (!b) return;
  const input = document.getElementById(b.dataset.pw);
  const show = input.type === "password";
  input.type = show ? "text" : "password";
  b.setAttribute("aria-pressed", String(show));
  b.setAttribute("aria-label", show ? "Parolu gizlət" : "Parolu göstər");
  b.innerHTML = icon(show ? "eyeOff" : "eye");
});

const errorBox = (msg, retry = true) => `
  <div class="alert alert-error" role="alert">${icon("alert")}<div class="stack-sm"><div>${esc(msg)}</div>
  ${retry ? `<div><button class="btn btn-secondary btn-sm" data-retry>${icon("refresh")} Yenidən cəhd et</button></div>` : ""}</div></div>`;

const loadingBox = (t = "Yüklənir…") => `<div class="loading"><span class="spinner" aria-hidden="true"></span> ${esc(t)}</div>`;

function setProgress(el, pct) {
  const span = el.querySelector("span");
  requestAnimationFrame(() => { span.style.width = `${Math.max(0, Math.min(100, pct))}%`; });
  el.classList.toggle("done", pct >= 100);
}

// ================================================================ giriş
function renderLogin(errorMsg = "") {
  document.title = "Giriş — Qiymətləndirmə portalı";
  if (location.hash) history.replaceState(null, "", location.pathname);
  app.innerHTML = `
    <main id="main" class="login-page">
      <div class="card login-card enter">
        <div class="brand">${'<span class="brand-mark">' + icon("check") + "</span>"}<span class="brand-name">Qiymətləndirmə portalı</span></div>
        <h1 class="sr-only">Giriş</h1>
        <p class="muted" style="margin-top:14px">Davam etmək üçün hesabınıza daxil olun.</p>
        <form id="login-form" class="stack" style="margin-top:20px" novalidate>
          <div id="login-error" role="alert">${errorMsg ? `<div class="alert alert-error">${icon("alert")}<div>${esc(errorMsg)}</div></div>` : ""}</div>
          <div class="field">
            <label for="username">İstifadəçi adı</label>
            <input class="input" id="username" name="username" autocomplete="username" autocapitalize="none" spellcheck="false" required>
          </div>
          ${pwField("password", "Parol", { autocomplete: "current-password" })}
          <button class="btn btn-primary btn-block" type="submit">Daxil ol</button>
        </form>
      </div>
    </main>`;
  const form = $("#login-form");
  $("#username").focus();
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const username = $("#username").value.trim();
    const password = $("#password").value;
    const errEl = $("#login-error");
    $("#username").removeAttribute("aria-invalid");
    $("#password").removeAttribute("aria-invalid");
    if (!username || !password) {
      errEl.innerHTML = `<div class="alert alert-error">${icon("alert")}<div>İstifadəçi adı və parolu daxil edin.</div></div>`;
      if (!username) $("#username").setAttribute("aria-invalid", "true");
      if (!password) $("#password").setAttribute("aria-invalid", "true");
      return;
    }
    const btn = $("button[type=submit]", form);
    setBusy(btn, true, "Daxil olunur…");
    try {
      const r = await api("POST", "/api/auth/login", { username, password });
      ME = r.user;
      startApp();
    } catch (err) {
      setBusy(btn, false);
      errEl.innerHTML = `<div class="alert alert-error">${icon("alert")}<div>${esc(err.message)}</div></div>`;
      $("#password").setAttribute("aria-invalid", "true");
      $("#password").select();
    }
  });
}

async function logout() {
  try { await api("POST", "/api/auth/logout"); } catch { /* */ }
  ME = null;
  document.getElementById("toasts").innerHTML = "";
  renderLogin();
}

// ================================================================ başlanğıc
async function boot() {
  try {
    const r = await api("GET", "/api/auth/me");
    ME = r.user;
    startApp();
  } catch (err) {
    if (err.status === 401) renderLogin();
    else app.innerHTML = `<main id="main" class="login-page"><div class="card login-card">${errorBox(err.message)}</div></main>`;
    const b = $("[data-retry]");
    if (b) b.addEventListener("click", boot);
  }
}

const isAdmin = () => ME && ME.role === "admin";
const can = (perm) => isAdmin() || !!(ME && ME.role === "operator" && (ME.permissions || []).includes(perm));
const ROLE_LABEL = { admin: "Admin", operator: "Operator", jury: "Jüri" };

function startApp() {
  if (ME.role === "admin" || ME.role === "operator") AdminApp.start();
  else JuryApp.start();
}

// ================================================================ ADMIN
let CUR = null; // seçilmiş müsabiqənin id-si
const ADM = () => `/api/admin/contests/${CUR}`;

const SECTIONS = [
  { id: "musabiqeler", title: "Müsabiqələr", icon: "layers", global: true },
  { id: "icmal", title: "İcmal", icon: "grid" },
  { id: "ayarlar", title: "Müsabiqə ayarları", icon: "sliders", perm: "contests" },
  { id: "komandalar", title: "Komandalar", icon: "users", perm: "teams" },
  { id: "meyarlar", title: "Meyarlar", icon: "list", perm: "criteria" },
  { id: "juriler", title: "Jürilər", icon: "userCheck", perm: "juries" },
  { id: "qiymetlendirmeler", title: "Qiymətləndirmələr", icon: "clipboard", admin: true },
  { id: "neticeler", title: "Nəticələr", icon: "trophy", admin: true },
  { id: "tarixce", title: "Tarixçə", icon: "history", admin: true },
  { id: "operatorlar", title: "Operatorlar", icon: "shield", admin: true, global: true },
];
const allowed = (sec) => (sec.admin ? isAdmin() : sec.perm ? can(sec.perm) : true);

const TYPE_HELP = {
  unique: {
    label: "Unikal bal — 1–N, təkrarsız",
    short: "N — komanda sayı",
    text: (n) => `Hər jüri hər meyar üzrə 1–N ballarından istifadə edir və eyni meyarda bir balı yalnız bir komandaya verə bilər. N komanda sayıdır (hazırda N = ${n}). Məhdudiyyət hər jüri və hər meyar üçün ayrıca tətbiq olunur.`,
    example: "Nümunə: «İnnovativlik» meyarında A komandasına 5 bal verilibsə, həmin meyarda başqa komandaya 5 bal vermək olmaz. Digər meyarlarda 5 baldan istifadə etmək olar.",
  },
  scale5: {
    label: "Şkala — 1–5, təkrara icazə verilir",
    short: "Komanda sayından asılı deyil",
    text: () => "Jüri hər komandaya hər meyar üzrə 1-dən 5-ə qədər tam bal verir. Eyni bal bir neçə komandaya verilə bilər.",
    example: "Nümunə: «İnnovativlik» meyarında həm A, həm də B komandasına 4 bal vermək olar.",
  },
  custom: {
    label: "Fərdi şkala — 1–n, təkrara icazə verilir",
    short: "n — sizin təyin etdiyiniz maksimum bal",
    text: () => "Şkalanın yuxarı həddini (n) siz müəyyən edirsiniz: 2–100. Jüri 1-dən n-ə qədər tam bal verir; eyni bal bir neçə komandaya verilə bilər. n komanda sayından asılı deyil.",
    example: "Nümunə: n = 10 olduqda həm A, həm də B komandasına 8 bal vermək olar.",
  },
};

const AdminApp = {
  section: null,
  start() {
    document.title = "Qiymətləndirmə portalı";
    app.innerHTML = `
      <div class="shell">
        <header class="topbar">
          <button class="btn btn-ghost btn-icon" id="menu-btn" aria-label="Menyunu aç" aria-expanded="false" aria-controls="sidebar">${icon("menu")}</button>
          <span class="brand-name">Qiymətləndirmə portalı</span>
        </header>
        <div class="scrim" id="scrim"></div>
        <aside class="sidebar" id="sidebar" aria-label="Admin menyusu">
          <div class="brand"><span class="brand-mark">${icon("check")}</span><span class="brand-name">Qiymətləndirmə portalı</span></div>
          <div class="contest-switch">
            <label for="contest-select">Seçilmiş müsabiqə</label>
            <select id="contest-select"></select>
          </div>
          <nav class="nav" id="nav"></nav>
          <div class="sidebar-foot">
            <div class="who">${ROLE_LABEL[ME.role]}<strong>${esc(ME.username)}</strong></div>
            <a class="btn btn-ghost" href="#/hesab" data-nav="hesab">${icon("key")} Parolu dəyiş</a>
            <button class="btn btn-ghost" id="logout-btn">${icon("logout")} Çıxış</button>
          </div>
        </aside>
        <main class="main" id="main" tabindex="-1"></main>
      </div>`;
    this.renderNav();
    const sb = $("#sidebar"), scrim = $("#scrim"), mb = $("#menu-btn");
    const setMenu = (open) => {
      sb.classList.toggle("open", open);
      scrim.classList.toggle("open", open);
      mb.setAttribute("aria-expanded", String(open));
      mb.setAttribute("aria-label", open ? "Menyunu bağla" : "Menyunu aç");
      if (open) $(".nav a", sb).focus();
    };
    mb.addEventListener("click", () => setMenu(!sb.classList.contains("open")));
    scrim.addEventListener("click", () => setMenu(false));
    sb.addEventListener("keydown", (e) => { if (e.key === "Escape" && sb.classList.contains("open")) { setMenu(false); mb.focus(); } });
    sb.addEventListener("click", (e) => { if (e.target.closest("a")) setMenu(false); });
    $("#logout-btn").addEventListener("click", logout);
    $("#contest-select").addEventListener("change", (e) => {
      this.select(+e.target.value);
      toast(`Seçildi: «${this.current().name}».`, "info");
      if (SECTIONS.find((x) => x.id === this.section)?.global) location.hash = "#/icmal"; else this.route();
    });
    window.onhashchange = () => this.route();
    this.route();
  },
  renderNav() {
    const nav = $("#nav");
    if (!nav) return;
    this._navKey = (ME.permissions || []).join(",");
    nav.innerHTML = SECTIONS.filter(allowed)
      .map((s) => `<a href="#/${s.id}" data-nav="${s.id}" ${s.id === this.section ? 'aria-current="page"' : ""}>${icon(s.icon)}<span>${s.title}</span></a>`).join("");
  },
  async refreshMe() {
    // Admin icazələri dəyişibsə, menyu dərhal yenilənir.
    const r = await api("GET", "/api/auth/me");
    ME = r.user;
    if ((ME.permissions || []).join(",") !== this._navKey) this.renderNav();
  },
  contests: [],
  current() { return this.contests.find((c) => c.id === CUR); },
  select(id) {
    CUR = id;
    store.set("qp_cur_contest", id);
    const sel = $("#contest-select");
    if (sel) sel.value = String(id);
  },
  async loadContests() {
    const d = await api("GET", "/api/admin/contests");
    this.contests = d.items;
    const saved = store.get("qp_cur_contest");
    const prev = CUR;
    const ids = this.contests.map((c) => c.id);
    // Seçim yoxdursa, ilk açıq müsabiqə (yoxdursa ən yenisi) seçilir.
    const firstOpen = this.contests.find((c) => c.is_open)?.id;
    let next = ids.includes(CUR) ? CUR : ids.includes(saved) ? saved : firstOpen ?? ids[0] ?? null;
    if (prev && !ids.includes(prev)) toast("Seçilmiş müsabiqə artıq mövcud deyil. Başqa müsabiqə seçildi.", "info");
    const sel = $("#contest-select");
    if (sel) {
      sel.innerHTML = this.contests.length
        ? this.contests.map((c) => `<option value="${c.id}">${esc(c.name)} — ${c.is_open ? "açıq" : "bağlı"}</option>`).join("")
        : `<option value="">— Müsabiqə yoxdur —</option>`;
      sel.disabled = !this.contests.length;
    }
    if (next !== null) this.select(next);
    else { CUR = null; store.del("qp_cur_contest"); }
  },
  contestBar() {
    const c = this.current();
    if (!c) return "";
    return `
      <div class="contest-bar ${c.is_open ? "is-open" : "is-closed"}">
        <div class="cb-text">
          <span class="muted small">Müsabiqə</span>
          <strong>${esc(c.name)}</strong>
        </div>
        ${c.is_open
          ? `<span class="chip chip-ok">${icon("play")} Qiymətləndirmə açıqdır</span>`
          : `<span class="chip chip-muted">${icon("stop")} Qiymətləndirmə bağlıdır</span>`}
        <div class="spacer"></div>
        ${isAdmin() ? `<button class="btn ${c.is_open ? "btn-secondary" : "btn-primary"} btn-sm" data-toggle-open="${c.id}">
          ${c.is_open ? `${icon("stop", "sm")} Qiymətləndirməni bağla` : `${icon("play", "sm")} Qiymətləndirməni aç`}</button>` : ""}
      </div>`;
  },
  async toggleOpen(id) {
    const c = this.contests.find((x) => x.id === id);
    if (!c) return;
    const open = !c.is_open;
    const ok = await modal({
      title: open ? "Qiymətləndirmə açılsın?" : "Qiymətləndirmə bağlansın?",
      body: open
        ? `<p><strong>${esc(c.name)}</strong> üzrə jürilər bal seçib təsdiqləyə biləcək.</p>`
        : `<p><strong>${esc(c.name)}</strong> üzrə jürilər yeni bal təsdiqləyə bilməyəcək. Artıq təsdiqlənmiş ballar saxlanılır; istənilən vaxt yenidən aça bilərsiniz.</p>`,
      confirmText: open ? "Aç" : "Bağla",
      onConfirm: () => api("POST", `/api/admin/contests/${id}/status`, { is_open: open }),
    });
    if (ok) { toast(open ? "Qiymətləndirmə açıldı." : "Qiymətləndirmə bağlandı."); this.route(); }
  },
  route() {
    if (!ME || (ME.role !== "admin" && ME.role !== "operator")) return;
    let id = (location.hash.replace(/^#\/?/, "") || "icmal").split("?")[0];
    if (!SECTIONS.some((s) => s.id === id && allowed(s)) && id !== "hesab") {
      if (location.hash && location.hash !== "#/icmal") history.replaceState(null, "", "#/icmal");
      id = "icmal";
    }
    this.section = id;
    $$("[data-nav]").forEach((a) => { if (a.dataset.nav === id) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current"); });
    const sec = SECTIONS.find((s) => s.id === id);
    document.title = `${sec ? sec.title : "Parolu dəyiş"} — Qiymətləndirmə portalı`;
    const main = $("#main");
    main.innerHTML = loadingBox();
    main.focus({ preventScroll: true });
    window.scrollTo(0, 0);
    const token = (this._token = (this._token || 0) + 1);
    const fail = (err) => {
      if (err.status === 401 || token !== this._token) return;
      main.innerHTML = errorBox(err.message);
      $("[data-retry]", main)?.addEventListener("click", () => this.route());
    };
    Promise.all([this.loadContests(), ME.role === "operator" ? this.refreshMe() : null]).then(() => {
      if (token !== this._token) return;
      if (sec && !allowed(sec)) { toast("Bu bölmə üçün icazəniz yoxdur.", "error"); location.hash = "#/icmal"; return; }
      const scoped = !(sec && sec.global) && id !== "hesab";
      if (scoped && CUR === null) { location.hash = "#/musabiqeler"; return; }
      main.innerHTML = `${scoped ? this.contestBar() : ""}<div id="view">${loadingBox()}</div>`;
      $("[data-toggle-open]", main)?.addEventListener("click", (e) => this.toggleOpen(+e.currentTarget.dataset.toggleOpen));
      const view = $("#view");
      return Promise.resolve(Views[id](view));
    }).catch((err) => {
      // Müsabiqə başqa sessiyada silinibsə, siyahını yeniləyib yenidən cəhd edirik.
      if (err.status === 404 && /Müsabiqə tapılmadı/.test(err.message) && !this._retried) {
        this._retried = true;
        return this.route();
      }
      fail(err);
    }).finally(() => { this._retried = false; });
  },
  refresh() { this.route(); },
};

const pageHead = (title, sub = "", actions = "") => `
  <div class="page-head"><div><h1>${esc(title)}</h1>${sub ? `<p class="sub">${sub}</p>` : ""}</div><div class="spacer"></div>${actions}</div>`;

const statusChip = (final) => final
  ? `<span class="chip chip-ok">${icon("checkCircle")} Yekun nəticələr</span>`
  : `<span class="chip chip-warn">${icon("clock")} Cari nəticələr</span>`;

const lockNotice = (contest, what) => contest.structure_locked ? `
  <div class="alert alert-info">${icon("lock")}<div>${what} İlk qiymətləndirmə ${esc(fmtTime(contest.locked_at))} tarixində təsdiqləndiyi üçün kilidlənib. Adları redaktə etmək mümkündür.</div></div>` : "";

const Views = {
  // ------------------------------------------------------------ Müsabiqələr
  musabiqeler(main) {
    const list = AdminApp.contests;
    main.innerHTML = `
      ${pageHead("Müsabiqələr", isAdmin() ? "Yeni müsabiqə yaradın, seçin, qiymətləndirməni açın və ya bağlayın." : "Müsabiqəni seçin və icazəniz olan bölmələrdə işləyin.")}
      <div class="stack">
        ${can("contests") ? `<form class="card stack enter" id="new-contest" novalidate>
          <h2>Yeni müsabiqə</h2>
          <div class="field"><label for="nc-name">Müsabiqənin adı</label>
            <input class="input" id="nc-name" maxlength="200" required></div>
          <fieldset class="stack-sm" style="border:0;padding:0;margin:0">
            <legend class="label" style="margin-bottom:8px">Qiymətləndirmə tipi</legend>
            <div class="type-options">
              ${["unique", "scale5", "custom"].map((t, i) => `
                <label class="type-opt">
                  <input type="radio" name="nc-type" value="${t}" ${i === 0 ? "checked" : ""}>
                  <span class="box"><span class="t"><span class="dot"></span>${esc(TYPE_HELP[t].label)}</span><span class="d">${esc(TYPE_HELP[t].short)}</span></span>
                </label>`).join("")}
            </div>
          </fieldset>
          <div class="field hidden" id="nc-max-field" style="max-width:260px">
            <label for="nc-max">Maksimum bal</label>
            <input class="input" id="nc-max" type="number" inputmode="numeric" min="2" max="100" step="1" value="10">
            <span class="hint">2 ilə 100 arasında tam ədəd.</span>
          </div>
          <div class="row" style="gap:10px 16px">
            <label class="row" style="gap:8px;min-height:44px;cursor:pointer"><input type="checkbox" id="nc-seed" checked style="width:20px;height:20px"> Nümunə komanda və 5 standart meyarla başla</label>
            <div class="row" id="nc-count-wrap" style="gap:8px"><label for="nc-count">Komanda sayı</label>
              <input class="input" id="nc-count" type="number" inputmode="numeric" min="0" max="100" step="1" value="10" style="width:100px"></div>
          </div>
          <p class="hint">Yeni müsabiqə <strong>bağlı</strong> vəziyyətdə yaradılır. Komanda, meyar və jüriləri hazırladıqdan sonra qiymətləndirməni açın. Jüri hesabları hər müsabiqə üçün ayrıca yaradılır.</p>
          <div id="nc-err" role="alert"></div>
          <div><button class="btn btn-primary" type="submit">${icon("plus")} Müsabiqə yarat</button></div>
        </form>` : ""}
        <div class="stack-sm">
          <h2>Bütün müsabiqələr <span class="muted num" style="font-weight:500">(${list.length})</span></h2>
          ${list.length ? `<div class="contest-list">${list.map((c) => `
            <article class="card contest-item enter ${c.id === CUR ? "is-current" : ""}">
              <div class="row" style="gap:8px">
                <h3 style="flex:1;min-width:0;overflow-wrap:anywhere">${esc(c.name)}</h3>
                ${c.id === CUR ? `<span class="chip chip-info">${icon("check")} Seçilib</span>` : ""}
                ${c.is_open ? `<span class="chip chip-ok">${icon("play")} Açıq</span>` : `<span class="chip chip-muted">${icon("stop")} Bağlı</span>`}
              </div>
              <div class="contest-meta small">
                <span>${esc(c.summary)}</span>
                <span class="num">${c.progress.teams} komanda · ${c.criteria_count} meyar · ${c.progress.juries} jüri</span>
                <span class="num">Qiymətləndirmə: ${c.progress.completed} / ${c.progress.expected} (${c.progress.percent}%)</span>
                <span class="muted">Yaradılıb: ${esc(fmtTime(c.created_at))}</span>
              </div>
              <div class="progress sm" data-cp="${c.id}" role="progressbar" aria-label="${esc(c.name)} irəliləyişi" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${c.progress.percent}"><span></span></div>
              <div class="row" style="gap:6px">
                ${c.id !== CUR ? `<button class="btn btn-secondary btn-sm" data-pick="${c.id}">Seç</button>` : `<a class="btn btn-secondary btn-sm" href="#/icmal">İcmala keç</a>`}
                ${isAdmin() ? `<button class="btn btn-ghost btn-sm" data-toggle-open="${c.id}">${c.is_open ? `${icon("stop", "sm")} Bağla` : `${icon("play", "sm")} Aç`}</button>
                <div class="spacer"></div>
                <button class="btn btn-danger-ghost btn-sm" data-del-contest="${c.id}">${icon("trash", "sm")} Sil</button>` : ""}
              </div>
            </article>`).join("")}</div>` : `<div class="card empty">${icon("layers")}<p>Hələ müsabiqə yoxdur. Yuxarıdakı formadan yeni müsabiqə yaradın.</p></div>`}
        </div>
      </div>`;
    list.forEach((c) => setProgress($(`[data-cp="${c.id}"]`, main), c.progress.percent));

    const form = $("#new-contest");
    if (form) {
    const syncForm = () => {
      const t = $("input[name=nc-type]:checked", form).value;
      $("#nc-max-field").classList.toggle("hidden", t !== "custom");
      $("#nc-count-wrap").classList.toggle("hidden", !$("#nc-seed").checked);
    };
    form.addEventListener("change", syncForm);
    syncForm();
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const errEl = $("#nc-err");
      const fail = (m, el) => { errEl.innerHTML = `<div class="alert alert-error">${icon("alert")}<div>${esc(m)}</div></div>`; el?.focus(); };
      errEl.innerHTML = "";
      const name = $("#nc-name").value.trim();
      const eval_type = $("input[name=nc-type]:checked", form).value;
      const seed = $("#nc-seed").checked;
      if (!name) return fail("Müsabiqənin adını daxil edin.", $("#nc-name"));
      let custom_max = null;
      if (eval_type === "custom") {
        const raw = $("#nc-max").value.trim();
        if (!/^\d+$/.test(raw) || +raw < 2 || +raw > 100) return fail("Maksimum bal 2 ilə 100 arasında tam ədəd olmalıdır.", $("#nc-max"));
        custom_max = +raw;
      }
      let team_count = 0;
      if (seed) {
        const raw = $("#nc-count").value.trim();
        if (!/^\d+$/.test(raw) || +raw > 100) return fail("Komanda sayı 0 ilə 100 arasında tam ədəd olmalıdır.", $("#nc-count"));
        team_count = +raw;
      }
      const btn = $("button[type=submit]", form);
      setBusy(btn, true, "Yaradılır…");
      try {
        const r = await api("POST", "/api/admin/contests", { name, eval_type, custom_max, seed_defaults: seed, team_count });
        AdminApp.select(r.contest.id);
        toast(`«${name}» yaradıldı və seçildi.`);
        location.hash = "#/icmal";
      } catch (er) { setBusy(btn, false); fail(er.message); }
    });
    }

    main.onclick = async (e) => {
      const pick = e.target.closest("[data-pick]"), tog = e.target.closest("[data-toggle-open]"), del = e.target.closest("[data-del-contest]");
      if (pick) {
        AdminApp.select(+pick.dataset.pick);
        toast(`Seçildi: «${AdminApp.current().name}».`, "info");
        location.hash = "#/icmal";
      } else if (tog) {
        AdminApp.toggleOpen(+tog.dataset.toggleOpen);
      } else if (del) {
        const c = AdminApp.contests.find((x) => x.id === +del.dataset.delContest);
        const ok = await modal({
          title: "Müsabiqə həmişəlik silinsin?",
          body: `
            <p><strong>${esc(c.name)}</strong> müsabiqəsi bütün məlumatları ilə birlikdə silinəcək:</p>
            <div class="kv">
              <div>Komandalar</div><div class="v">${c.progress.teams}</div>
              <div>Meyarlar</div><div class="v">${c.criteria_count}</div>
              <div>Jüri hesabları</div><div class="v">${c.progress.juries}</div>
              <div>Təsdiqlənmiş qiymətləndirmələr</div><div class="v">${c.progress.completed}</div>
            </div>
            <div class="alert alert-error">${icon("alert")}<div>Bu əməliyyat geri qaytarılmır. Nəticələri saxlamaq istəyirsinizsə, əvvəlcə <a href="/api/admin/contests/${c.id}/results.csv" download>CSV faylını yükləyin</a>.</div></div>
            <div class="field"><label for="del-name">Təsdiq üçün müsabiqənin adını yazın: <strong>${esc(c.name)}</strong></label>
              <input class="input" id="del-name" autocomplete="off" spellcheck="false"></div>`,
          confirmText: "Həmişəlik sil", danger: true,
          onOpen: (dl) => {
            const ok = $("[data-ok]", dl), inp = $("#del-name", dl);
            ok.disabled = true;
            inp.addEventListener("input", () => { ok.disabled = inp.value.trim() !== c.name; });
            inp.focus();
          },
          onConfirm: (dl) => api("POST", `/api/admin/contests/${c.id}/delete`, { confirm_name: $("#del-name", dl).value.trim() }),
        });
        if (ok) {
          if (c.id === CUR) { CUR = null; store.del("qp_cur_contest"); }
          toast(`«${c.name}» silindi.`);
          AdminApp.route();
        }
      }
    };
  },

  // ------------------------------------------------------------ İcmal
  async icmal(main) {
    const d = await api("GET", `${ADM()}/overview`);
    const p = d.progress, c = d.contest;
    main.innerHTML = `
      ${pageHead("İcmal", esc(c.name))}
      <div class="stack">
        <div class="grid-stats">
          <div class="card stat enter"><div class="stat-label">Komandalar</div><div class="stat-value">${p.teams}</div></div>
          <div class="card stat enter"><div class="stat-label">Jürilər</div><div class="stat-value">${p.juries}</div></div>
          <div class="card stat enter"><div class="stat-label">Meyarlar</div><div class="stat-value">${d.criteria_count}</div></div>
          <div class="card stat enter"><div class="stat-label">Qiymətləndirmə tipi</div><div class="stat-value sm">${esc(c.type_label)}<br><span class="muted small">Bal aralığı: ${esc(c.range_label)}, ${c.repeats_allowed ? "təkrara icazə verilir" : "təkrarsız"}</span></div></div>
        </div>
        <div class="card enter stack">
          <div class="row"><h2>Ümumi irəliləyiş</h2><div class="spacer"></div>${statusChip(p.final)}</div>
          <div class="row"><span class="num" style="font-size:1.5rem;font-weight:700;color:var(--navy)">${p.percent}%</span>
            <span class="muted">${p.completed} / ${p.expected} təsdiqlənmiş qiymətləndirmə</span></div>
          <div class="progress" id="ov-progress" role="progressbar" aria-label="Ümumi irəliləyiş" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${p.percent}"><span></span></div>
          <p class="hint">Gözlənilən qiymətləndirmə sayı: komanda sayı × jüri sayı = ${p.teams} × ${p.juries} = ${p.expected}. Bir jürinin bir komandanı bütün meyarlar üzrə təsdiqləməsi bir qiymətləndirmə sayılır.</p>
          ${p.juries === 0 ? `<div class="alert alert-warn">${icon("alert")}<div>Jüri hesabı yoxdur. Nəticələr yekun hesab edilmir.${can("juries") ? ' <a href="#/juriler">Jüri əlavə edin</a>.' : ""}</div></div>` : ""}
        </div>
        <div class="card enter stack">
          <h2>Jürilər üzrə irəliləyiş</h2>
          ${d.juries.length ? `<div class="stack-sm">${d.juries.map((j, i) => `
            <div class="stack-sm" style="gap:6px">
              <div class="row" style="gap:8px"><strong>${esc(j.username)}</strong><div class="spacer"></div>
              ${j.completed >= j.total && j.total > 0 ? `<span class="chip chip-ok">${icon("check")} Tamamlanıb</span>` : ""}
              <span class="muted num small">${j.completed} / ${j.total} komanda</span></div>
              <div class="progress sm" data-jp="${i}" role="progressbar" aria-label="${esc(j.username)} irəliləyişi" aria-valuemin="0" aria-valuemax="${j.total}" aria-valuenow="${j.completed}"><span></span></div>
            </div>`).join("")}</div>` : `<p class="muted">Hələ jüri hesabı yaradılmayıb.</p>`}
        </div>
      </div>`;
    setProgress($("#ov-progress"), p.percent);
    d.juries.forEach((j, i) => setProgress($(`[data-jp="${i}"]`), j.total ? (j.completed * 100) / j.total : 0));
  },

  // ------------------------------------------------------------ Ayarlar
  async ayarlar(main) {
    const d = await api("GET", `${ADM()}/contest`);
    const c = d.contest;
    const locked = c.structure_locked;
    main.innerHTML = `
      ${pageHead("Müsabiqə ayarları")}
      <form class="card stack enter" id="settings-form" novalidate>
        <div class="field">
          <label for="c-name">Müsabiqənin adı</label>
          <input class="input" id="c-name" maxlength="200" value="${esc(c.name)}" required>
        </div>
        <fieldset class="stack-sm" style="border:0;padding:0;margin:0">
          <legend class="label" style="margin-bottom:8px">Qiymətləndirmə tipi</legend>
          ${locked ? `<div class="alert alert-info" style="margin-bottom:8px">${icon("lock")}<div>Qiymətləndirmə tipi və şkala həddi ilk qiymətləndirmə təsdiqləndiyi üçün (${esc(fmtTime(c.locked_at))}) kilidlənib. Bu, artıq verilmiş balların eyni qaydalarla müqayisəsini qoruyur.</div></div>` : ""}
          <div class="type-options">
            ${["unique", "scale5", "custom"].map((t) => `
              <label class="type-opt">
                <input type="radio" name="etype" value="${t}" ${c.eval_type === t ? "checked" : ""} ${locked ? "disabled" : ""}>
                <span class="box"><span class="t"><span class="dot"></span>${esc(TYPE_HELP[t].label)}</span><span class="d">${esc(TYPE_HELP[t].short)}</span></span>
              </label>`).join("")}
          </div>
        </fieldset>
        <div class="field ${c.eval_type === "custom" ? "" : "hidden"}" id="max-field" style="max-width:260px">
          <label for="c-max">Maksimum bal</label>
          <input class="input" id="c-max" type="number" inputmode="numeric" min="2" max="100" step="1" value="${c.custom_max ?? 10}" ${locked ? "disabled" : ""} aria-describedby="c-max-hint">
          <span class="hint" id="c-max-hint">2 ilə 100 arasında tam ədəd.</span>
          <span class="field-error hidden" id="c-max-err" role="alert"></span>
        </div>
        <div class="alert alert-info" id="type-help"></div>
        <div class="row"><button class="btn btn-primary" type="submit">Yadda saxla</button></div>
      </form>`;
    const form = $("#settings-form");
    const help = () => {
      const t = $("input[name=etype]:checked", form).value;
      const h = TYPE_HELP[t];
      const box = $("#type-help");
      box.innerHTML = `${icon("info")}<div class="stack-sm" style="gap:4px"><div>${esc(h.text(d.teams))}</div><div class="muted small">${esc(h.example)}</div></div>`;
      box.classList.remove("reveal"); void box.offsetWidth; box.classList.add("reveal");
      const mf = $("#max-field");
      const was = mf.classList.contains("hidden");
      mf.classList.toggle("hidden", t !== "custom");
      if (t === "custom" && was) mf.classList.add("reveal");
    };
    $$("input[name=etype]", form).forEach((r) => r.addEventListener("change", help));
    help();
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const name = $("#c-name").value.trim();
      const eval_type = $("input[name=etype]:checked", form).value;
      let custom_max = null;
      const err = $("#c-max-err");
      err.classList.add("hidden");
      $("#c-max").removeAttribute("aria-invalid");
      if (!name) { toast("Müsabiqənin adı boş ola bilməz.", "error"); $("#c-name").focus(); return; }
      if (eval_type === "custom") {
        const raw = $("#c-max").value.trim();
        if (!/^\d+$/.test(raw) || +raw < 2 || +raw > 100) {
          err.innerHTML = `${icon("alert", "sm")} Maksimum bal 2 ilə 100 arasında tam ədəd olmalıdır.`;
          err.classList.remove("hidden");
          $("#c-max").setAttribute("aria-invalid", "true");
          $("#c-max").focus();
          return;
        }
        custom_max = +raw;
      }
      const btn = $("button[type=submit]", form);
      setBusy(btn, true, "Yadda saxlanılır…");
      try {
        await api("PUT", `${ADM()}/contest`, { name, eval_type, custom_max, version: c.version });
        toast("Ayarlar yadda saxlanıldı.");
        AdminApp.refresh();
      } catch (er) {
        setBusy(btn, false);
        toast(er.message, "error");
      }
    });
  },

  // ------------------------------------------------------------ Komandalar / Meyarlar
  komandalar(main) { return entityView(main, { path: "teams", title: "Komandalar", one: "Komanda", gen: "komanda", placeholder: "Komandanın adı" }); },
  meyarlar(main) { return entityView(main, { path: "criteria", title: "Meyarlar", one: "Meyar", gen: "meyar", placeholder: "Meyarın adı" }); },

  // ------------------------------------------------------------ Jürilər
  async juriler(main) {
    const d = await api("GET", `${ADM()}/juries`);
    const p = d.progress;
    main.innerHTML = `
      ${pageHead("Jürilər", `Gözlənilən qiymətləndirmə sayı: ${p.teams} komanda × ${p.juries} jüri = <strong class="num">${p.expected}</strong>`)}
      <div class="stack">
        <form class="card stack enter" id="jury-form" novalidate>
          <h2>Yeni jüri hesabı</h2>
          <div class="form-row">
            <div class="field"><label for="j-user">İstifadəçi adı</label>
              <input class="input" id="j-user" autocomplete="off" autocapitalize="none" spellcheck="false" maxlength="50" required aria-describedby="j-user-hint">
              <span class="hint" id="j-user-hint">3–50 simvol: hərf, rəqəm, nöqtə, defis, alt xətt.</span></div>
            ${pwField("j-pass", "Parol", { hint: "Ən azı 8 simvol." })}
          </div>
          <div id="jury-form-err" role="alert"></div>
          <div class="row"><button class="btn btn-primary" type="submit">${icon("plus")} Hesab yarat</button></div>
        </form>
        ${d.items.length ? `
        <div class="table-wrap enter">
          <table>
            <thead><tr><th scope="col">İstifadəçi adı</th><th scope="col">İrəliləyiş</th><th scope="col" class="num">Əməliyyatlar</th></tr></thead>
            <tbody>${d.items.map((j, i) => `
              <tr>
                <td><strong>${esc(j.username)}</strong></td>
                <td style="min-width:180px"><div class="stack-sm" style="gap:4px"><span class="small muted num">${j.completed} / ${j.total} komanda</span>
                  <div class="progress sm" data-jp="${i}" role="progressbar" aria-label="${esc(j.username)} irəliləyişi" aria-valuemin="0" aria-valuemax="${j.total}" aria-valuenow="${j.completed}"><span></span></div></div></td>
                <td class="num"><div class="row" style="justify-content:flex-end;gap:4px;flex-wrap:nowrap">
                  <button class="btn btn-ghost btn-sm" data-rename="${j.id}">${icon("edit", "sm")} Adı dəyiş</button>
                  <button class="btn btn-ghost btn-sm" data-pass="${j.id}">${icon("key", "sm")} Yeni parol</button>
                  ${j.completed > 0 && !isAdmin() ? "" : `<button class="btn btn-danger-ghost btn-sm btn-icon" data-del="${j.id}" aria-label="${esc(j.username)} hesabını sil">${icon("trash", "sm")}</button>`}
                </div></td>
              </tr>`).join("")}</tbody>
          </table>
        </div>` : `<div class="card empty">${icon("users")}<p>Hələ jüri hesabı yoxdur. Yuxarıdakı formadan ilk hesabı yaradın.</p></div>`}
      </div>`;
    d.items.forEach((j, i) => setProgress($(`[data-jp="${i}"]`), j.total ? (j.completed * 100) / j.total : 0));
    const byId = Object.fromEntries(d.items.map((j) => [j.id, j]));
    $("#jury-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const username = $("#j-user").value.trim(), password = $("#j-pass").value;
      const errEl = $("#jury-form-err");
      errEl.innerHTML = "";
      const fail = (m, el) => { errEl.innerHTML = `<div class="alert alert-error">${icon("alert")}<div>${esc(m)}</div></div>`; if (el) { el.setAttribute("aria-invalid", "true"); el.focus(); } };
      $("#j-user").removeAttribute("aria-invalid"); $("#j-pass").removeAttribute("aria-invalid");
      if (!/^[\p{L}\p{N}_.\-]{3,50}$/u.test(username)) return fail("İstifadəçi adı 3–50 simvol olmalı, yalnız hərf, rəqəm, nöqtə, defis və alt xətt içərməlidir.", $("#j-user"));
      if (password.length < 8) return fail("Parol ən azı 8 simvoldan ibarət olmalıdır.", $("#j-pass"));
      const btn = $("button[type=submit]", e.target);
      setBusy(btn, true, "Yaradılır…");
      try {
        await api("POST", `${ADM()}/juries`, { username, password });
        toast(`«${username}» jüri hesabı yaradıldı.`);
        AdminApp.refresh();
      } catch (er) { setBusy(btn, false); fail(er.message); }
    });
    main.onclick = async (e) => {
      const r = e.target.closest("[data-rename]"), pw = e.target.closest("[data-pass]"), del = e.target.closest("[data-del]");
      if (r) {
        const j = byId[r.dataset.rename];
        const ok = await modal({
          title: "İstifadəçi adını dəyiş",
          body: `<div class="field"><label for="m-user">Yeni istifadəçi adı</label><input class="input" id="m-user" maxlength="50" value="${esc(j.username)}" autocapitalize="none" spellcheck="false"></div>`,
          confirmText: "Yadda saxla",
          onOpen: (dl) => $("#m-user", dl).select(),
          onConfirm: (dl) => api("PATCH", `${ADM()}/juries/${j.id}`, { username: $("#m-user", dl).value.trim(), version: j.version }),
        });
        if (ok) { toast("İstifadəçi adı dəyişdirildi."); AdminApp.refresh(); }
      } else if (pw) {
        const j = byId[pw.dataset.pass];
        const ok = await modal({
          title: `Yeni parol: ${j.username}`,
          body: `${pwField("m-pass", "Yeni parol", { hint: "Ən azı 8 simvol. Jürinin aktiv sessiyaları bağlanacaq." })}`,
          confirmText: "Parolu təyin et",
          onOpen: (dl) => $("#m-pass", dl).focus(),
          onConfirm: (dl) => {
            const v = $("#m-pass", dl).value;
            if (v.length < 8) throw new Error("Parol ən azı 8 simvoldan ibarət olmalıdır.");
            return api("POST", `${ADM()}/juries/${j.id}/password`, { password: v });
          },
        });
        if (ok) toast("Yeni parol təyin edildi.");
      } else if (del) {
        const j = byId[del.dataset.del];
        const hasScores = j.completed > 0;
        const ok = await modal({
          title: "Jüri hesabını sil",
          body: hasScores ? `
            <p><strong>${esc(j.username)}</strong> hesabı silinəcək.</p>
            <div class="alert alert-error">${icon("alert")}<div>Bu jürinin <strong>${j.completed}</strong> komanda üzrə təsdiqlənmiş balları da silinəcək və nəticələrdən çıxarılacaq. Bu əməliyyat geri qaytarılmır. Silinən ballar tarixçədə saxlanılır.</div></div>
            <div class="field"><label for="del-jury">Təsdiq üçün istifadəçi adını yazın: <strong>${esc(j.username)}</strong></label>
              <input class="input" id="del-jury" autocomplete="off" autocapitalize="none" spellcheck="false"></div>`
            : `<p><strong>${esc(j.username)}</strong> hesabı silinəcək. Bu jürinin təsdiqlənmiş balı yoxdur.</p>`,
          confirmText: hasScores ? "Ballarla birlikdə sil" : "Sil", danger: true,
          onOpen: (dl) => {
            if (!hasScores) return;
            const okb = $("[data-ok]", dl), inp = $("#del-jury", dl);
            okb.disabled = true;
            inp.addEventListener("input", () => { okb.disabled = inp.value.trim() !== j.username; });
            inp.focus();
          },
          onConfirm: () => api("DELETE", `${ADM()}/juries/${j.id}${hasScores ? "?with_scores=true" : ""}`),
        });
        if (ok) { toast(hasScores ? "Jüri hesabı balları ilə birlikdə silindi." : "Jüri hesabı silindi."); AdminApp.refresh(); }
      }
    };
  },

  // ------------------------------------------------------------ Qiymətləndirmələr
  async qiymetlendirmeler(main) {
    const list = await api("GET", `${ADM()}/juries`);
    if (!list.items.length) {
      main.innerHTML = `${pageHead("Qiymətləndirmələr")}<div class="card empty">${icon("clipboard")}<p>Jüri hesabı yoxdur. <a href="#/juriler">Jüri əlavə edin</a>.</p></div>`;
      return;
    }
    const saved = store.get("qp_admin_jury");
    const jid = list.items.some((j) => j.id === saved) ? saved : list.items[0].id;
    main.innerHTML = `
      ${pageHead("Qiymətləndirmələr", "Jüri seçin: həmin jürinin bütün komandalara verdiyi ballar göstərilir.")}
      <div class="stack">
        <div class="field" style="max-width:360px"><label for="ev-jury">Jüri</label>
          <select class="input" id="ev-jury">${list.items.map((j) => `<option value="${j.id}" ${j.id === jid ? "selected" : ""}>${esc(j.username)} (${j.completed}/${j.total})</option>`).join("")}</select></div>
        <div id="ev-body">${loadingBox()}</div>
      </div>`;
    const sel = $("#ev-jury");
    sel.addEventListener("change", () => { store.set("qp_admin_jury", +sel.value); loadJuryEvals(+sel.value); });
    await loadJuryEvals(jid);
  },

  // ------------------------------------------------------------ Nəticələr
  async neticeler(main) {
    const r = await api("GET", `${ADM()}/results`);
    const c = r.contest, p = r.progress;
    main.innerHTML = `
      ${pageHead(p.status_label, esc(c.name), `<a class="btn btn-secondary" href="${ADM()}/results.csv" download>${icon("download")} CSV yüklə</a>`)}
      <div class="stack">
        <div class="card enter row" style="gap:16px 28px">
          <div>${statusChip(p.final)}</div>
          <div><div class="muted small">Qiymətləndirmə tipi</div><strong>${esc(c.type_label)}</strong></div>
          <div><div class="muted small">Bal aralığı</div><strong class="num">${esc(c.range_label)}</strong> <span class="muted small">${c.repeats_allowed ? "(təkrara icazə verilir)" : "(təkrarsız)"}</span></div>
          <div><div class="muted small">Tamamlanma</div><strong class="num">${p.completed} / ${p.expected}</strong> <span class="muted small num">(${p.percent}%)</span></div>
        </div>
        ${p.juries === 0 ? `<div class="alert alert-warn">${icon("alert")}<div>Jüri hesabı yoxdur, ona görə nəticələr yekun hesab edilmir.</div></div>` : ""}
        ${!p.final && p.juries > 0 ? `<div class="alert alert-info">${icon("info")}<div>Bütün qiymətləndirmələr tamamlanmayıb. Cədvəl hazırda təsdiqlənmiş balları göstərir.</div></div>` : ""}
        <div class="table-wrap enter">
          <table>
            <caption class="sr-only">${esc(p.status_label)}: komandalar ümumi bala görə</caption>
            <thead><tr>
              <th scope="col">Yer</th><th scope="col" class="sticky-col">Komanda</th>
              ${r.criteria.map((x) => `<th scope="col" class="num">${esc(x.name)}</th>`).join("")}
              <th scope="col" class="num">Jüri sayı</th><th scope="col" class="num">Ümumi bal</th>
            </tr></thead>
            <tbody>${r.rows.map((row) => `
              <tr>
                <td>${row.rank ? `<span class="rank ${row.rank <= 3 ? `r${row.rank}` : ""}">${row.rank}</span>` : `<span class="rank" aria-label="Qiymətləndirilməyib">—</span>`}</td>
                <th scope="row" class="sticky-col" style="position:sticky;background:#fff;font-weight:600;color:var(--text)">${esc(row.team)}</th>
                ${row.criteria.map((v) => `<td class="num">${v}</td>`).join("")}
                <td class="num">${row.juries}</td>
                <td class="num total-col">${row.total}</td>
              </tr>`).join("")}</tbody>
          </table>
        </div>
        <p class="hint">Ümumi bal — bütün jürilərin bütün meyarlar üzrə komandaya verdiyi təsdiqlənmiş balların cəmidir. Bərabər bal toplayan komandalar eyni yeri paylaşır.</p>
      </div>`;
  },

  // ------------------------------------------------------------ Tarixçə
  async tarixce(main) {
    let offset = 0;
    let onlyAdmin = !!store.get("qp_audit_admin");
    main.innerHTML = `
      ${pageHead("Tarixçə", "Bütün vaxtlar Bakı vaxtı ilə göstərilir.")}
      <div class="stack">
        <label class="row" style="gap:8px;min-height:44px;cursor:pointer"><input type="checkbox" id="only-admin" ${onlyAdmin ? "checked" : ""} style="width:20px;height:20px"> Yalnız admin və operator əməliyyatları</label>
        <div class="card" style="padding:0" id="audit-list">${loadingBox()}</div>
        <div><button class="btn btn-secondary hidden" id="audit-more">Daha çox göstər</button></div>
      </div>`;
    const listEl = $("#audit-list"), more = $("#audit-more");
    const load = async (reset) => {
      if (reset) { offset = 0; listEl.innerHTML = loadingBox(); }
      setBusy(more, true, "Yüklənir…");
      try {
        const d = await api("GET", `${ADM()}/audit?offset=${offset}&limit=50&only_admin=${onlyAdmin}`);
        if (reset) listEl.innerHTML = "";
        if (!d.items.length && offset === 0) listEl.innerHTML = `<div class="empty">${icon("history")}<p>Hələ heç bir qeyd yoxdur.</p></div>`;
        listEl.insertAdjacentHTML("beforeend", d.items.map(auditItem).join(""));
        offset += d.items.length;
        setBusy(more, false);
        more.classList.toggle("hidden", offset >= d.total);
      } catch (err) {
        setBusy(more, false);
        if (reset) listEl.innerHTML = errorBox(err.message, false); else toast(err.message, "error");
      }
    };
    $("#only-admin").addEventListener("change", (e) => { onlyAdmin = e.target.checked; store.set("qp_audit_admin", onlyAdmin); load(true); });
    more.addEventListener("click", () => load(false));
    await load(true);
  },

  // ------------------------------------------------------------ Operatorlar
  async operatorlar(main) {
    const d = await api("GET", "/api/admin/operators");
    const P = d.permissions;
    const permBoxes = (prefix, selected = []) => `
      <fieldset class="perm-grid">
        <legend class="label">İcazələr</legend>
        ${P.map((p) => `<label class="perm-opt"><input type="checkbox" name="${prefix}-perm" value="${p.key}" ${selected.includes(p.key) ? "checked" : ""}><span>${esc(p.label)}</span></label>`).join("")}
      </fieldset>`;
    const chips = (perms) => perms.length
      ? perms.map((k) => `<span class="chip chip-info">${icon("check")} ${esc(P.find((p) => p.key === k)?.label || k)}</span>`).join(" ")
      : `<span class="chip chip-muted">İcazə verilməyib</span>`;
    main.innerHTML = `
      ${pageHead("Operatorlar", "Operator yalnız sizin verdiyiniz icazələr daxilində işləyir. Müsabiqəni silmək, qiymətləndirməni açıb-bağlamaq, balları redaktə etmək, nəticələr və tarixçə yalnız adminə məxsusdur.")}
      <div class="stack">
        <form class="card stack enter" id="op-form" novalidate>
          <h2>Yeni operator</h2>
          <div class="form-row">
            <div class="field"><label for="op-user">İstifadəçi adı</label>
              <input class="input" id="op-user" autocomplete="off" autocapitalize="none" spellcheck="false" maxlength="50"></div>
            ${pwField("op-pass", "Parol", { hint: "Ən azı 8 simvol." })}
          </div>
          ${permBoxes("new", ["contests", "juries", "teams", "criteria"])}
          <div id="op-err" role="alert"></div>
          <div><button class="btn btn-primary" type="submit">${icon("plus")} Operator yarat</button></div>
        </form>
        ${d.items.length ? `<div class="contest-list">${d.items.map((o) => `
          <article class="card contest-item enter">
            <div class="row" style="gap:8px"><span class="brand-mark" style="width:34px;height:34px;border-radius:9px">${icon("shield")}</span>
              <h3 style="flex:1;min-width:0;overflow-wrap:anywhere">${esc(o.username)}</h3></div>
            <div class="row" style="gap:6px">${chips(o.permissions)}</div>
            <div class="row" style="gap:6px">
              <button class="btn btn-secondary btn-sm" data-op-edit="${o.id}">${icon("edit", "sm")} İcazələr və ad</button>
              <button class="btn btn-ghost btn-sm" data-op-pass="${o.id}">${icon("key", "sm")} Yeni parol</button>
              <div class="spacer"></div>
              <button class="btn btn-danger-ghost btn-sm btn-icon" data-op-del="${o.id}" aria-label="${esc(o.username)} operatorunu sil">${icon("trash", "sm")}</button>
            </div>
          </article>`).join("")}</div>` : `<div class="card empty">${icon("shield")}<p>Hələ operator yoxdur.</p></div>`}
      </div>`;
    const byId = Object.fromEntries(d.items.map((o) => [o.id, o]));
    const checked = (root, prefix) => $$(`input[name=${prefix}-perm]:checked`, root).map((i) => i.value);
    $("#op-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const errEl = $("#op-err");
      const fail = (m, el) => { errEl.innerHTML = `<div class="alert alert-error">${icon("alert")}<div>${esc(m)}</div></div>`; el?.focus(); };
      errEl.innerHTML = "";
      const username = $("#op-user").value.trim(), password = $("#op-pass").value;
      if (!/^[\p{L}\p{N}_.\-]{3,50}$/u.test(username)) return fail("İstifadəçi adı 3–50 simvol olmalı, yalnız hərf, rəqəm, nöqtə, defis və alt xətt içərməlidir.", $("#op-user"));
      if (password.length < 8) return fail("Parol ən azı 8 simvoldan ibarət olmalıdır.", $("#op-pass"));
      const btn = $("button[type=submit]", e.target);
      setBusy(btn, true, "Yaradılır…");
      try {
        await api("POST", "/api/admin/operators", { username, password, permissions: checked(e.target, "new") });
        toast(`«${username}» operatoru yaradıldı.`);
        AdminApp.refresh();
      } catch (er) { setBusy(btn, false); fail(er.message); }
    });
    main.onclick = async (e) => {
      const ed = e.target.closest("[data-op-edit]"), pw = e.target.closest("[data-op-pass]"), del = e.target.closest("[data-op-del]");
      if (ed) {
        const o = byId[ed.dataset.opEdit];
        const ok = await modal({
          title: `Operator: ${o.username}`,
          body: `<div class="field"><label for="m-op-user">İstifadəçi adı</label><input class="input" id="m-op-user" maxlength="50" value="${esc(o.username)}" autocapitalize="none" spellcheck="false"></div>
                 ${permBoxes("edit", o.permissions)}
                 <p class="hint">Dəyişiklik dərhal qüvvəyə minir, operatorun yenidən daxil olmasına ehtiyac yoxdur.</p>`,
          confirmText: "Yadda saxla",
          onConfirm: (dl) => api("PATCH", `/api/admin/operators/${o.id}`, { username: $("#m-op-user", dl).value.trim(), permissions: checked(dl, "edit"), version: o.version }),
        });
        if (ok) { toast("Operator yeniləndi."); AdminApp.refresh(); }
      } else if (pw) {
        const o = byId[pw.dataset.opPass];
        const ok = await modal({
          title: `Yeni parol: ${o.username}`,
          body: pwField("m-op-pass", "Yeni parol", { hint: "Ən azı 8 simvol. Operatorun aktiv sessiyaları bağlanacaq." }),
          confirmText: "Parolu təyin et",
          onOpen: (dl) => $("#m-op-pass", dl).focus(),
          onConfirm: (dl) => {
            const v = $("#m-op-pass", dl).value;
            if (v.length < 8) throw new Error("Parol ən azı 8 simvoldan ibarət olmalıdır.");
            return api("POST", `/api/admin/operators/${o.id}/password`, { password: v });
          },
        });
        if (ok) toast("Yeni parol təyin edildi.");
      } else if (del) {
        const o = byId[del.dataset.opDel];
        const ok = await modal({
          title: "Operator silinsin?",
          body: `<p><strong>${esc(o.username)}</strong> hesabı silinəcək və onun aktiv sessiyaları bağlanacaq. Operatorun yaratdığı müsabiqələr, komandalar və jürilər qalır.</p>`,
          confirmText: "Sil", danger: true,
          onConfirm: () => api("DELETE", `/api/admin/operators/${o.id}`),
        });
        if (ok) { toast("Operator silindi."); AdminApp.refresh(); }
      }
    };
  },

  // ------------------------------------------------------------ Hesab
  hesab(main) {
    main.innerHTML = `
      ${pageHead("Parolu dəyiş")}
      <form class="card stack enter" id="pw-form" style="max-width:480px" novalidate>
        ${pwField("cur-pass", "Cari parol", { autocomplete: "current-password" })}
        ${pwField("new-pass", "Yeni parol", { hint: "Ən azı 8 simvol." })}
        ${pwField("new-pass2", "Yeni parolu təkrarlayın")}
        <div id="pw-err" role="alert"></div>
        <div><button class="btn btn-primary" type="submit">Parolu dəyiş</button></div>
      </form>`;
    $("#pw-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const cur = $("#cur-pass").value, n1 = $("#new-pass").value, n2 = $("#new-pass2").value;
      const errEl = $("#pw-err");
      const fail = (m) => { errEl.innerHTML = `<div class="alert alert-error">${icon("alert")}<div>${esc(m)}</div></div>`; };
      errEl.innerHTML = "";
      if (n1.length < 8) return fail("Yeni parol ən azı 8 simvoldan ibarət olmalıdır.");
      if (n1 !== n2) return fail("Yeni parollar uyğun gəlmir.");
      const btn = $("button[type=submit]", e.target);
      setBusy(btn, true);
      try {
        await api("POST", "/api/auth/password", { current_password: cur, new_password: n1 });
        toast("Parol dəyişdirildi.");
        e.target.reset();
        setBusy(btn, false);
      } catch (er) { setBusy(btn, false); fail(er.message); }
    });
  },
};

function auditItem(a) {
  let details = "";
  const dd = a.details || {};
  if (a.action === "scores_edit" && dd.items) {
    details = `<details><summary>Dəyişiklikləri göstər</summary>
      <table><thead><tr><th>Komanda</th><th>Meyar</th><th class="num">Əvvəl</th><th class="num">Sonra</th></tr></thead><tbody>
      ${dd.items.flatMap((it) => it.changes.map((ch) => `<tr><td>${esc(it.team)}</td><td>${esc(ch.criterion)}</td>
        <td class="num"><span class="diff-old">${esc(ch.old)}</span></td><td class="num"><span class="diff-new">${esc(ch.new)}</span></td></tr>`)).join("")}
      </tbody></table></details>`;
  } else if ((a.action === "evaluation_unlock" && dd.deleted_scores) || (a.action === "evaluation_confirm" && dd.scores)) {
    const sc = dd.deleted_scores || dd.scores;
    details = `<details><summary>${a.action === "evaluation_unlock" ? "Silinmiş ballar" : "Ballar"}</summary>
      <table><tbody>${Object.entries(sc).map(([k, v]) => `<tr><td>${esc(k)}</td><td class="num"><strong>${esc(v)}</strong></td></tr>`).join("")}</tbody></table></details>`;
  } else if (a.action === "jury_delete" && dd.deleted) {
    details = `<details><summary>Silinmiş ballar</summary>
      <table><thead><tr><th>Komanda</th><th>Ballar</th></tr></thead><tbody>${Object.entries(dd.deleted).map(([t, sc]) =>
        `<tr><td>${esc(t)}</td><td>${Object.entries(sc).map(([k, v]) => `${esc(k)}: <strong>${esc(v)}</strong>`).join(" · ")}</td></tr>`).join("")}</tbody></table></details>`;
  } else if ((a.action === "contest_update" || a.action === "operator_update") && dd.changes) {
    details = `<details><summary>Dəyişiklikləri göstər</summary>
      <table><tbody>${Object.entries(dd.changes).map(([k, [o, n]]) => `<tr><td>${esc(k)}</td><td><span class="diff-old">${esc(o)}</span> → <span class="diff-new">${esc(n)}</span></td></tr>`).join("")}</tbody></table></details>`;
  }
  return `<div class="audit-item"><time datetime="${esc(a.at)}">${esc(fmtTime(a.at))}</time>
    <div><div>${esc(a.summary)}</div><div class="who">${esc(a.actor)} · ${(ROLE_LABEL[a.role] || a.role).toLowerCase()}</div></div>${details}</div>`;
}

// ------------------------------------------------------------ Komanda/Meyar ümumi görünüşü
async function entityView(main, cfg) {
  const d = await api("GET", `${ADM()}/${cfg.path}`);
  const locked = d.structure_locked;
  const c = d.contest;
  const rangeNote = cfg.path === "teams"
    ? (c.eval_type === "unique" ? `Unikal bal tipində bal aralığı komanda sayına bərabərdir: hazırda <strong class="num">${esc(c.range_label)}</strong>.` : `Cari tipdə (${esc(c.type_label)}) komanda sayı bal aralığına təsir etmir: <strong class="num">${esc(c.range_label)}</strong>.`)
    : "Bütün meyarlar bərabər çəkilidir; nəticə balların birbaşa cəmi ilə hesablanır.";
  main.innerHTML = `
    ${pageHead(cfg.title, `${d.items.length} ${cfg.gen} · ${rangeNote}`)}
    <div class="stack">
      ${lockNotice(c, `${cfg.one} əlavə etmək və silmək bağlıdır.`)}
      <form class="card enter" id="add-form" novalidate>
        <div class="form-row">
          <div class="field"><label for="new-name">Yeni ${cfg.gen}</label>
            <input class="input" id="new-name" maxlength="100" placeholder="${esc(cfg.placeholder)}" ${locked ? "disabled" : ""}></div>
          <button class="btn btn-primary" type="submit" ${locked ? "disabled" : ""}>${icon("plus")} Əlavə et</button>
        </div>
        <div id="add-err" role="alert" style="margin-top:8px"></div>
      </form>
      ${d.items.length ? `<ul class="list card enter" style="padding:0" id="ent-list">
        ${d.items.map((it, i) => `
          <li class="list-item" data-id="${it.id}">
            <span class="idx">${i + 1}.</span>
            <span class="name">${esc(it.name)}</span>
            <div class="list-actions">
              <button class="btn btn-ghost btn-sm" data-edit aria-label="«${esc(it.name)}» adını dəyiş">${icon("edit", "sm")}<span class="hide-sm">Adı dəyiş</span></button>
              <button class="btn btn-danger-ghost btn-sm btn-icon" data-delete ${locked ? 'disabled title="İlk təsdiqdən sonra silmək mümkün deyil"' : ""} aria-label="«${esc(it.name)}» sil">${icon("trash", "sm")}</button>
            </div>
          </li>`).join("")}
      </ul>` : `<div class="card empty">${icon("inbox")}<p>Siyahı boşdur. Yuxarıdakı formadan əlavə edin.</p></div>`}
    </div>`;
  const items = Object.fromEntries(d.items.map((it) => [it.id, it]));
  $("#add-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const inp = $("#new-name"), name = inp.value.trim();
    const errEl = $("#add-err");
    errEl.innerHTML = "";
    if (!name) { errEl.innerHTML = `<span class="field-error">${icon("alert", "sm")} Ad boş ola bilməz.</span>`; inp.focus(); return; }
    const btn = $("button[type=submit]", e.target);
    setBusy(btn, true, "Əlavə edilir…");
    try {
      await api("POST", `${ADM()}/${cfg.path}`, { name });
      toast(`«${name}» əlavə edildi.`);
      AdminApp.refresh();
    } catch (er) { setBusy(btn, false); errEl.innerHTML = `<div class="alert alert-error">${icon("alert")}<div>${esc(er.message)}</div></div>`; }
  });
  $("#ent-list")?.addEventListener("click", async (e) => {
    const li = e.target.closest("li[data-id]");
    if (!li) return;
    const it = items[li.dataset.id];
    if (e.target.closest("[data-edit]")) {
      li.innerHTML = `
        <form class="row" style="flex:1;gap:8px;flex-wrap:nowrap" novalidate>
          <label class="sr-only" for="ed-${it.id}">${cfg.one} adı</label>
          <input class="input" id="ed-${it.id}" maxlength="100" value="${esc(it.name)}" style="flex:1;min-width:0">
          <button class="btn btn-primary btn-sm" type="submit">Saxla</button>
          <button class="btn btn-ghost btn-sm" type="button" data-cancel>Ləğv et</button>
        </form>`;
      const inp = $("input", li);
      inp.focus(); inp.select();
      $("[data-cancel]", li).addEventListener("click", () => AdminApp.refresh());
      inp.addEventListener("keydown", (ev) => { if (ev.key === "Escape") AdminApp.refresh(); });
      $("form", li).addEventListener("submit", async (ev) => {
        ev.preventDefault();
        const btn = $("button[type=submit]", li);
        setBusy(btn, true, "…");
        try {
          await api("PATCH", `${ADM()}/${cfg.path}/${it.id}`, { name: inp.value.trim(), version: it.version });
          toast("Ad dəyişdirildi.");
          AdminApp.refresh();
        } catch (er) { setBusy(btn, false); toast(er.message, "error"); inp.setAttribute("aria-invalid", "true"); }
      });
    } else if (e.target.closest("[data-delete]")) {
      const ok = await modal({
        title: `${cfg.one} silinsin?`,
        body: `<p><strong>${esc(it.name)}</strong> siyahıdan silinəcək.</p>`,
        confirmText: "Sil", danger: true,
        onConfirm: () => api("DELETE", `${ADM()}/${cfg.path}/${it.id}`),
      });
      if (ok) { toast(`«${it.name}» silindi.`); AdminApp.refresh(); }
    }
  });
}

// ------------------------------------------------------------ Admin: jürinin balları
async function loadJuryEvals(jid) {
  const body = $("#ev-body");
  body.innerHTML = loadingBox();
  let d;
  try { d = await api("GET", `${ADM()}/juries/${jid}/evaluations`); } catch (err) {
    body.innerHTML = errorBox(err.message);
    $("[data-retry]", body)?.addEventListener("click", () => loadJuryEvals(jid));
    return;
  }
  const c = d.contest;
  let editing = false;
  const done = d.teams.filter((t) => t.evaluation).length;

  const render = () => {
    body.innerHTML = `
      <div class="stack">
        <div class="row">
          <span class="chip chip-info">${esc(c.summary)}</span>
          <span class="muted small num">${done} / ${d.teams.length} komanda təsdiqlənib</span>
          <div class="spacer"></div>
          ${done ? (editing
            ? `<button class="btn btn-secondary" id="ev-cancel">Ləğv et</button><button class="btn btn-primary" id="ev-save">Dəyişiklikləri yadda saxla</button>`
            : `<button class="btn btn-secondary" id="ev-edit">${icon("edit")} Balları redaktə et</button>`) : ""}
        </div>
        <div id="ev-err" role="alert"></div>
        <div class="table-wrap">
          <table>
            <caption class="sr-only">${esc(d.jury.username)} jürisinin balları</caption>
            <thead><tr><th scope="col" class="sticky-col">Komanda</th>
              ${d.criteria.map((x) => `<th scope="col" class="num">${esc(x.name)}</th>`).join("")}
              <th scope="col">Status</th><th scope="col" class="num">Əməliyyat</th></tr></thead>
            <tbody>${d.teams.map((t) => {
              const e = t.evaluation;
              return `<tr data-team="${t.id}">
                <th scope="row" class="sticky-col" style="position:sticky;background:#fff;font-weight:600;color:var(--text)">${esc(t.name)}</th>
                ${d.criteria.map((cr) => {
                  const v = e ? e.scores[cr.id] : null;
                  if (editing && e) return `<td class="num"><input class="input cell-input num" type="number" inputmode="numeric" min="1" max="${c.max}" step="1" value="${v}" data-eval="${e.id}" data-crit="${cr.id}" aria-label="${esc(t.name)}, ${esc(cr.name)}"></td>`;
                  return `<td class="num">${v ?? '<span class="muted">—</span>'}</td>`;
                }).join("")}
                <td>${e ? `<span class="chip chip-ok" title="${esc(fmtTime(e.confirmed_at))}">${icon("lock")} Təsdiqlənib</span>${e.edited_at ? `<div class="small muted">Redaktə: ${esc(fmtTime(e.edited_at))}</div>` : ""}` : `<span class="chip chip-muted">${icon("clock")} Gözləyir</span>`}</td>
                <td class="num">${e && !editing ? `<button class="btn btn-ghost btn-sm" data-unlock="${t.id}">${icon("unlock", "sm")} Kilidi aç</button>` : ""}</td>
              </tr>`;
            }).join("")}</tbody>
          </table>
        </div>
        ${editing ? `<p class="hint">İcazə verilən aralıq: ${esc(c.range_label)}, ${c.repeats_allowed ? "təkrar ballara icazə verilir" : "eyni meyarda təkrar bal qəbul edilmir"}.</p>` : ""}
      </div>`;
    $("#ev-edit")?.addEventListener("click", () => { editing = true; render(); $("input[data-eval]", body)?.focus(); });
    $("#ev-cancel")?.addEventListener("click", () => { editing = false; render(); });
    $("#ev-save")?.addEventListener("click", save);
    body.oninput = editing ? validate : null;
  };

  const readInputs = () => {
    const vals = {};
    $$("input[data-eval]", body).forEach((inp) => {
      (vals[inp.dataset.eval] ||= {})[inp.dataset.crit] = inp.value.trim();
    });
    return vals;
  };

  function validate() {
    let msg = "";
    const inputs = $$("input[data-eval]", body);
    inputs.forEach((i) => i.removeAttribute("aria-invalid"));
    inputs.forEach((i) => {
      const v = i.value.trim();
      if (!/^\d+$/.test(v) || +v < 1 || +v > c.max) { i.setAttribute("aria-invalid", "true"); msg ||= `Bal 1 ilə ${c.max} arasında tam ədəd olmalıdır.`; }
    });
    if (!c.repeats_allowed) {
      const groups = {};
      inputs.forEach((i) => { (groups[`${i.dataset.crit}:${i.value.trim()}`] ||= []).push(i); });
      Object.values(groups).forEach((g) => { if (g.length > 1) { g.forEach((i) => i.setAttribute("aria-invalid", "true")); msg ||= "Unikal bal tipində eyni meyar üzrə eyni bal iki komandaya verilə bilməz."; } });
    }
    const errEl = $("#ev-err");
    if (errEl) errEl.innerHTML = msg ? `<div class="alert alert-error">${icon("alert")}<div>${esc(msg)}</div></div>` : "";
    return !msg;
  }

  async function save() {
    if (!validate()) return;
    const vals = readInputs();
    const changes = [];
    d.teams.forEach((t) => {
      const e = t.evaluation;
      if (!e || !vals[e.id]) return;
      const nv = vals[e.id];
      const changed = d.criteria.some((cr) => String(e.scores[cr.id]) !== nv[cr.id]);
      if (changed) changes.push({ evaluation_id: e.id, version: e.version, scores: d.criteria.map((cr) => ({ criterion_id: cr.id, value: parseInt(nv[cr.id], 10) })) });
    });
    if (!changes.length) { editing = false; render(); toast("Dəyişiklik yoxdur.", "info"); return; }
    const btn = $("#ev-save");
    setBusy(btn, true, "Yadda saxlanılır…");
    try {
      await api("PUT", `${ADM()}/juries/${jid}/evaluations`, { changes });
      toast(`Ballar yeniləndi (${changes.length} komanda).`);
      loadJuryEvals(jid);
    } catch (err) {
      setBusy(btn, false);
      $("#ev-err").innerHTML = `<div class="alert alert-error">${icon("alert")}<div>${esc(err.message)}</div></div>`;
    }
  }

  body.onclick = async (e) => {
    const b = e.target.closest("[data-unlock]");
    if (!b) return;
    const t = d.teams.find((x) => x.id === +b.dataset.unlock);
    const ev = t.evaluation;
    const ok = await modal({
      title: "Qiymətləndirmənin kilidi açılsın?",
      body: `
        <p><strong>${esc(d.jury.username)}</strong> jürisinin <strong>${esc(t.name)}</strong> komandası üzrə qiymətləndirməsi:</p>
        <div class="kv">${d.criteria.map((cr) => `<div>${esc(cr.name)}</div><div class="v">${ev.scores[cr.id]}</div>`).join("")}</div>
        <div class="alert alert-warn">${icon("alert")}<div>Kilid açıldıqda bu komanda üzrə bütün ballar silinəcək və jüri komandanı yenidən qiymətləndirməli olacaq.${c.eval_type === "unique" ? " Silinən ballar həmin jüri üçün yenidən istifadəyə açılacaq." : ""} Müsabiqənin struktur kilidi qüvvədə qalır.</div></div>`,
      confirmText: "Kilidi aç və balları sil", danger: true,
      onConfirm: () => api("POST", `${ADM()}/evaluations/${ev.id}/unlock`, { version: ev.version }),
    });
    if (ok) { toast(`«${t.name}» üzrə kilid açıldı.`); loadJuryEvals(jid); }
  };
  render();
}

// ================================================================ JÜRİ
const JuryApp = {
  st: null,
  drafts: {},
  filter: "all",
  saving: new Set(),
  draftKey() { return `qp_draft_${ME.id}`; },

  async start() {
    document.title = "Qiymətləndirmə — Qiymətləndirmə portalı";
    if (location.hash) history.replaceState(null, "", location.pathname);
    window.onhashchange = null;
    this.drafts = store.get(this.draftKey()) || {};
    this.filter = store.get("qp_jury_filter") || "all";
    app.innerHTML = `
      <header class="jury-top"><div class="jury-top-inner">
        <div class="brand"><span class="brand-mark">${icon("check")}</span><span class="brand-name">Qiymətləndirmə portalı</span></div>
        <div class="spacer"></div>
        <span class="who">${esc(ME.username)}</span>
        <button class="btn btn-ghost" id="logout-btn">${icon("logout")} Çıxış</button>
      </div></header>
      <main class="jury-main" id="main" tabindex="-1">${loadingBox()}</main>`;
    $("#logout-btn").addEventListener("click", logout);
    await this.load(true);
    if (!this._focusBound) {
      this._focusBound = true;
      document.addEventListener("visibilitychange", () => {
        if (document.visibilityState === "visible" && ME && ME.role === "jury" && !this.saving.size && !openModals.size) this.load(false);
      });
    }
  },

  async load(full) {
    const main = $("#main");
    try {
      this.st = await api("GET", "/api/jury/state");
    } catch (err) {
      if (err.status === 401) return;
      if (full) {
        main.innerHTML = errorBox(err.message);
        $("[data-retry]", main)?.addEventListener("click", () => this.load(true));
      } else toast(err.message, "error");
      return;
    }
    this.cleanDrafts();
    this.render();
  },

  confirmedMap() { return Object.fromEntries(this.st.evaluations.map((e) => [e.team_id, e])); },

  cleanDrafts() {
    const conf = this.confirmedMap();
    const max = this.st.contest.max;
    const teamIds = new Set(this.st.teams.map((t) => String(t.id)));
    const critIds = new Set(this.st.criteria.map((c) => String(c.id)));
    for (const tid of Object.keys(this.drafts)) {
      if (!teamIds.has(tid) || conf[tid]) { delete this.drafts[tid]; continue; }
      for (const cid of Object.keys(this.drafts[tid])) {
        const v = this.drafts[tid][cid];
        if (!critIds.has(cid) || !Number.isInteger(v) || v < 1 || v > max) delete this.drafts[tid][cid];
      }
    }
    this.saveDrafts();
  },
  saveDrafts() { store.set(this.draftKey(), this.drafts); },

  render() {
    const { contest: c, teams, criteria } = this.st;
    const conf = this.confirmedMap();
    const done = teams.filter((t) => conf[t.id]).length;
    const pct = teams.length ? (done * 100) / teams.length : 0;
    const instr = c.eval_type === "unique"
      ? `Hər meyar üzrə 1–${c.max} ballarından istifadə edin. Eyni meyarda bir bal yalnız bir komandaya verilə bilər; istifadə olunmuş ballar deaktiv göstərilir.`
      : `Hər komandaya hər meyar üzrə 1–${c.max} aralığında tam bal verin. Eyni bal bir neçə komandaya verilə bilər.`;
    const main = $("#main");
    main.innerHTML = `
      <div class="stack">
        <div><h1>${esc(c.name)}</h1></div>
        ${c.is_open ? "" : `<div class="alert alert-warn enter" role="status">${icon("stop")}<div><strong>Qiymətləndirmə hazırda bağlıdır.</strong> Admin açdıqdan sonra davam edə bilərsiniz. Təsdiqlənmiş ballarınız saxlanılıb.</div></div>`}
        <div class="jury-summary">
          <div class="card stack-sm enter">
            <div class="row" style="gap:8px"><span class="chip chip-info">${esc(c.type_label)}</span><span class="chip chip-muted num">Bal aralığı: ${esc(c.range_label)}</span></div>
            <p class="small">${esc(instr)} Hər komanda üçün bütün meyarları doldurub «Təsdiqlə» düyməsini basın. Təsdiqdən sonra ballar dəyişdirilə bilməz.</p>
          </div>
          <div class="card stack-sm enter">
            <div class="row"><strong>İrəliləyiş</strong><div class="spacer"></div><span class="num" id="jp-text"><strong>${done}</strong> / ${teams.length} komanda təsdiqlənib</span></div>
            <div class="progress" id="jp-bar" role="progressbar" aria-label="Təsdiqlənmiş komandalar" aria-valuemin="0" aria-valuemax="${teams.length}" aria-valuenow="${done}"><span></span></div>
            ${done === teams.length && teams.length ? `<div class="alert alert-ok" style="margin-top:6px">${icon("checkCircle")}<div>Bütün komandaların qiymətləndirilməsini tamamladınız. Təşəkkür edirik!</div></div>` : ""}
          </div>
        </div>
        ${teams.length && criteria.length ? `
        <div class="row">
          <div class="segmented" role="group" aria-label="Komandaları süz">
            ${[["all", "Hamısı", teams.length], ["pending", "Gözləyən", teams.length - done], ["done", "Təsdiqlənib", done]].map(([k, l, n]) =>
              `<button type="button" data-filter="${k}" aria-pressed="${this.filter === k}">${l} <span class="num">(${n})</span></button>`).join("")}
          </div>
        </div>
        <div class="team-grid" id="team-grid"></div>` : `<div class="card empty">${icon("inbox")}<p>Qiymətləndirmə üçün komanda və ya meyar hələ müəyyən edilməyib.</p></div>`}
      </div>`;
    setProgress($("#jp-bar"), pct);
    $$("[data-filter]", main).forEach((b) => b.addEventListener("click", () => {
      this.filter = b.dataset.filter; store.set("qp_jury_filter", this.filter);
      $$("[data-filter]", main).forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
      this.applyFilter();
    }));
    const grid = $("#team-grid");
    if (!grid) return;
    grid.innerHTML = teams.map((t, i) => this.cardHtml(t, conf[t.id], i)).join("");
    grid.addEventListener("change", (e) => this.onPick(e));
    grid.addEventListener("click", (e) => this.onClick(e));
    this.syncAll();
    this.applyFilter();
  },

  applyFilter() {
    const conf = this.confirmedMap();
    let shown = 0;
    $$(".team-card").forEach((card) => {
      const isDone = !!conf[card.dataset.team];
      const show = this.filter === "all" || (this.filter === "done" ? isDone : !isDone);
      card.classList.toggle("hidden", !show);
      if (show) shown++;
    });
    let empty = $("#filter-empty");
    if (!shown) {
      if (!empty) $("#team-grid").insertAdjacentHTML("afterend", `<div class="card empty" id="filter-empty">${icon("inbox")}<p>Bu filtrdə komanda yoxdur.</p></div>`);
    } else if (empty) empty.remove();
  },

  cardHtml(t, ev, i) {
    const { contest: c, criteria } = this.st;
    const delay = `style="animation-delay:${Math.min(i, 8) * 30}ms"`;
    if (ev) {
      return `
        <article class="card team-card is-done enter" data-team="${t.id}" ${delay} aria-labelledby="tn-${t.id}">
          <div class="team-head"><h3 id="tn-${t.id}">${esc(t.name)}</h3>
            <span class="chip chip-ok">${icon("lock")} Təsdiqlənib</span></div>
          <dl class="locked-scores">${criteria.map((cr) => `<dt>${esc(cr.name)}</dt><dd>${ev.scores[cr.id] ?? "—"}</dd>`).join("")}</dl>
          <p class="small muted">${icon("lock", "sm")} Ballar kilidlənib · ${esc(fmtTime(ev.confirmed_at))}</p>
        </article>`;
    }
    const useSelect = c.max > 10;
    const picker = (cr) => {
      const name = `s-${t.id}-${cr.id}`;
      if (useSelect) {
        return `<select class="input" id="${name}" data-team="${t.id}" data-crit="${cr.id}" aria-describedby="un-${t.id}-${cr.id}">
          <option value="">— Bal seçin —</option>
          ${Array.from({ length: c.max }, (_, k) => `<option value="${k + 1}">${k + 1}</option>`).join("")}
        </select>`;
      }
      return `<fieldset class="scores" aria-describedby="un-${t.id}-${cr.id}"><legend class="sr-only">${esc(cr.name)}</legend>
        ${Array.from({ length: c.max }, (_, k) => k + 1).map((v) => `
          <label class="score"><input type="radio" name="${name}" value="${v}" data-team="${t.id}" data-crit="${cr.id}"><span>${v}</span></label>`).join("")}
      </fieldset>`;
    };
    return `
      <article class="card team-card enter" data-team="${t.id}" ${delay} aria-labelledby="tn-${t.id}">
        <div class="team-head"><h3 id="tn-${t.id}">${esc(t.name)}</h3>
          <span class="chip chip-warn" data-status>${icon("clock")} Gözləyir</span></div>
        ${criteria.map((cr) => `
          <div class="crit">
            <div class="crit-label">${useSelect ? `<label for="s-${t.id}-${cr.id}">${esc(cr.name)}</label>` : `<span>${esc(cr.name)}</span>`}<span class="val" data-val="${cr.id}"></span></div>
            ${picker(cr)}
            <div class="used-note" id="un-${t.id}-${cr.id}" data-note="${cr.id}"></div>
          </div>`).join("")}
        <div class="card-error" role="alert"></div>
        <div class="team-foot">
          <button class="btn btn-primary" data-confirm disabled>${icon("check")} Təsdiqlə</button>
          <button class="btn btn-ghost btn-sm" data-clear>Təmizlə</button>
          <span class="count" data-count></span>
        </div>
      </article>`;
  },

  // Unikal bal tipində istifadə olunmuş ballar
  usage() {
    const conf = {}; const draft = {};
    const names = Object.fromEntries(this.st.teams.map((t) => [t.id, t.name]));
    this.st.evaluations.forEach((e) => {
      for (const [cid, v] of Object.entries(e.scores)) ((conf[cid] ||= {})[v] = names[e.team_id]);
    });
    const confirmed = this.confirmedMap();
    for (const [tid, sc] of Object.entries(this.drafts)) {
      if (confirmed[tid]) continue;
      for (const [cid, v] of Object.entries(sc)) ((draft[cid] ||= {})[v] = tid);
    }
    return { conf, draft };
  },

  syncAll() {
    const unique = this.st.contest.eval_type === "unique";
    const use = unique ? this.usage() : null;
    $$(".team-card:not(.is-done)").forEach((card) => this.syncCard(card, use));
  },

  syncCard(card, use) {
    const tid = card.dataset.team;
    const closed = !this.st.contest.is_open;
    const d = this.drafts[tid] || {};
    const crits = this.st.criteria;
    let filled = 0;
    for (const cr of crits) {
      const v = d[cr.id];
      if (v) filled++;
      const valEl = $(`[data-val="${cr.id}"]`, card);
      valEl.textContent = v ? `${v} bal` : "";
      const note = $(`[data-note="${cr.id}"]`, card);
      const usedConf = use ? use.conf[cr.id] || {} : {};
      const usedDraft = use ? use.draft[cr.id] || {} : {};
      const isUsed = (val) => usedConf[val] !== undefined;
      const isDraftElsewhere = (val) => usedDraft[val] !== undefined && usedDraft[val] !== tid;
      const sel = $(`select[data-crit="${cr.id}"]`, card);
      if (sel) {
        sel.disabled = closed;
        sel.value = v ? String(v) : "";
        $$("option", sel).forEach((o) => {
          if (!o.value) return;
          const n = +o.value;
          const used = isUsed(n), dr = isDraftElsewhere(n);
          o.disabled = closed || used || dr;
          o.textContent = used ? `${n} — istifadə olunub` : dr ? `${n} — başqa kartda seçilib` : String(n);
        });
      } else {
        $$(`input[data-crit="${cr.id}"]`, card).forEach((inp) => {
          const n = +inp.value;
          inp.checked = v === n;
          const used = isUsed(n), dr = isDraftElsewhere(n);
          inp.disabled = closed || used || dr;
          const span = inp.nextElementSibling;
          if (used) span.title = `İstifadə olunub («${usedConf[n]}»)`;
          else if (dr) span.title = "Başqa kartda seçilib (təsdiqlənməyib)";
          else span.removeAttribute("title");
          inp.setAttribute("aria-label", used ? `${n} — istifadə olunub` : dr ? `${n} — başqa kartda seçilib` : `${n} bal`);
        });
      }
      if (use) {
        const u = Object.keys(usedConf).map(Number).sort((a, b) => a - b);
        const dr = Object.entries(usedDraft).filter(([, t]) => t !== tid).map(([val]) => +val).sort((a, b) => a - b);
        const parts = [];
        if (u.length) parts.push(`İstifadə olunub: ${u.join(", ")}`);
        if (dr.length) parts.push(`Başqa kartda seçilib: ${dr.join(", ")}`);
        note.textContent = parts.join(" · ");
      } else note.textContent = "";
    }
    const complete = filled === crits.length;
    const btn = $("[data-confirm]", card);
    if (!this.saving.has(tid)) btn.disabled = !complete || closed;
    btn.setAttribute("aria-disabled", String(!complete || closed));
    $("[data-count]", card).textContent = `${filled} / ${crits.length} meyar seçilib`;
    $("[data-clear]", card).classList.toggle("hidden", filled === 0 || closed);
    const chip = $("[data-status]", card);
    chip.className = `chip ${closed ? "chip-muted" : "chip-warn"}`;
    chip.innerHTML = closed ? `${icon("stop")} Bağlıdır` : `${icon("clock")} Gözləyir`;
    card.classList.toggle("complete", complete);
  },

  onPick(e) {
    const el = e.target;
    if (!el.dataset.crit) return;
    const tid = el.dataset.team, cid = el.dataset.crit;
    if (this.saving.has(tid)) return;
    const v = el.value ? parseInt(el.value, 10) : null;
    const d = (this.drafts[tid] ||= {});
    if (v) d[cid] = v; else delete d[cid];
    this.saveDrafts();
    const card = el.closest(".team-card");
    $(".card-error", card).innerHTML = "";
    if (this.st.contest.eval_type === "unique") this.syncAll();
    else this.syncCard(card, null);
  },

  onClick(e) {
    const card = e.target.closest(".team-card");
    if (!card) return;
    const tid = card.dataset.team;
    if (e.target.closest("[data-clear]")) {
      delete this.drafts[tid];
      this.saveDrafts();
      this.st.contest.eval_type === "unique" ? this.syncAll() : this.syncCard(card, null);
      return;
    }
    if (e.target.closest("[data-confirm]")) this.confirm(card, tid);
  },

  async confirm(card, tid) {
    const team = this.st.teams.find((t) => String(t.id) === tid);
    const d = this.drafts[tid] || {};
    const crits = this.st.criteria;
    if (crits.some((cr) => !d[cr.id])) return;
    const ok = await modal({
      title: "Qiymətləndirməni təsdiqlə",
      body: `
        <p>Komanda: <strong>${esc(team.name)}</strong></p>
        <div class="kv">${crits.map((cr) => `<div>${esc(cr.name)}</div><div class="v">${d[cr.id]}</div>`).join("")}</div>
        <div class="alert alert-warn">${icon("lock")}<div>Təsdiqdən sonra ballar kilidlənəcək və onları dəyişmək mümkün olmayacaq.</div></div>`,
      confirmText: "Təsdiqlə",
      cancelText: "Geri",
      onConfirm: () => true,
    });
    if (!ok) return;
    const btn = $("[data-confirm]", card);
    this.saving.add(tid);
    setBusy(btn, true, "Yadda saxlanılır…");
    $$("input, select", card).forEach((i) => { i.dataset.wasDisabled = i.disabled ? "1" : ""; i.disabled = true; });
    try {
      await api("POST", "/api/jury/evaluations", {
        team_id: team.id,
        scores: crits.map((cr) => ({ criterion_id: cr.id, value: d[cr.id] })),
      });
      this.saving.delete(tid);
      delete this.drafts[tid];
      this.saveDrafts();
      toast(`«${team.name}» təsdiqləndi.`);
      await this.reloadAfterConfirm(tid);
    } catch (err) {
      this.saving.delete(tid);
      setBusy(btn, false);
      $$("input, select", card).forEach((i) => { i.disabled = i.dataset.wasDisabled === "1"; });
      if (err.status === 401) return;
      $(".card-error", card).innerHTML = `<div class="alert alert-error">${icon("alert")}<div>${esc(err.message)} Seçdiyiniz ballar saxlanılıb.</div></div>`;
      // Server vəziyyəti dəyişmiş ola bilər (məs., bal başqa cihazdan istifadə olunub)
      if (err.status === 409) {
        try {
          this.st = await api("GET", "/api/jury/state");
          const msg = $(".card-error", card).innerHTML;
          if (this.confirmedMap()[tid]) { this.cleanDrafts(); this.render(); return; }
          if (!this.st.contest.is_open) { this.render(); toast(err.message, "error"); return; }
          this.syncAll();
          $(".card-error", card).innerHTML = msg;
        } catch { /* */ }
      }
    }
  },

  async reloadAfterConfirm(tid) {
    try { this.st = await api("GET", "/api/jury/state"); } catch { return; }
    this.cleanDrafts();
    const conf = this.confirmedMap();
    const card = $(`.team-card[data-team="${tid}"]`);
    const idx = this.st.teams.findIndex((t) => String(t.id) === tid);
    if (card && conf[tid]) {
      const tmp = document.createElement("div");
      tmp.innerHTML = this.cardHtml(this.st.teams[idx], conf[tid], 0).trim();
      const nc = tmp.firstElementChild;
      nc.classList.remove("enter");
      $(".chip-ok .icon", nc)?.classList.add("pop");
      card.replaceWith(nc);
    }
    const done = Object.keys(conf).length, total = this.st.teams.length;
    $("#jp-text").innerHTML = `<strong>${done}</strong> / ${total} komanda təsdiqlənib`;
    const bar = $("#jp-bar");
    bar.setAttribute("aria-valuenow", String(done));
    setProgress(bar, total ? (done * 100) / total : 0);
    $$("[data-filter]").forEach((b) => {
      const n = b.dataset.filter === "all" ? total : b.dataset.filter === "done" ? done : total - done;
      $(".num", b).textContent = `(${n})`;
    });
    if (done === total) { this.render(); return; }
    this.syncAll();
    this.applyFilter();
  },
};

boot();
