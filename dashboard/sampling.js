/* Sampling tools: zoom, coordinates, marked points, summary maps, satellite passes,
   water temperature. Loaded before app.js; uses its helpers ($, t, state, ...) at run time. */
"use strict";

let GRIDS = {}, MAPS = null, PASSES = null, TEMP = [], POINTS = [];
const mapState = { res: null, kind: "freq" };
let VIEWZOOM = null, MAPZOOM = null;

// Coordinates ------------------------------------------------------------------
// Each reservoir's images share one north-up UTM grid; inside it, lat/lon is
// bilinear in the corner coordinates (error well below 1 m, see pipeline/grid.py).
function fracToLonLat(grid, fx, fy) {
  const c = grid.corners_lonlat;
  const top = [0, 1].map((i) => c.nw[i] + (c.ne[i] - c.nw[i]) * fx);
  const bot = [0, 1].map((i) => c.sw[i] + (c.se[i] - c.sw[i]) * fx);
  return [0, 1].map((i) => top[i] + (bot[i] - top[i]) * fy);
}
function lonLatToFrac(grid, lon, lat) {
  let fx = 0.5, fy = 0.5; // Newton iterations on the bilinear mapping
  for (let k = 0; k < 6; k++) {
    const [x, y] = fracToLonLat(grid, fx, fy), e = 1e-4;
    const [x1, y1] = fracToLonLat(grid, fx + e, fy), [x2, y2] = fracToLonLat(grid, fx, fy + e);
    const a = (x1 - x) / e, b = (x2 - x) / e, c = (y1 - y) / e, d = (y2 - y) / e;
    const det = a * d - b * c, rx = lon - x, ry = lat - y;
    fx += (d * rx - b * ry) / det; fy += (-c * rx + a * ry) / det;
  }
  return [fx, fy];
}
function fmtCoord(lat, lon) {
  const ew = lon >= 0 ? "E" : state.lang === "es" ? "O" : "W";
  return `${Math.abs(lat).toFixed(5)}° ${lat >= 0 ? "N" : "S"}, ${Math.abs(lon).toFixed(5)}° ${ew}`;
}
const decimal = (lat, lon) => `${lat.toFixed(6)}, ${lon.toFixed(6)}`;

// Marked points (kept in this browser only) --------------------------------------
function loadPoints() {
  try { POINTS = JSON.parse(localStorage.getItem("sampling_points") || "[]"); } catch { POINTS = []; }
}
function savePoints() {
  try { localStorage.setItem("sampling_points", JSON.stringify(POINTS)); } catch { /* ignore */ }
}
function addPoint(res, lat, lon, from) {
  const prefix = res.slice(0, 1).toUpperCase();
  let n = 1;
  while (POINTS.some((p) => p.name === prefix + n)) n++;
  POINTS.push({ name: prefix + n, res, lat: +lat.toFixed(6), lon: +lon.toFixed(6), from });
  savePoints(); renderPoints(); refreshMarkers();
}
const xmlEsc = (s) => String(s).replace(/[<>&"']/g, (c) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;", "'": "&apos;" })[c]);
function download(name, text, type) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([text], { type }));
  a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}
