/* Sentinel-2 reservoir dashboard. Static: reads data/ndci.json, data/meta.json, images/. */
"use strict";

const state = {
  lang: "es", res: "all", from: "", to: "", clear: 50, thr: 0.1,
  high: false, img: false, view: null, // view = {res, date}
  sortKey: "date", sortDir: -1,
};
let ROWS = [], META = null, RESERVOIRS = [], FILTERED = [];
const $ = (id) => document.getElementById(id);
const t = (k) => (I18N[state.lang][k] ?? k);
const chl = (x) => 14.039 + 86.115 * x + 194.325 * x * x; // Mishra & Mishra 2012
const fmt = (v, d = 2) => (v == null || Number.isNaN(v) ? "–" : Number(v).toFixed(d));
const pct = (v) => (v == null ? "–" : Math.round(100 * v) + " %");

// Storage can be unavailable (private mode); never depend on it.
const store = {
  get(k) { try { return localStorage.getItem(k); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch { /* ignore */ } },
};

// URL <-> state, so a filtered view or an image can be shared as a link
function readUrl() {
  const p = new URLSearchParams(location.hash.slice(1));
  if (p.get("lang")) state.lang = p.get("lang");
  else if (store.get("lang")) state.lang = store.get("lang");
  for (const k of ["res", "from", "to"]) if (p.get(k)) state[k] = p.get(k);
  if (p.get("clear")) state.clear = +p.get("clear");
  if (p.get("thr")) state.thr = +p.get("thr");
  state.high = p.get("high") === "1";
  state.img = p.get("img") === "1";
  if (p.get("view")) { const [r, d] = p.get("view").split("@"); state.view = { res: r, date: d }; }
}
function writeUrl() {
  const p = new URLSearchParams({ lang: state.lang, res: state.res, from: state.from, to: state.to,
    clear: state.clear, thr: state.thr });
  if (state.high) p.set("high", "1");
  if (state.img) p.set("img", "1");
  if (state.view) p.set("view", `${state.view.res}@${state.view.date}`);
  history.replaceState(null, "", "#" + p.toString());
}

function applyLang() {
  document.documentElement.lang = state.lang;
  document.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll("[data-i18n-html]").forEach((el) => { el.innerHTML = t(el.dataset.i18nHtml); });
  $("lang").textContent = t("lang");
  document.title = t("title");
  if (META) $("updated").textContent = new Date(META.updated_utc).toLocaleString(state.lang);
  const ticks = [-0.1, 0, 0.1, 0.2, 0.3, 0.4];
  $("ticks").innerHTML = ticks.map((v) =>
    `<span style="left:${((v + 0.1) / 0.5) * 100}%">${v.toFixed(1)}<br><small>~${Math.round(chl(v))}</small></span>`).join("");
}

function colors() {
  const s = getComputedStyle(document.documentElement);
  const g = (n) => s.getPropertyValue(n).trim();
  return { surface: g("--surface"), text: g("--text"), text2: g("--text-2"), border: g("--border"),
    median: g("--s-median"), p90: g("--s-p90"), b4: g("--s-b4"), high: g("--high") };
}

// Filtering -------------------------------------------------------------------
function filterRows() {
  return ROWS.filter((r) =>
    (state.res === "all" || r.reservoir === state.res) &&
    (!state.from || r.date >= state.from) && (!state.to || r.date <= state.to) &&
    r.frac_valid * 100 >= state.clear &&
    (!state.high || r.ndci_p90 >= state.thr) &&
    (!state.img || r.img));
}

function render() {
  FILTERED = filterRows();
  $("v-clear").textContent = state.clear + " %";
  $("v-thr").textContent = state.thr.toFixed(2) + ` (~${Math.round(chl(state.thr))} µg/L)`;
  renderCards();
  renderCharts();
  renderTable();
  writeUrl();
}

// Cards -----------------------------------------------------------------------
function renderCards() {
  $("cards").innerHTML = "";
  for (const name of RESERVOIRS) {
    const good = ROWS.filter((r) => r.reservoir === name && r.frac_valid >= 0.5);
    if (!good.length) continue;
    const last = good[good.length - 1];
    const below = good.filter((r) => r.ndci_p90 < last.ndci_p90).length;
    const p = Math.round((100 * below) / good.length);
    const hi = last.ndci_p90 >= state.thr;
    const el = document.createElement("div");
    el.className = "card";
    el.tabIndex = 0;
    el.innerHTML = `<h3>${name}${hi ? ` <span class="badge high">▲ ${t("above")}</span>` : ""}</h3>
      <div class="lbl">${t("latest")}: <b>${last.date}</b> · ${pct(last.frac_valid)} ${t("clear")}</div>
      <div class="big">${fmt(last.ndci_p90)} <span class="lbl">NDCI p90 · ${t("median")} ${fmt(last.ndci_p50)}</span></div>
      <div class="lbl">${t("pct_of").replace("{p}", p)}</div>`;
    const open = () => openViewer(name, last.date);
    el.addEventListener("click", open);
    el.addEventListener("keydown", (e) => { if (e.key === "Enter") open(); });
    $("cards").appendChild(el);
  }
}

// Charts ----------------------------------------------------------------------
function layoutBase(c, title, ytitle) {
  return {
    title: { text: title, x: 0.01, font: { size: 14, color: c.text } },
    paper_bgcolor: c.surface, plot_bgcolor: c.surface,
    font: { color: c.text2, size: 12 },
    margin: { l: 56, r: 16, t: 36, b: 36 },
    xaxis: { type: "date", gridcolor: c.border, linecolor: c.border, zeroline: false },
    yaxis: { title: { text: ytitle }, gridcolor: c.border, zeroline: false },
    legend: { orientation: "h", x: 1, xanchor: "right", y: 1.12 },
    hovermode: "closest", hoverlabel: { bgcolor: c.surface, bordercolor: c.border, font: { color: c.text } },
  };
}
const cfg = { displaylogo: false, responsive: true,
  modeBarButtonsToRemove: ["select2d", "lasso2d", "autoScale2d"] };

function renderCharts() {
  const c = colors();
  const names = state.res === "all" ? RESERVOIRS : [state.res];
  const box = $("charts"), boxB4 = $("charts-b4");
  box.innerHTML = ""; boxB4.innerHTML = "";
  for (const name of names) {
    const d = FILTERED.filter((r) => r.reservoir === name);
    const x = d.map((r) => r.date);
    const cd = d.map((r) => [name, r.date, pct(r.frac_valid)]);
    const hi = d.filter((r) => r.ndci_p90 >= state.thr);
    const hover = "%{x}<br>%{fullData.name}: %{y:.3f}<br>%{customdata[2]} " + t("clear") + "<extra></extra>";
    const traces = [
      { x, y: d.map((r) => r.ndci_p50), customdata: cd, name: "NDCI " + t("median"), type: "scatter",
        mode: "lines+markers", line: { color: c.median, width: 1.5 }, marker: { size: 6, color: c.median },
        hovertemplate: hover },
      { x, y: d.map((r) => r.ndci_p90), customdata: cd, name: "NDCI p90", type: "scatter", mode: "markers",
        marker: { size: 8, color: c.p90, line: { color: c.surface, width: 1 } }, hovertemplate: hover },
      { x: hi.map((r) => r.date), y: hi.map((r) => r.ndci_p90), customdata: hi.map((r) => [name, r.date, pct(r.frac_valid)]),
        name: t("above"), type: "scatter", mode: "markers", hovertemplate: hover,
        marker: { size: 15, color: "rgba(0,0,0,0)", line: { color: c.high, width: 2 } } },
    ];
    const lay = layoutBase(c, name, "NDCI");
    lay.shapes = [{ type: "line", xref: "paper", x0: 0, x1: 1, y0: state.thr, y1: state.thr,
      line: { color: c.high, width: 1.5, dash: "dot" } }];
    const div = document.createElement("div");
    div.className = "chart";
    box.appendChild(div);
    Plotly.newPlot(div, traces, lay, cfg);
    div.on("plotly_click", (ev) => { const p = ev.points[0]; openViewer(p.customdata[0], p.customdata[1]); });

    const lb = layoutBase(c, name, "B4");
    lb.showlegend = false;
    const divB = document.createElement("div");
    divB.className = "chart small";
    boxB4.appendChild(divB);
    Plotly.newPlot(divB, [{ x, y: d.map((r) => r.b4_p50), customdata: cd, name: "B4", type: "scatter",
      mode: "markers", marker: { size: 6, color: c.b4 }, hovertemplate: "%{x}<br>B4: %{y:.3f}<extra></extra>" }], lb, cfg);
    divB.on("plotly_click", (ev) => { const p = ev.points[0]; openViewer(p.customdata[0], p.customdata[1]); });
  }
}

// Viewer ----------------------------------------------------------------------
function openViewer(res, date, scroll = true) {
  const r = ROWS.find((x) => x.reservoir === res && x.date === date);
  if (!r) return;
  state.view = { res, date };
  const v = $("viewer");
  v.hidden = false;
  $("v-title").textContent = `${res} · ${date}`;
  $("v-stats").textContent =
    `NDCI p50 ${fmt(r.ndci_p50)} · p90 ${fmt(r.ndci_p90)} · ${t("c_gt")} ${pct(r["frac_ndci_gt_0.1"])} · ` +
    `B4 ${fmt(r.b4_p50, 3)} · ${t("c_nir")} ${pct(r.frac_high_nir)} · ${pct(r.frac_valid)} ${t("clear")}`;
  const base = `images/${encodeURIComponent(res)}/${date}`;
  $("v-rgb").hidden = $("v-ndci").hidden = !r.img;
  $("v-rgb").parentElement.hidden = $("v-ndci").parentElement.hidden = !r.img;
  $("v-noimg").hidden = r.img;
  if (r.img) {
    $("v-rgb").src = base + "_rgb.webp"; $("v-rgb").alt = `${res} ${date} ${t("cap_rgb")}`;
    $("v-ndci").src = base + "_ndci.webp"; $("v-ndci").alt = `${res} ${date} NDCI`;
  }
  writeUrl();
  if (scroll) v.scrollIntoView({ behavior: "smooth", block: "start" });
}
function step(dir) {
  if (!state.view) return;
  // Navigate within the current filter, same reservoir
  const list = FILTERED.filter((r) => r.reservoir === state.view.res);
  let i = list.findIndex((r) => r.date === state.view.date);
  if (i < 0) i = list.findIndex((r) => r.date > state.view.date) - (dir > 0 ? 1 : 0);
  const n = list[i + dir];
  if (n) openViewer(n.reservoir, n.date, false);
}

// Table -----------------------------------------------------------------------
const COLS = [
  ["reservoir", "c_res", (r) => r.reservoir],
  ["date", "c_date", (r) => r.date],
  ["ndci_p50", "c_p50", (r) => fmt(r.ndci_p50, 3)],
  ["ndci_p90", "c_p90", (r) => fmt(r.ndci_p90, 3)],
  ["frac_ndci_gt_0.1", "c_gt", (r) => pct(r["frac_ndci_gt_0.1"])],
  ["b4_p50", "c_b4", (r) => fmt(r.b4_p50, 3)],
  ["frac_high_nir", "c_nir", (r) => pct(r.frac_high_nir)],
  ["frac_valid", "c_clear", (r) => pct(r.frac_valid)],
  ["img", "c_img", (r) => (r.img ? t("yes") : t("no"))],
];
function renderTable() {
  const k = state.sortKey, s = state.sortDir;
  const rows = [...FILTERED].sort((a, b) => (a[k] > b[k] ? s : a[k] < b[k] ? -s : 0));
  $("n-rows").textContent = rows.length;
  $("tbl").tHead.innerHTML = "<tr>" + COLS.map(([key, lbl]) =>
    `<th data-k="${key}">${t(lbl)}${key === k ? (s > 0 ? " ▲" : " ▼") : ""}</th>`).join("") + "</tr>";
  $("tbl").tBodies[0].innerHTML = rows.map((r) =>
    `<tr data-r="${r.reservoir}" data-d="${r.date}">` + COLS.map(([key, , f]) =>
      `<td${key === "ndci_p90" && r.ndci_p90 >= state.thr ? ' class="hi"' : ""}>${f(r)}</td>`).join("") + "</tr>").join("");
}

function downloadFiltered() {
  const keys = Object.keys(ROWS[0] || {}).filter((k) => k !== "img");
  const esc = (v) => (v == null ? "" : /[",\n]/.test(String(v)) ? `"${String(v).replace(/"/g, '""')}"` : v);
  const csv = [keys.join(","), ...FILTERED.map((r) => keys.map((k) => esc(r[k])).join(","))].join("\n");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
  a.download = `reservoir_ndci_${state.res}_${state.from || "start"}_${state.to || "end"}.csv`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

// Wiring ----------------------------------------------------------------------
function syncInputs() {
  $("f-res").value = state.res; $("f-from").value = state.from; $("f-to").value = state.to;
  $("f-clear").value = state.clear; $("f-thr").value = state.thr;
  $("f-high").checked = state.high; $("f-img").checked = state.img;
}
function wire() {
  const on = (id, ev, fn) => $(id).addEventListener(ev, fn);
  on("f-res", "change", (e) => { state.res = e.target.value; render(); });
  on("f-from", "change", (e) => { state.from = e.target.value; render(); });
  on("f-to", "change", (e) => { state.to = e.target.value; render(); });
  on("f-clear", "input", (e) => { state.clear = +e.target.value; render(); });
  on("f-thr", "input", (e) => { state.thr = +e.target.value; render(); });
  on("f-high", "change", (e) => { state.high = e.target.checked; render(); });
  on("f-img", "change", (e) => { state.img = e.target.checked; render(); });
  document.querySelectorAll("[data-range]").forEach((b) => b.addEventListener("click", () => {
    const last = ROWS.reduce((m, r) => (r.date > m ? r.date : m), "");
    if (b.dataset.range === "all") { state.from = ""; state.to = ""; }
    else {
      const d = new Date(last); d.setDate(d.getDate() - +b.dataset.range);
      state.from = d.toISOString().slice(0, 10); state.to = "";
    }
    syncInputs(); render();
  }));
  on("lang", "click", () => { state.lang = state.lang === "es" ? "en" : "es"; store.set("lang", state.lang);
    applyLang(); render(); if (state.view) openViewer(state.view.res, state.view.date, false); });
  on("v-prev", "click", () => step(-1));
  on("v-next", "click", () => step(1));
  on("v-close", "click", () => { $("viewer").hidden = true; state.view = null; writeUrl(); });
  document.addEventListener("keydown", (e) => {
    if ($("viewer").hidden || /INPUT|SELECT/.test(document.activeElement.tagName)) return;
    if (e.key === "ArrowLeft") step(-1);
    if (e.key === "ArrowRight") step(1);
  });
  $("tbl").tHead.addEventListener("click", (e) => {
    const k = e.target.closest("th")?.dataset.k; if (!k) return;
    state.sortDir = state.sortKey === k ? -state.sortDir : (k === "date" ? -1 : -1);
    state.sortKey = k; renderTable();
  });
  $("tbl").tBodies[0].addEventListener("click", (e) => {
    const tr = e.target.closest("tr"); if (tr) openViewer(tr.dataset.r, tr.dataset.d);
  });
  on("dl-filtered", "click", downloadFiltered);
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", renderCharts);
}

async function main() {
  readUrl();
  applyLang();
  const [cols, meta] = await Promise.all([
    fetch("data/ndci.json", { cache: "no-cache" }).then((r) => r.json()),
    fetch("data/meta.json", { cache: "no-cache" }).then((r) => r.json()),
  ]);
  META = meta;
  const keys = Object.keys(cols);
  ROWS = cols.date.map((_, i) => Object.fromEntries(keys.map((k) => [k, cols[k][i]])));
  RESERVOIRS = [...new Set(ROWS.map((r) => r.reservoir))];
  for (const n of RESERVOIRS) $("f-res").insertAdjacentHTML("beforeend", `<option value="${n}">${n}</option>`);
  if (state.res !== "all" && !RESERVOIRS.includes(state.res)) state.res = "all";
  applyLang(); syncInputs(); wire(); render();
  if (state.view) openViewer(state.view.res, state.view.date);
}
main().catch((e) => {
  document.querySelector("main").insertAdjacentHTML("afterbegin",
    `<p class="note">Error loading data / Error al cargar datos: ${e.message}</p>`);
});
