/* Sentinel-2 reservoir dashboard. Static: reads data/ndci.json, data/meta.json,
   data/columns.json (optional) and images/. */
"use strict";

// Settings ---------------------------------------------------------------------
const RELIABLE = 0.5;        // a date is "usable" when at least half the reservoir is cloud-free
const LEVEL_PCT = [50, 75, 90]; // ndci_p90 percentiles of usable dates: Low | Medium | Elevated | Very high
const SEDIMENT_PCT = 90;     // B4 above this reservoir percentile -> "sediment" warning
const SURFACE_FRAC = 0.1;    // frac_high_nir above this -> "surface" warning

const state = {
  lang: "es", res: "all", from: "", to: "", clear: 50,
  high: false, img: false, view: null, sortKey: "date", sortDir: -1,
};
let ROWS = [], META = null, COLMETA = null, RESERVOIRS = [], FILTERED = [];
const STATS = {}; // per reservoir: level thresholds, B4 threshold

const $ = (id) => document.getElementById(id);
const t = (k, vars) => {
  let s = I18N[state.lang][k] ?? k;
  if (vars) for (const [a, b] of Object.entries(vars)) s = s.replace(`{${a}}`, b);
  return s;
};
const chl = (x) => 14.039 + 86.115 * x + 194.325 * x * x; // Mishra & Mishra 2012
const fmt = (v, d = 2) => (v == null || Number.isNaN(v) ? "–" : Number(v).toFixed(d));
const pct = (v) => (v == null ? "–" : Math.round(100 * v) + " %");
const store = {
  get(k) { try { return localStorage.getItem(k); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch { /* ignore */ } },
};
const fmtDate = (d, opts = { day: "numeric", month: "short", year: "numeric" }) =>
  new Date(d + "T12:00:00Z").toLocaleDateString(state.lang, { ...opts, timeZone: "UTC" });

function quantile(sorted, q) {
  if (!sorted.length) return null;
  const pos = (sorted.length - 1) * q, lo = Math.floor(pos), hi = Math.ceil(pos);
  return sorted[lo] + (sorted[hi] - sorted[lo]) * (pos - lo);
}

// Classification ---------------------------------------------------------------
function computeStats() {
  for (const name of RESERVOIRS) {
    const good = ROWS.filter((r) => r.reservoir === name && r.frac_valid >= RELIABLE);
    const p90 = good.map((r) => r.ndci_p90).filter((v) => v != null).sort((a, b) => a - b);
    const b4 = good.map((r) => r.b4_p50).filter((v) => v != null).sort((a, b) => a - b);
    STATS[name] = { p90, cut: LEVEL_PCT.map((q) => quantile(p90, q / 100)),
                    b4cut: quantile(b4, SEDIMENT_PCT / 100) };
  }
  for (const r of ROWS) {
    const s = STATS[r.reservoir];
    r.level = r.ndci_p90 == null ? 0 : 1 + s.cut.filter((c) => r.ndci_p90 >= c).length;
    r.rank = s.p90.length ? Math.round(100 * s.p90.filter((v) => v < r.ndci_p90).length / s.p90.length) : null;
    r.notes = [];
    if (r.frac_valid < RELIABLE) r.notes.push("clouds");
    if (r.b4_p50 != null && r.b4_p50 >= s.b4cut) r.notes.push("sediment");
    if (r.frac_high_nir != null && r.frac_high_nir >= SURFACE_FRAC) r.notes.push("surface");
  }
}
const LEVEL_ICON = ["", "●", "●", "▲", "▲▲"];
function levelBadge(l, long = false) {
  if (!l) return "–";
  return `<span class="lvl lvl-${l}"><span aria-hidden="true">${LEVEL_ICON[l]}</span> ${t("lvl_" + l)}</span>` +
    (long ? ` <span class="note">${t("lvl_" + l + "_long")}</span>` : "");
}
function noteText(r, n) {
  return t("note_" + n, { p: n === "clouds" ? Math.round(100 * r.frac_valid) : Math.round(100 * r.frac_high_nir) });
}

// URL <-> state, so a view can be shared as a link --------------------------------
function readUrl() {
  const p = new URLSearchParams(location.hash.slice(1));
  state.lang = p.get("lang") || store.get("lang") || "es";
  if (!I18N[state.lang]) state.lang = "es";
  for (const k of ["res", "from", "to"]) if (p.get(k)) state[k] = p.get(k);
  if (p.get("clear")) state.clear = +p.get("clear");
  state.high = p.get("high") === "1";
  state.img = p.get("img") === "1";
  if (p.get("view")) { const [r, d] = p.get("view").split("@"); state.view = { res: r, date: d }; }
}
function writeUrl() {
  const p = new URLSearchParams({ lang: state.lang, res: state.res });
  if (state.from) p.set("from", state.from);
  if (state.to) p.set("to", state.to);
  if (state.clear !== 50) p.set("clear", state.clear);
  if (state.high) p.set("high", "1");
  if (state.img) p.set("img", "1");
  if (state.view) p.set("view", `${state.view.res}@${state.view.date}`);
  history.replaceState(null, "", "#" + p.toString());
}

// Static text ------------------------------------------------------------------
function applyLang() {
  document.documentElement.lang = state.lang;
  document.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll("[data-i18n-html]").forEach((el) => { el.innerHTML = t(el.dataset.i18nHtml); });
  $("lang").textContent = t("lang");
  document.title = t("title");
  if (META) $("updated").textContent = new Date(META.updated_utc).toLocaleString(state.lang,
    { dateStyle: "medium", timeStyle: "short" });
  $("ticks").innerHTML = [-0.1, 0, 0.1, 0.2, 0.3, 0.4].map((v) =>
    `<span style="left:${((v + 0.1) / 0.5) * 100}%">${v.toFixed(1)}<br><small>~${Math.round(chl(v))}</small></span>`).join("");
  $("explain").innerHTML = I18N[state.lang].explain.map(([h, body], i) =>
    `<details${i < 2 ? " open" : ""}><summary>${h}</summary>${body}</details>`).join("");
}

function colors() {
  const s = getComputedStyle(document.documentElement);
  const g = (n) => s.getPropertyValue(n).trim();
  return { surface: g("--surface"), text: g("--text"), text2: g("--text-2"), border: g("--border"),
    median: g("--s-median"), p90: g("--s-p90"), b4: g("--s-b4"), l3: g("--st-warning"), l4: g("--st-critical"),
    temp: g("--s-temp"), tempBand: g("--s-temp-band") };
}

// Rendering --------------------------------------------------------------------
function filterRows() {
  return ROWS.filter((r) =>
    (state.res === "all" || r.reservoir === state.res) &&
    (!state.from || r.date >= state.from) && (!state.to || r.date <= state.to) &&
    r.frac_valid * 100 >= state.clear &&
    (!state.high || r.level >= 3) && (!state.img || r.img));
}
function render() {
  FILTERED = filterRows();
  $("v-clear").textContent = state.clear + " %";
  renderCards(); renderSeason(); renderCharts(); renderTable(); renderSampling();
  writeUrl();
}

function tempLine(name) {
  const r = lastTemp(name);
  if (!r) return "";
  return `<div class="lbl">🌡 ${t("temp_last")}: <b>${r.temp_p50.toFixed(1)} °C</b> (Landsat, ${fmtDate(r.date)})</div>`;
}
function daysAgo(d) {
  const n = Math.round((Date.now() - new Date(d + "T15:15:00Z")) / 864e5);
  return n <= 0 ? t("today") : n === 1 ? t("yesterday") : t("days_ago", { n });
}
function renderCards() {
  $("cards").innerHTML = "";
  for (const name of RESERVOIRS) {
    const good = ROWS.filter((r) => r.reservoir === name && r.frac_valid >= RELIABLE);
    const el = document.createElement("div");
    el.className = "card";
    if (!good.length) { el.innerHTML = `<h3>${name}</h3><p>${t("no_recent")}</p>`; $("cards").appendChild(el); continue; }
    const r = good[good.length - 1];
    const thumb = r.img ? `<img class="thumb" alt="" loading="lazy" src="images/${encodeURIComponent(name)}/${r.date}_ndci.webp">` : "";
    el.innerHTML = `
      <div class="card-text">
        <h3>${name}</h3>
        <div class="lbl">${t("last_image")}: <b>${fmtDate(r.date)}</b> (${daysAgo(r.date)}) · ${pct(r.frac_valid)} ${t("visible")}</div>
        <div class="big">${levelBadge(r.level)}</div>
        <p class="sentence">${t("card_sentence", { p: r.rank })}</p>
        ${tempLine(name)}
        ${r.notes.length ? `<ul class="notes">${r.notes.map((n) => `<li>⚠ ${noteText(r, n)}</li>`).join("")}</ul>` : ""}
        <button type="button" class="btn">${t("see_images")}</button>
      </div>${thumb}`;
    el.querySelector("button").addEventListener("click", () => openViewer(name, r.date));
    if (thumb) el.querySelector("img").addEventListener("click", () => openViewer(name, r.date));
    $("cards").appendChild(el);
  }
}

const cfg = { displaylogo: false, responsive: true, displayModeBar: false };
function baseLayout(c, title, ytitle) {
  return {
    title: { text: title, x: 0.01, font: { size: 14, color: c.text } },
    paper_bgcolor: c.surface, plot_bgcolor: c.surface, font: { color: c.text2, size: 12 },
    margin: { l: 56, r: 16, t: 36, b: 36 },
    xaxis: { gridcolor: c.border, linecolor: c.border, zeroline: false },
    yaxis: { title: { text: ytitle }, gridcolor: c.border, zeroline: false },
    legend: { orientation: "h", x: 1, xanchor: "right", y: 1.14 },
    hovermode: "closest", hoverlabel: { bgcolor: c.surface, bordercolor: c.border, font: { color: c.text } },
  };
}

function renderSeason() {
  const c = colors(), box = $("season");
  box.innerHTML = "";
  const months = [...Array(12).keys()];
  const mName = (m) => new Date(Date.UTC(2020, m, 15)).toLocaleDateString(state.lang, { month: "short", timeZone: "UTC" });
  const names = state.res === "all" ? RESERVOIRS : [state.res];
  const plots = []; // create all containers first, so each chart gets its final width
  for (const name of names) {
    const good = ROWS.filter((r) => r.reservoir === name && r.frac_valid >= RELIABLE && r.ndci_p90 != null);
    const med = [], n = [];
    for (const m of months) {
      const v = good.filter((r) => +r.date.slice(5, 7) === m + 1).map((r) => r.ndci_p90).sort((a, b) => a - b);
      med.push(quantile(v, 0.5)); n.push(v.length);
    }
    const top = months.filter((m) => med[m] != null).sort((a, b) => med[b] - med[a]).slice(0, 3).map(mName);
    const wrap = document.createElement("div");
    wrap.className = "season-item";
    const div = document.createElement("div");
    div.className = "chart small";
    wrap.appendChild(div);
    wrap.insertAdjacentHTML("beforeend", `<p class="note">${t("season_top")}: <b>${top.join(", ")}</b></p>`);
    box.appendChild(wrap);
    const lay = baseLayout(c, name, t("axis_ndci"));
    lay.showlegend = false;
    lay.margin.b = 28;
    lay.bargap = 0.25;
    plots.push([div, [{ type: "bar", x: months.map(mName), y: med, customdata: n,
      marker: { color: c.p90 }, hovertemplate: `%{x}: %{y:.3f}<br>%{customdata} ${t("season_n")}<extra></extra>` }], lay]);
  }
  // same y-scale for all reservoirs, so bar heights can be compared between them
  const all = plots.flatMap(([, d]) => d[0].y).filter((v) => v != null);
  const range = [Math.min(0, ...all) * 1.1, Math.max(0, ...all) * 1.1];
  for (const [div, data, lay] of plots) { lay.yaxis.range = range; Plotly.newPlot(div, data, lay, cfg); }
}

function renderCharts() {
  const c = colors(), names = state.res === "all" ? RESERVOIRS : [state.res];
  const box = $("charts"), boxB4 = $("charts-b4");
  box.innerHTML = ""; boxB4.innerHTML = "";
  for (const name of names) {
    const d = FILTERED.filter((r) => r.reservoir === name);
    const x = d.map((r) => r.date);
    const cd = d.map((r) => [name, r.date, pct(r.frac_valid), t("lvl_" + r.level)]);
    const hover = `%{x|%d %b %Y}<br>%{fullData.name}: %{y:.3f}<br>%{customdata[3]} · %{customdata[2]} ${t("visible")}<extra></extra>`;
    const [, c75, c90] = STATS[name].cut;
    const lay = baseLayout(c, name, t("axis_ndci"));
    lay.xaxis.type = "date";
    lay.shapes = [[c75, c.l3], [c90, c.l4]].map(([y, col]) => ({ type: "line", xref: "paper", x0: 0, x1: 1, y0: y, y1: y,
      line: { color: col, width: 1.5, dash: "dot" } }));
    // "Elevated" label under its line, "Very high" above its line, so they never overlap
    lay.annotations = [[c75, "line_l3", "top"], [c90, "line_l4", "bottom"]].map(([y, k, ya]) => ({
      xref: "paper", x: 1, xanchor: "right", y, yanchor: ya, text: t(k), showarrow: false,
      font: { size: 11, color: c.text2 }, bgcolor: c.surface }));
    const div = document.createElement("div");
    div.className = "chart";
    box.appendChild(div);
    Plotly.newPlot(div, [
      { x, y: d.map((r) => r.ndci_p50), customdata: cd, name: t("s_p50"), type: "scatter", mode: "lines+markers",
        line: { color: c.median, width: 1 }, marker: { size: 5, color: c.median }, hovertemplate: hover },
      { x, y: d.map((r) => r.ndci_p90), customdata: cd, name: t("s_p90"), type: "scatter", mode: "markers",
        marker: { size: 8, color: c.p90, line: { color: c.surface, width: 1 } }, hovertemplate: hover },
    ], lay, cfg);
    div.on("plotly_click", (ev) => { const p = ev.points[0]; openViewer(p.customdata[0], p.customdata[1]); });

    const lb = baseLayout(c, name, "B4");
    lb.xaxis.type = "date"; lb.showlegend = false;
    const divB = document.createElement("div");
    divB.className = "chart small";
    boxB4.appendChild(divB);
    Plotly.newPlot(divB, [{ x, y: d.map((r) => r.b4_p50), customdata: cd, type: "scatter", mode: "markers",
      marker: { size: 6, color: c.b4 }, hovertemplate: "%{x|%d %b %Y}<br>B4: %{y:.3f}<extra></extra>" }], lb, cfg);
    divB.on("plotly_click", (ev) => { const p = ev.points[0]; openViewer(p.customdata[0], p.customdata[1]); });
  }
}

// Viewer -----------------------------------------------------------------------
function openViewer(res, date, scroll = true) {
  const r = ROWS.find((x) => x.reservoir === res && x.date === date);
  if (!r) return;
  if (state.view?.res !== res) VIEWZOOM?.reset(); // keep the zoom when stepping through dates
  state.view = { res, date };
  $("viewer").hidden = false;
  $("v-title").textContent = `${res} · ${fmtDate(date, { weekday: "long", day: "numeric", month: "long", year: "numeric" })}`;
  $("v-summary").innerHTML = t("v_summary", { lvl: levelBadge(r.level), long: t("lvl_" + r.level + "_long"),
    vis: Math.round(100 * r.frac_valid) });
  $("v-notes").innerHTML = r.notes.map((n) => `<li>⚠ ${noteText(r, n)}</li>`).join("");
  $("v-stats").textContent =
    `NDCI p50 ${fmt(r.ndci_p50, 3)} · p90 ${fmt(r.ndci_p90, 3)} · NDCI>0.1 ${pct(r["frac_ndci_gt_0.1"])} · ` +
    `B4 ${fmt(r.b4_p50, 3)} · B8>0.05 ${pct(r.frac_high_nir)} · ${pct(r.frac_valid)} ${t("visible")} · ${r.scene ?? ""}`;
  const base = `images/${encodeURIComponent(res)}/${date}`;
  $("v-rgb").closest("figure").hidden = $("v-ndci").closest("figure").hidden = !r.img;
  $("v-tools").hidden = !r.img;
  $("v-noimg").hidden = r.img;
  if (r.img) {
    $("v-rgb").src = base + "_rgb.webp"; $("v-rgb").alt = `${res} ${date} ${t("cap_rgb")}`;
    $("v-ndci").src = base + "_ndci.webp"; $("v-ndci").alt = `${res} ${date} NDCI`;
  }
  refreshMarkers();
  writeUrl();
  if (scroll) $("viewer").scrollIntoView({ behavior: "smooth", block: "start" });
}
function step(dir) {
  if (!state.view) return;
  const list = FILTERED.filter((r) => r.reservoir === state.view.res);
  let i = list.findIndex((r) => r.date === state.view.date);
  if (i < 0) i = list.findIndex((r) => r.date > state.view.date) - (dir > 0 ? 1 : 0);
  const n = list[i + dir];
  if (n) openViewer(n.reservoir, n.date, false);
}

// Table ------------------------------------------------------------------------
const COLS = [
  ["date", "c_date", (r) => fmtDate(r.date)],
  ["reservoir", "c_res", (r) => r.reservoir],
  ["level", "c_lvl", (r) => levelBadge(r.level)],
  ["ndci_p90", "c_p90", (r) => fmt(r.ndci_p90, 3)],
  ["ndci_p50", "c_p50", (r) => fmt(r.ndci_p50, 3)],
  ["frac_valid", "c_vis", (r) => pct(r.frac_valid)],
  ["notes", "c_notes", (r) => r.notes.map((n) => `<span class="chip" title="${noteText(r, n)}">⚠ ${t("n_" + n)}</span>`).join(" ")],
  ["img", "c_img", (r) => (r.img ? t("yes") : t("no"))],
];
function renderTable() {
  const k = state.sortKey, s = state.sortDir;
  const val = (r) => (k === "notes" ? r.notes.length : r[k]);
  const rows = [...FILTERED].sort((a, b) => (val(a) > val(b) ? s : val(a) < val(b) ? -s : 0));
  $("n-rows").textContent = rows.length;
  $("tbl").tHead.innerHTML = "<tr>" + COLS.map(([key, lbl]) =>
    `<th data-k="${key}" title="${colHelp(key)}">${t(lbl)}${key === k ? (s > 0 ? " ▲" : " ▼") : ""}</th>`).join("") + "</tr>";
  $("tbl").tBodies[0].innerHTML = rows.map((r) =>
    `<tr data-r="${r.reservoir}" data-d="${r.date}">` + COLS.map(([, , f]) => `<td>${f(r)}</td>`).join("") + "</tr>").join("");
}
function colHelp(key) {
  const c = COLMETA?.find((x) => x.name === key);
  if (!c) return "";
  return (state.lang === "es" ? `${c.es} ${c.read_es}` : `${c.en} ${c.read_en}`).replace(/"/g, "&quot;");
}

function downloadFiltered() {
  const keys = Object.keys(ROWS[0] || {}).filter((k) => !["img", "level", "rank", "notes"].includes(k));
  const esc = (v) => (v == null ? "" : /[",\n]/.test(String(v)) ? `"${String(v).replace(/"/g, '""')}"` : v);
  const head = [`# Sentinel-2 NDCI, ${state.res === "all" ? RESERVOIRS.join(" + ") : state.res}`,
    `# ${t("dl_filtered_help")}`];
  if (COLMETA) for (const c of COLMETA)
    head.push(`#   ${c.name} | ${c.unit} | ${state.lang === "es" ? c.es + " " + c.read_es : c.en + " " + c.read_en}`.trimEnd());
  const csv = [...head, keys.join(","), ...FILTERED.map((r) => keys.map((k) => esc(r[k])).join(","))].join("\n");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
  a.download = `reservoir_ndci_${state.res}_${state.from || "start"}_${state.to || "end"}.csv`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

// Wiring -----------------------------------------------------------------------
function syncInputs() {
  $("f-res").value = state.res; $("f-from").value = state.from; $("f-to").value = state.to;
  $("f-clear").value = state.clear; $("f-high").checked = state.high; $("f-img").checked = state.img;
}
function wire() {
  const on = (id, ev, fn) => $(id).addEventListener(ev, fn);
  on("f-res", "change", (e) => { state.res = e.target.value; render(); });
  on("f-from", "change", (e) => { state.from = e.target.value; render(); });
  on("f-to", "change", (e) => { state.to = e.target.value; render(); });
  on("f-clear", "input", (e) => { state.clear = +e.target.value; render(); });
  on("f-high", "change", (e) => { state.high = e.target.checked; render(); });
  on("f-img", "change", (e) => { state.img = e.target.checked; render(); });
  document.querySelectorAll("[data-range]").forEach((b) => b.addEventListener("click", () => {
    const last = ROWS.reduce((m, r) => (r.date > m ? r.date : m), "");
    if (b.dataset.range === "all") { state.from = ""; state.to = ""; }
    else { const d = new Date(last); d.setDate(d.getDate() - +b.dataset.range);
      state.from = d.toISOString().slice(0, 10); state.to = ""; }
    syncInputs(); render();
  }));
  on("lang", "click", () => {
    state.lang = state.lang === "es" ? "en" : "es"; store.set("lang", state.lang);
    applyLang(); render(); if (state.view) openViewer(state.view.res, state.view.date, false);
  });
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
    state.sortDir = state.sortKey === k ? -state.sortDir : -1;
    state.sortKey = k; renderTable();
  });
  $("tbl").tBodies[0].addEventListener("click", (e) => {
    const tr = e.target.closest("tr"); if (tr) openViewer(tr.dataset.r, tr.dataset.d);
  });
  on("dl-filtered", "click", downloadFiltered);
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => { renderSeason(); renderCharts(); renderTemp(); });
}

async function main() {
  readUrl();
  applyLang();
  const get = (u) => fetch(u, { cache: "no-cache" }).then((r) => { if (!r.ok) throw new Error(u); return r.json(); });
  const opt = (u) => get(u).catch(() => null); // optional files
  const [cols, meta, colmeta, grids, maps, passes, temp] = await Promise.all([
    get("data/ndci.json"), get("data/meta.json"), opt("data/columns.json"), opt("data/image_grid.json"),
    opt("data/maps.json"), opt("data/passes.json"), opt("data/temperature.json")]);
  META = meta; COLMETA = colmeta; GRIDS = grids || {}; MAPS = maps; PASSES = passes;
  if (temp) TEMP = temp.date.map((_, i) => Object.fromEntries(Object.keys(temp).map((k) => [k, temp[k][i]])));
  const keys = Object.keys(cols);
  ROWS = cols.date.map((_, i) => Object.fromEntries(keys.map((k) => [k, cols[k][i]])));
  RESERVOIRS = [...new Set(ROWS.map((r) => r.reservoir))];
  for (const n of RESERVOIRS) $("f-res").insertAdjacentHTML("beforeend", `<option value="${n}">${n}</option>`);
  if (state.res !== "all" && !RESERVOIRS.includes(state.res)) state.res = "all";
  computeStats();
  initSampling();
  applyLang(); syncInputs(); wire(); render();
  if (state.view) openViewer(state.view.res, state.view.date);
}
main().catch((e) => {
  document.querySelector("main").insertAdjacentHTML("afterbegin",
    `<p class="note">Error loading data / Error al cargar datos: ${e.message}</p>`);
});