function exportGpx() {
  const wpt = POINTS.map((p) => `  <wpt lat="${p.lat}" lon="${p.lon}"><name>${xmlEsc(p.name)}</name>` +
    `<desc>${xmlEsc(`${p.res} · ${p.from}`)}</desc></wpt>`).join("\n");
  download("puntos_muestreo.gpx", `<?xml version="1.0" encoding="UTF-8"?>\n<gpx version="1.1" ` +
    `creator="embalses-s2-monitor" xmlns="http://www.topografix.com/GPX/1/1">\n${wpt}\n</gpx>\n`, "application/gpx+xml");
}
function exportCsv() {
  const q = (v) => `"${String(v).replace(/"/g, '""')}"`;
  const rows = ["name,reservoir,latitude,longitude,marked_on",
    ...POINTS.map((p) => [q(p.name), q(p.res), p.lat, p.lon, q(p.from)].join(","))];
  download("puntos_muestreo.csv", rows.join("\n") + "\n", "text/csv");
}
function renderPoints() {
  const tb = $("pts");
  $("pts-empty").hidden = POINTS.length > 0;
  tb.parentElement.hidden = POINTS.length === 0;
  ["pts-gpx", "pts-csv", "pts-clear"].forEach((id) => { $(id).disabled = POINTS.length === 0; });
  tb.tHead.innerHTML = "<tr>" + ["p_name", "p_res", "p_lat", "p_lon", "p_from", "", ""].map((k) =>
    `<th>${k ? t(k) : ""}</th>`).join("") + "</tr>";
  tb.tBodies[0].innerHTML = POINTS.map((p, i) => `<tr data-i="${i}">
    <td><input class="pt-name" value="${xmlEsc(p.name)}" aria-label="${t("p_name")}" size="8"></td>
    <td>${p.res}</td><td>${p.lat.toFixed(6)}</td><td>${p.lon.toFixed(6)}</td><td>${xmlEsc(p.from)}</td>
    <td><button type="button" class="btn small pt-copy">${t("p_copy")}</button></td>
    <td><button type="button" class="btn small pt-del">${t("p_delete")}</button></td></tr>`).join("");
}
function wirePoints() {
  const tb = $("pts").tBodies[0];
  tb.addEventListener("change", (e) => {
    if (!e.target.classList.contains("pt-name")) return;
    const p = POINTS[+e.target.closest("tr").dataset.i];
    p.name = e.target.value.trim() || p.name; savePoints(); refreshMarkers();
  });
  tb.addEventListener("click", async (e) => {
    const tr = e.target.closest("tr"); if (!tr) return;
    const p = POINTS[+tr.dataset.i];
    if (e.target.classList.contains("pt-del")) { POINTS.splice(+tr.dataset.i, 1); savePoints(); renderPoints(); refreshMarkers(); }
    if (e.target.classList.contains("pt-copy")) {
      try { await navigator.clipboard.writeText(decimal(p.lat, p.lon)); e.target.textContent = t("p_copied"); } catch { /* ignore */ }
    }
  });
  $("pts-gpx").addEventListener("click", exportGpx);
  $("pts-csv").addEventListener("click", exportCsv);
  $("pts-clear").addEventListener("click", () => {
    if (confirm(t("points_confirm"))) { POINTS = []; savePoints(); renderPoints(); refreshMarkers(); }
  });
}
function drawMarkers(box, res) {
  const layer = box.querySelector(".markers"), grid = GRIDS[res];
  if (!layer) return;
  layer.innerHTML = !grid ? "" : POINTS.filter((p) => p.res === res).map((p) => {
    const [fx, fy] = lonLatToFrac(grid, p.lon, p.lat);
    return `<div class="pin" style="left:${(100 * fx).toFixed(3)}%;top:${(100 * fy).toFixed(3)}%"><span>${xmlEsc(p.name)}</span></div>`;
  }).join("");
}
function refreshMarkers() {
  if (VIEWZOOM && state.view) VIEWZOOM.boxes.forEach((b) => drawMarkers(b, state.view.res));
  if (MAPZOOM && mapState.res) MAPZOOM.boxes.forEach((b) => drawMarkers(b, mapState.res));
}

