# Monitor de embalses Sentinel-2 · Sentinel-2 reservoir monitor

**Valdesia y Hatillo, República Dominicana.** NDCI (índice de clorofila) desde Sentinel-2,
actualizado automáticamente cada día. · *NDCI (chlorophyll index) from Sentinel-2, updated
automatically every day.*

- **Dashboard:** https://kristofm854.github.io/embalses-s2-monitor/
- **Datos / Data:** [`data/reservoir_ndci.csv`](data/reservoir_ndci.csv) ·
  [`data/reservoir_ndci.xlsx`](data/reservoir_ndci.xlsx)

[Español](#español) · [English](#english)

---

## Español

### Qué hace
Cada día, GitHub Actions consulta Google Earth Engine para ver si hay imágenes nuevas de
Sentinel-2 sobre los dos embalses. Para cada fecha calcula estadísticas de NDCI sobre el
agua sin nubes, genera dos imágenes (color verdadero y NDCI) y publica todo en el dashboard.
Nadie tiene que hacer nada para que funcione.

### Uso del dashboard
- **Tarjetas arriba:** la última observación útil (≥ 50 % sin nubes) de cada embalse y
  cómo se compara con todo el historial.
- **Filtros:** embalse, fechas, mínimo de cielo despejado, umbral de NDCI p90.
  "Solo fechas ≥ umbral" deja solo los eventos altos.
- **Clic** en un punto del gráfico o en una fila de la tabla abre las imágenes de esa fecha.
  Use ◀ ▶ (o las flechas del teclado) para pasar a la fecha anterior o siguiente.
- **Descargas:** la tabla completa en CSV o Excel (botones arriba), o solo la selección
  filtrada ("Descargar selección").
- El enlace en la barra del navegador guarda los filtros y la imagen abierta: se puede
  copiar y enviar a otra persona.

### Columnas de la tabla
| Columna | Significado |
|---|---|
| `date` | Fecha de adquisición (UTC, ~15:00) |
| `ndci_p50`, `ndci_p90`, `ndci_mean` | Mediana, percentil 90 y promedio de NDCI en el agua despejada |
| `frac_ndci_gt_0.1`, `frac_ndci_gt_0.2` | Fracción de píxeles con NDCI > 0.1 / > 0.2 |
| `b4_p50` | Reflectancia roja (sube con sedimento) |
| `b8_p50`, `frac_high_nir` | Reflectancia NIR; fracción con B8 > 0.05 (nata de algas, plantas, reflejo, neblina) |
| `n_valid`, `n_total`, `frac_valid` | Píxeles de agua despejados / totales (20 m) |
| `scene` | ID de la imagen en Earth Engine |

La hoja "README" del Excel repite estas descripciones.

### Cómo interpretar
NDCI es un **indicador relativo** de floraciones, no una medición de clorofila-a. La
corrección atmosférica (Sen2Cor) está hecha para tierra; no hay calibración local. Compare
cada embalse consigo mismo en el tiempo. Si B4 sube junto con NDCI después de lluvias,
probablemente es sedimento. Con menos de ~50 % sin nubes, los valores son menos fiables.

### Si algo falla
GitHub envía un correo al dueño del repositorio cuando falla una actualización.
1. Vaya a la pestaña **Actions** → "Update data" → abra la ejecución en rojo.
2. Errores típicos:
   - *"Secret EE_SERVICE_ACCOUNT_KEY is missing"* o *"permission denied"*: la clave de la
     cuenta de servicio falta o fue revocada. Ver [docs/SETUP.md](docs/SETUP.md).
   - Errores de Earth Engine (*"Too many concurrent aggregations"*, *"Computation timed
     out"*): normalmente temporales. Pulse **Re-run jobs**; si no, se resuelve en la
     ejecución del día siguiente.
3. Los datos ya publicados no se pierden si una actualización falla.
4. GitHub desactiva las tareas programadas después de 60 días sin actividad en el
   repositorio. Si el dashboard deja de actualizarse: Actions → "Update data" →
   **Enable workflow**.

### Ejecutar a mano
Actions → "Update data" → **Run workflow**. "full_rebuild" vuelve a calcular todo desde
2017 (solo necesario si se cambia `pipeline/config.py`).

---

## English

### What it does
A daily GitHub Action queries Google Earth Engine for new Sentinel-2 L2A scenes over both
reservoirs. For each date it computes NDCI statistics over clear water (Cloud Score+),
renders a true-colour and an NDCI image, commits them, and redeploys the static dashboard
on GitHub Pages. No server, no database, no cost.

### Repository layout
```
pipeline/        Python: Earth Engine queries (gee.py), table handling (store.py),
                 settings (config.py), entry point (update.py)
dashboard/       static site (HTML/JS/CSS, Plotly vendored, ES/EN text in i18n.js)
data/            published outputs: CSV, XLSX, JSON for the dashboard, reservoir outlines
images/          <reservoir>/<date>_rgb.webp and _ndci.webp
analysis/        R script for exploring the CSV (no Earth Engine needed)
tests/           unit tests for the table logic
.github/workflows/
  update.yml     daily fetch + commit + deploy
  deploy.yml     publish dashboard + data + images to GitHub Pages
  tests.yml      unit tests
docs/SETUP.md    one-time setup: service account, secret, Pages, first backfill
```

### Method
- **Data:** `COPERNICUS/S2_SR_HARMONIZED` (L2A, Sen2Cor; the processing-baseline 04.00
  offset is already removed in this collection).
- **Clouds:** `GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED`, pixels kept at `cs_cdf ≥ 0.6`.
- **Outline:** largest JRC Global Surface Water body (occurrence ≥ 80 %) near each dam,
  buffered 60 m inward to avoid mixed shore pixels. Cached in `data/aoi_*.geojson`, so
  `n_total` is fixed; open these files in QGIS to check them.
- **Statistics:** at 20 m in UTM 19N: NDCI = (B5 − B4)/(B5 + B4) percentiles, mean and
  threshold fractions; B4 and B8 medians; NIR flag. If both granules of a day cover the
  reservoir, the one with more clear pixels is kept.
- **Incremental:** each run re-queries the last 45 days to pick up late or reprocessed
  scenes, and replaces those rows.
- **Images:** rendered for dates with ≥ 30 % clear water, newest first, at most
  `max_images` per run, so the first backfill spreads over a few days unless you raise it.
- **Coverage:** L2A in Earth Engine is sparse before late 2018 for this region. The series
  starts wherever usable L2A exists. See `data/meta.json` for the actual first dates.

### Run locally
```bash
pip install -r requirements.txt
python -m pipeline.update --project hab-quiz-ae5a8 --max-images 20   # browser login on first use
python -m pytest -q
cd dashboard && ln -s ../data data && ln -s ../images images && python -m http.server
```

### Known limitations / possible next steps
- NDCI from Sen2Cor over small, turbid reservoirs is relative only. A water-specific
  atmospheric correction (ACOLITE) and in-situ chl-a would turn it into a calibrated product.
- Valdesia is narrow; at 20 m some arms have few pure-water pixels after the shore buffer.
- The service-account key is long-lived. Workload Identity Federation would avoid storing
  a key (see docs/SETUP.md).