// Zoom and pan, shared by all boxes of a group (both viewer images move together) -----
class ZoomGroup {
  constructor(boxes, tools, context) {
    Object.assign(this, { boxes, context, s: 1, tx: 0, ty: 0, mark: false, ptrs: new Map() });
    tools.innerHTML = `
      <button type="button" class="btn small" data-z="in" title="" aria-label="">+</button>
      <button type="button" class="btn small" data-z="out" aria-label="">−</button>
      <button type="button" class="btn small" data-z="reset"></button>
      <button type="button" class="btn small mark" aria-pressed="false"></button>
      <span class="coords" aria-live="off"></span>
      <span class="note hint"></span>`;
    this.tools = tools;
    tools.addEventListener("click", (e) => {
      const z = e.target.closest("button"); if (!z) return;
      const b = this.boxes[0];
      if (z.dataset.z === "in") this.zoomAt(b.clientWidth / 2, b.clientHeight / 2, 1.6);
      else if (z.dataset.z === "out") this.zoomAt(b.clientWidth / 2, b.clientHeight / 2, 1 / 1.6);
      else if (z.dataset.z === "reset") this.reset();
      else if (z.classList.contains("mark")) { this.mark = !this.mark; this.labels(); }
    });
    for (const box of boxes) this.wire(box);
    this.labels();
  }
  labels() {
    const q = (s) => this.tools.querySelector(s);
    q('[data-z="in"]').title = q('[data-z="in"]').ariaLabel = t("zoom_in");
    q('[data-z="out"]').title = q('[data-z="out"]').ariaLabel = t("zoom_out");
    q('[data-z="reset"]').textContent = t("zoom_reset");
    const m = q(".mark");
    m.textContent = this.mark ? t("mark_on") : t("mark_off");
    m.setAttribute("aria-pressed", this.mark);
    m.classList.toggle("on", this.mark);
    q(".hint").textContent = t("zoom_hint");
    if (!q(".coords").dataset.set) q(".coords").textContent = t("coords_hint");
    for (const b of this.boxes) b.classList.toggle("marking", this.mark);
  }
  apply() {
    for (const b of this.boxes) {
      const c = b.querySelector(".zoomcontent");
      c.style.transform = `translate(${this.tx}px, ${this.ty}px) scale(${this.s})`;
      c.style.setProperty("--inv", 1 / this.s);
    }
  }
  clamp() {
    const b = this.boxes[0], w = b.clientWidth, h = b.clientHeight;
    this.tx = Math.min(0, Math.max(w - w * this.s, this.tx));
    this.ty = Math.min(0, Math.max(h - h * this.s, this.ty));
  }
  zoomAt(cx, cy, f) {
    const s2 = Math.min(8, Math.max(1, this.s * f));
    this.tx = cx - (cx - this.tx) * (s2 / this.s);
    this.ty = cy - (cy - this.ty) * (s2 / this.s);
    this.s = s2; this.clamp(); this.apply();
  }
  reset() { this.s = 1; this.tx = 0; this.ty = 0; this.apply(); }
  lonlat(e, box) {
    const img = box.querySelector("img"), r = img.getBoundingClientRect();
    const fx = (e.clientX - r.left) / r.width, fy = (e.clientY - r.top) / r.height;
    const ctx = this.context(), grid = ctx && GRIDS[ctx.res];
    if (!grid || !img.complete || fx < 0 || fx > 1 || fy < 0 || fy > 1) return null;
    return fracToLonLat(grid, fx, fy);
  }
  wire(box) {
    box.addEventListener("wheel", (e) => {
      if (!(e.ctrlKey || e.metaKey)) return; // plain wheel scrolls the page
      e.preventDefault();
      const r = box.getBoundingClientRect();
      this.zoomAt(e.clientX - r.left, e.clientY - r.top, e.deltaY < 0 ? 1.25 : 0.8);
    }, { passive: false });
    box.addEventListener("dblclick", (e) => {
      const r = box.getBoundingClientRect();
      this.zoomAt(e.clientX - r.left, e.clientY - r.top, 2);
    });
    box.addEventListener("pointerdown", (e) => {
      box.setPointerCapture(e.pointerId);
      this.ptrs.set(e.pointerId, { x: e.clientX, y: e.clientY, x0: e.clientX, y0: e.clientY });
    });
    box.addEventListener("pointermove", (e) => {
      const ll = this.lonlat(e, box), co = this.tools.querySelector(".coords");
      if (ll) { co.textContent = fmtCoord(ll[1], ll[0]); co.dataset.set = "1"; }
      const p = this.ptrs.get(e.pointerId); if (!p) return;
      if (this.ptrs.size === 2) { // pinch
        const [a, b] = [...this.ptrs.values()];
        const d0 = Math.hypot(a.x - b.x, a.y - b.y);
        p.x = e.clientX; p.y = e.clientY;
        const d1 = Math.hypot(a.x - b.x, a.y - b.y), r = box.getBoundingClientRect();
        if (d0 > 0) this.zoomAt((a.x + b.x) / 2 - r.left, (a.y + b.y) / 2 - r.top, d1 / d0);
        return;
      }
      this.tx += e.clientX - p.x; this.ty += e.clientY - p.y;
      p.x = e.clientX; p.y = e.clientY;
      this.clamp(); this.apply();
    });
    const end = (e) => {
      const p = this.ptrs.get(e.pointerId);
      this.ptrs.delete(e.pointerId);
      if (!p || e.type !== "pointerup" || !this.mark) return;
      if (Math.hypot(e.clientX - p.x0, e.clientY - p.y0) > 5) return; // it was a drag
      const ll = this.lonlat(e, box), ctx = this.context();
      if (ll) addPoint(ctx.res, ll[1], ll[0], ctx.from);
    };
    box.addEventListener("pointerup", end);
    box.addEventListener("pointercancel", end);
  }
}

// Summary maps -------------------------------------------------------------------
function renderMaps() {
  const sel = $("m-res");
  if (!sel.options.length) for (const n of RESERVOIRS) sel.insertAdjacentHTML("beforeend", `<option value="${n}">${n}</option>`);
  if (!mapState.res) mapState.res = RESERVOIRS[0];
  sel.value = mapState.res;
  document.querySelectorAll("[data-map]").forEach((b) => b.classList.toggle("active", b.dataset.map === mapState.kind));
  const m = MAPS && MAPS[mapState.res];
  const box = $("m-img").closest(".map-wrap");
  box.hidden = !m; $("m-tools").hidden = !m;
  if (!m) { $("m-lo").textContent = $("m-hi").textContent = ""; $("m-note").textContent = t("map_missing"); return; }
  const src = `images/maps/${encodeURIComponent(mapState.res)}_${mapState.kind}.webp?v=${encodeURIComponent(m.rendered_utc)}`;
  if ($("m-img").getAttribute("src") !== src) $("m-img").src = src;
  $("m-img").alt = `${mapState.res}: ${t(mapState.kind === "freq" ? "map_freq" : "map_mean")}`;
  document.querySelector("#maps .bar.seq").style.background =
    `linear-gradient(90deg, ${m.palette.map((c) => "#" + c).join(", ")})`;
  const vars = { n: m.n_images, a: fmtDate(m.period[0]), b: fmtDate(m.period[1]), t: m.green_ndci };
  if (mapState.kind === "freq") {
    $("m-lo").textContent = t("map_freq_lo");
    $("m-hi").textContent = t("map_freq_hi", { p: Math.round(100 * m.freq_max) });
    $("m-note").textContent = t("map_freq_note", vars);
  } else {
    $("m-lo").textContent = t("map_mean_lo", { v: m.mean_range[0].toFixed(2) });
    $("m-hi").textContent = t("map_mean_hi", { v: m.mean_range[1].toFixed(2) });
    $("m-note").textContent = t("map_mean_note", vars);
  }
  refreshMarkers();
}

// Satellite passes ---------------------------------------------------------------
function renderPasses() {
  const box = $("passes");
  box.innerHTML = "";
  if (!PASSES) { box.hidden = true; return; }
  const today = new Date().toLocaleDateString("en-CA", { timeZone: "America/Santo_Domingo" });
  const tomorrow = new Date(Date.now() + 864e5).toLocaleDateString("en-CA", { timeZone: "America/Santo_Domingo" });
  for (const name of RESERVOIRS) {
    const p = PASSES[name] || {};
    const items = [...(p.s2 || []).map(([d]) => [d, "s2"]), ...(p.landsat || []).map(([d]) => [d, "ls"])]
      .filter(([d]) => d >= today).sort();
    const byDate = new Map();
    for (const [d, k] of items) { if (!byDate.has(d)) byDate.set(d, new Set()); byDate.get(d).add(k); }
    const lines = [...byDate.entries()].slice(0, 8).map(([d, ks]) => {
      const rel = d === today ? ` (${t("pass_today")})` : d === tomorrow ? ` (${t("pass_tomorrow")})` : "";
      return `<li><b>${fmtDate(d, { weekday: "short", day: "numeric", month: "short" })}</b>${rel} · ` +
        [...ks].sort().reverse().map((k) => t(k === "s2" ? "pass_s2" : "pass_ls")).join(" · ") + "</li>";
    });
    box.insertAdjacentHTML("beforeend", `<div class="card passes-card"><div><h3>${name}</h3>
      ${lines.length ? `<ul class="pass-list">${lines.join("")}</ul>` : `<p class="note">${t("pass_none")}</p>`}</div></div>`);
  }
}

// Water temperature --------------------------------------------------------------
function lastTemp(name) {
  const rows = TEMP.filter((r) => r.reservoir === name && r.frac_valid >= RELIABLE && r.temp_p50 != null);
  return rows[rows.length - 1];
}
function renderTemp() {
  const c = colors(), box = $("charts-temp");
  box.innerHTML = "";
  if (!TEMP.length) return;
  const names = state.res === "all" ? RESERVOIRS : [state.res];
  for (const name of names) {
    const d = TEMP.filter((r) => r.reservoir === name && r.frac_valid >= RELIABLE &&
      (!state.from || r.date >= state.from) && (!state.to || r.date <= state.to));
    const x = d.map((r) => r.date);
    const lay = baseLayout(c, name, t("temp_axis"));
    lay.xaxis.type = "date";
    const div = document.createElement("div");
    div.className = "chart";
    box.appendChild(div);
    Plotly.newPlot(div, [
      { x, y: d.map((r) => r.temp_p90), type: "scatter", mode: "lines", line: { width: 0 },
        showlegend: false, hoverinfo: "skip" },
      { x, y: d.map((r) => r.temp_p10), type: "scatter", mode: "lines", line: { width: 0 },
        fill: "tonexty", fillcolor: c.tempBand, name: t("temp_range"), hoverinfo: "skip" },
      { x, y: d.map((r) => r.temp_p50), type: "scatter", mode: "lines+markers", name: t("temp_typ"),
        line: { color: c.temp, width: 1 }, marker: { size: 5, color: c.temp },
        customdata: d.map((r) => [r.temp_p10, r.temp_p90, Math.round(100 * r.frac_valid), r.spacecraft]),
        hovertemplate: `%{x|%d %b %Y}<br>%{y:.1f} °C (%{customdata[0]:.1f}–%{customdata[1]:.1f})<br>` +
          `%{customdata[2]} % ${t("visible")} · %{customdata[3]}<extra></extra>` },
    ], lay, cfg);
  }
}

// Setup --------------------------------------------------------------------------
function initSampling() {
  loadPoints();
  const vboxes = [...document.querySelectorAll("#viewer .zoombox")];
  VIEWZOOM = new ZoomGroup(vboxes, $("v-tools"),
    () => state.view && { res: state.view.res, from: t("p_from_image", { d: state.view.date }) });
  MAPZOOM = new ZoomGroup([document.querySelector("#maps .zoombox")], $("m-tools"),
    () => ({ res: mapState.res, from: t(mapState.kind === "freq" ? "map_freq" : "map_mean") }));
  $("m-res").addEventListener("change", (e) => { mapState.res = e.target.value; MAPZOOM.reset(); renderMaps(); });
  document.querySelectorAll("[data-map]").forEach((b) => b.addEventListener("click", () => {
    mapState.kind = b.dataset.map; renderMaps();
  }));
  for (const img of document.querySelectorAll(".zoombox img")) img.addEventListener("load", refreshMarkers);
  wirePoints();
}
function renderSampling() {
  VIEWZOOM?.labels(); MAPZOOM?.labels();
  renderPasses(); renderMaps(); renderTemp(); renderPoints();
}
