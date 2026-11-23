# Monitor de embalses Sentinel-2 · Sentinel-2 reservoir monitor

**Valdesia y Hatillo, República Dominicana · Dominican Republic.** Índice de clorofila (NDCI) de
Sentinel-2 y temperatura del agua de Landsat, actualizados cada dos horas. · *Chlorophyll index (NDCI)
from Sentinel-2 and water temperature from Landsat, updated every two hours.*

- **Panel / Dashboard:** https://kristofm854.github.io/embalses-s2-monitor/
- **Datos / Data:** [`data/reservoir_ndci.xlsx`](data/reservoir_ndci.xlsx) ·
  [`data/reservoir_ndci.csv`](data/reservoir_ndci.csv)

[Español](#español) · [English](#english)

---

## Español

### Qué hace
Cada dos horas, GitHub Actions consulta Google Earth Engine para ver si hay imágenes nuevas de
Sentinel-2 y Landsat sobre los dos embalses. Para cada imagen Sentinel-2 calcula un índice de
clorofila (NDCI) sobre el agua sin nubes y genera dos imágenes (foto en color real y mapa de
clorofila); de Landsat calcula la temperatura de la superficie del agua. Una vez al mes genera
mapas de dónde suele haber más algas, y en cada ejecución calcula los próximos pasos de los
satélites. Todo se publica en el panel. Si no hay nada nuevo, no se cambia nada. Nadie tiene que
hacer nada para que funcione. Una imagen nueva suele aparecer en el panel en menos de un día.

### Uso del panel
1. **Situación actual:** la última imagen útil (al menos 50 % del embalse sin nubes) de cada
   embalse, con su nivel: Bajo, Medio, Elevado o Muy alto. El nivel compara la imagen con todas
   las imágenes anteriores del mismo embalse.
2. **Próximos pasos del satélite:** los días en que Sentinel-2 y Landsat pasarán sobre cada embalse.
3. **¿En qué meses suele haber más algas?:** valor típico por mes. Sirve para decidir cuándo muestrear.
4. **¿Dónde suele haber más algas?:** dos mapas de todas las imágenes desde 2019: con qué frecuencia
   cada punto está verde, y su valor típico. Sirven para elegir puntos de muestreo.
5. **Historial:** cada punto es una imagen. Filtros: embalse, período, solo niveles altos, solo
   fechas con imagen. Haga clic en un punto para ver las imágenes de ese día; ◀ ▶ (o las flechas
   del teclado) pasan a la fecha anterior o siguiente.
6. **Temperatura del agua (Landsat):** temperatura de la superficie, una imagen cada 8 días.
7. **Lista de fechas:** todas las fechas con nivel y avisos (nubes, sedimento, superficie).
8. **Mis puntos de muestreo:** puntos marcados en las imágenes o mapas, para descargar como GPX
   (GPS, teléfono) o CSV.
9. **Descargar datos:** Excel (recomendado), CSV de clorofila y de temperatura, la selección
   filtrada y los contornos (GeoJSON).
10. **¿Cómo funciona?:** explicación sencilla de lo que miden los satélites, qué puede engañarlos,
   qué no pueden decir y cómo usar los datos para planificar el muestreo.

En las imágenes y los mapas: **+ / −** o Ctrl + rueda del ratón (dos dedos en el teléfono) para
acercar, arrastrar para moverse. Al pasar el ratón se ven las coordenadas (latitud, longitud).
Con **"Marcar puntos"** activado, un clic guarda el punto.

El enlace en la barra del navegador guarda los filtros y la imagen abierta: se puede copiar y
enviar a otra persona.

### Columnas de la tabla
| Columna | Unidad | Significado |
|---|---|---|
| `reservoir` | - | Nombre del embalse. |
| `date` | YYYY-MM-DD | Fecha de la imagen Sentinel-2 (UTC). El satélite pasa a las 15:15 UTC aprox. (11:15 hora local). Use esta fecha para comparar con muestras de campo del mismo día. |
| `ndci_p50` | index (-1 to 1) | Mediana del NDCI sobre el agua sin nubes del embalse. NDCI = (B5 - B4) / (B5 + B4), reflectancia del borde rojo (705 nm) frente al rojo (665 nm). Nivel típico de clorofila del embalse en conjunto. Más alto = agua más verde. |
| `ndci_p90` | index (-1 to 1) | Percentil 90 del NDCI: valor que supera el 10 % más verde del agua. Clorofila en las zonas más verdes. Reacciona a floraciones que cubren solo una parte del embalse. |
| `ndci_mean` | index (-1 to 1) | Promedio del NDCI sobre el agua sin nubes. Parecido a la mediana, pero más afectado por pocos píxeles extremos. |
| `frac_ndci_gt_0.1` | fraction (0 to 1) | Fracción del agua sin nubes con NDCI > 0,1. Cuánto del embalse está claramente verde. 0,3 = 30 % de la superficie. |
| `frac_ndci_gt_0.2` | fraction (0 to 1) | Fracción del agua sin nubes con NDCI > 0,2. Cuánto del embalse está muy verde. |
| `b4_p50` | reflectance (0 to 1) | Mediana de la reflectancia roja (banda B4 de Sentinel-2, 665 nm). Sube con barro o sedimento en el agua. Si está alta junto con el NDCI, el NDCI puede deberse a sedimento y no a algas. |
| `b8_p50` | reflectance (0 to 1) | Mediana de la reflectancia del infrarrojo cercano (banda B8, 842 nm). El agua limpia es oscura en el infrarrojo cercano (cerca de 0). |
| `frac_high_nir` | fraction (0 to 1) | Fracción del agua sin nubes con reflectancia infrarroja mayor que 0,05. El agua no debería ser brillante en el infrarrojo. Los píxeles brillantes son nata de algas, plantas flotantes (p. ej. jacinto de agua), reflejo del sol o neblina. Revise la imagen. |
| `n_valid` | pixels (20 m) | Número de píxeles de agua sin nubes usados. |
| `n_total` | pixels (20 m) | Número de píxeles de agua dentro del contorno del embalse. |
| `frac_valid` | fraction (0 to 1) | Fracción del embalse sin nubes (n_valid / n_total). Por debajo de 0,5 (la mitad del embalse cubierta por nubes), use los valores con cautela. |
| `scene` | - | Identificador de la imagen Sentinel-2 en Google Earth Engine. |

**Temperatura del agua** (`landsat_temperature.csv`, hoja "Temperatura · Temperature" del Excel):

| Columna | Unidad | Significado |
|---|---|---|
| `reservoir` | - | Nombre del embalse. |
| `date` | YYYY-MM-DD | Fecha de la imagen Landsat (UTC). Landsat pasa a las 15:00 UTC aprox. (11:00 hora local). |
| `temp_p10` | °C | Percentil 10 de la temperatura de la superficie del agua (zonas más frías). |
| `temp_p50` | °C | Mediana de la temperatura de la superficie del agua. Temperatura de los primeros milímetros del agua ('piel'), exactitud de 1 a 2 °C aprox. El agua cálida favorece las floraciones de algas y cianobacterias. |
| `temp_p90` | °C | Percentil 90 de la temperatura de la superficie del agua (zonas más cálidas). |
| `n_valid` | pixels (30 m) | Número de píxeles de agua sin nubes usados. |
| `n_total` | pixels (30 m) | Número de píxeles de agua en el contorno de temperatura (120 m dentro de la orilla, porque la banda térmica es de 100 m y si no mezclaría tierra caliente). |
| `frac_valid` | fraction (0 to 1) | Fracción sin nubes del contorno de temperatura. Por debajo de 0,5, use los valores con cautela. |
| `spacecraft` | - | LANDSAT_8 o LANDSAT_9. |
| `scene` | - | Identificador del producto Landsat. |

Las mismas descripciones están en la hoja "Metadatos · Metadata" del Excel y en las primeras
líneas del CSV (las que empiezan con `#`). Para leer el CSV: en R
`read.csv("reservoir_ndci.csv", comment.char = "#")`, en Python
`pandas.read_csv("reservoir_ndci.csv", comment="#")`. En Excel es más fácil abrir el archivo `.xlsx`.

### Cómo interpretar
- NDCI es un **indicador relativo** de algas, no una medición de clorofila-a. La corrección
  atmosférica (Sen2Cor) está hecha para tierra y no hay calibración local. Compare cada embalse
  consigo mismo en el tiempo.
- **Sedimento:** si la reflectancia roja (`b4_p50`) sube junto con el NDCI después de lluvias,
  probablemente es barro y no algas.
- **Superficie brillante** (`frac_high_nir`): nata de algas, plantas flotantes, reflejo del sol o
  neblina. Revise la imagen.
- Con menos de ~50 % del embalse sin nubes (`frac_valid` < 0,5) los valores son poco fiables.
- El satélite no distingue cianobacterias de otras algas ni mide toxinas.

### Corregir el contorno de un embalse
El contorno en uso está en `data/aoi_Valdesia.geojson` y `data/aoi_Hatillo.geojson` (GitHub lo
muestra en un mapa). Si no es correcto, dibuje uno a mano: ver
[data/aoi_overrides/README.md](data/aoi_overrides/README.md).

### Si algo falla
GitHub envía un correo al dueño del repositorio cuando falla una actualización.
1. Vaya a la pestaña **Actions** → "Update data" → abra la ejecución en rojo.
2. Errores típicos:
   - *"Secret EE_SERVICE_ACCOUNT_KEY is missing"* o *"permission denied"*: la clave de la cuenta
     de servicio falta, fue revocada o le falta un permiso. Ver [docs/SETUP.md](docs/SETUP.md).
   - Errores de Earth Engine (*"Too many concurrent aggregations"*, *"Computation timed out"*,
     *"503 Service Unavailable"*): normalmente temporales. Pulse **Re-run jobs**; si no, se
     resuelve en la ejecución del día siguiente.
3. Los datos ya publicados no se pierden si una actualización falla.
4. GitHub desactiva las tareas programadas después de 60 días sin actividad en el repositorio.
   Si el panel deja de actualizarse: Actions → "Update data" → **Enable workflow**.

### Ejecutar a mano
Actions → "Update data" → **Run workflow**. "full_rebuild" vuelve a calcular todo desde 2017
(normalmente no hace falta: un cambio de contorno ya lo hace automáticamente). "max_images"
limita cuántas imágenes se generan en una ejecución.

### Para personas técnicas
**Estructura del repositorio**
```
pipeline/        Python: consultas a Earth Engine (gee.py), tablas (store.py),
                 descripción de columnas (metadata.py), cuadrícula de las imágenes (grid.py),
                 ajustes (config.py), inicio (update.py)
dashboard/       panel estático (HTML/JS/CSS, Plotly incluido, textos ES/EN en i18n.js)
data/            resultados: CSV, XLSX, JSON para el panel, contornos de los embalses
images/          <embalse>/<fecha>_rgb.webp y _ndci.webp; maps/<embalse>_freq.webp y _mean.webp
analysis/        script de R para explorar el CSV (no necesita Earth Engine)
tests/           pruebas automáticas
.github/workflows/
  update.yml     consulta cada dos horas + guardar + publicar (solo si hay algo nuevo)
  deploy.yml     publica panel, datos e imágenes en GitHub Pages
  tests.yml      pruebas automáticas
docs/SETUP.md    configuración inicial: cuenta de servicio, secreto, Pages, primera ejecución
```

**Método**
- **Datos:** `COPERNICUS/S2_SR_HARMONIZED` (L2A, Sen2Cor; el desfase de la versión de
  procesamiento 04.00 ya está corregido en esta colección).
- **Nubes:** `GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED`, se usan píxeles con `cs_cdf ≥ 0,6`.
- **Contorno:** de Sentinel-2. Para 2019–2025 se calcula en cuántas imágenes despejadas cada píxel
  es agua (MNDWI = (B3 − B11)/(B3 + B11) > 0). Los píxeles que son agua en ≥ 75 % de ellas forman
  el embalse, trazado a 10 m y reducido 20 m desde la orilla. Se guarda en `data/aoi_*.geojson`.
  Un contorno dibujado a mano en `data/aoi_overrides/` lo reemplaza. Si cambian los ajustes del
  contorno, la siguiente ejecución recalcula el contorno y toda la serie automáticamente.
- **Estadísticas:** a 20 m en UTM 19N: percentiles, promedio y fracciones de NDCI = (B5 − B4)/(B5 + B4);
  medianas de B4 y B8; indicador NIR. Un píxel cuenta si su centro está dentro del contorno.
  Si dos imágenes del mismo día cubren el embalse, se usa la que tiene más píxeles despejados.
- **Actualización:** cada ejecución vuelve a consultar los últimos 45 días para incluir imágenes
  tardías o reprocesadas.
- **Imágenes:** para fechas con ≥ 30 % de agua despejada, primero las más recientes.
- **Niveles del panel:** percentiles 50, 75 y 90 de `ndci_p90` de las fechas útiles del mismo embalse.
- **Cuadrícula de las imágenes:** todas las imágenes de un embalse comparten una cuadrícula UTM 19N
  exacta (`data/image_grid.json`, de 10 a 15 m por píxel), por eso el panel puede mostrar coordenadas.
- **Mapas resumen:** de las imágenes Sentinel-2 útiles (≥ 50 % sin nubes) desde 2019: fracción de
  observaciones despejadas con NDCI > 0,1 por píxel, y NDCI promedio por píxel (escala de los percentiles
  2 a 98 del embalse), sobre una mediana sin nubes del último año. Se renuevan cada 30 días (`data/maps.json`).
- **Temperatura:** Landsat 8/9 Colección 2 Nivel 2, banda ST_B10 (K × 0,00341802 + 149,0 − 273,15),
  píxeles sin nubes, sombra ni cirros según QA_PIXEL, a 30 m, en el contorno reducido otros 100 m.
- **Próximos pasos:** fechas de adquisición de cada satélite en los últimos 48 días (con o sin nubes),
  repetidas cada 10 días (Sentinel-2) o 16 días (Landsat) (`data/passes.json`).

**Ejecutar en una computadora**
```bash
pip install -r requirements.txt
python -m pipeline.update --project hab-quiz-ae5a8 --max-images 20   # inicio de sesión en el navegador la primera vez
python -m pytest -q
cd dashboard && ln -s ../data data && ln -s ../images images && python -m http.server
```

**Limitaciones y próximos pasos**
- El NDCI de Sen2Cor sobre embalses pequeños y turbios es solo relativo. Una corrección atmosférica
  para agua (ACOLITE) y muestras de clorofila-a del mismo día lo convertirían en un producto calibrado.
- El contorno es fijo. Cuando baja el nivel del agua, la orilla expuesta dentro del contorno cuenta
  como agua sin nubes con NDCI bajo y B4/B8 altos.
- La clave de la cuenta de servicio es de larga duración. Workload Identity Federation evitaría
  guardar una clave (ver docs/SETUP.md).

---

## English

### What it does
Every two hours, GitHub Actions asks Google Earth Engine whether there are new Sentinel-2 and
Landsat images of the two reservoirs. For each Sentinel-2 image it computes a chlorophyll index
(NDCI) over the cloud-free water and renders two images (true-colour photo and chlorophyll map);
from Landsat it computes the water surface temperature. Once a month it renders maps of where
there are usually more algae, and every run predicts the next satellite passes. Everything is
published on the dashboard. If nothing is new, nothing changes. Nobody has to do anything to keep
it running. A new image usually appears on the dashboard within a day.

### Using the dashboard
1. **Current situation:** the latest usable image (at least 50 % of the reservoir cloud-free) of
   each reservoir, with its level: Low, Medium, Elevated or Very high. The level compares the image
   with all earlier images of the same reservoir.
2. **Upcoming satellite passes:** the days when Sentinel-2 and Landsat will pass over each reservoir.
3. **In which months are there usually more algae?:** typical value per month. Helps decide when to sample.
4. **Where are there usually more algae?:** two maps from all images since 2019: how often each
   point is green, and its typical value. Help choose sampling points.
5. **History:** each point is an image. Filters: reservoir, period, only high levels, only dates
   with an image. Click a point to see the images of that day; ◀ ▶ (or the arrow keys) go to the
   previous or next date.
6. **Water temperature (Landsat):** surface temperature, one image every 8 days.
7. **List of dates:** all dates with level and warnings (clouds, sediment, surface).
8. **My sampling points:** points marked on the images or maps, to download as GPX (GPS, phone)
   or CSV.
9. **Download data:** Excel (recommended), chlorophyll and temperature CSV, the filtered selection
   and the outlines (GeoJSON).
10. **How does it work?:** a simple explanation of what the satellites measure, what can mislead
   them, what they cannot tell and how to use the data to plan sampling.

On the images and maps: **+ / −** or Ctrl + mouse wheel (two fingers on a phone) to zoom, drag to
move. Moving the mouse shows the coordinates (latitude, longitude). With **"Mark points"** switched
on, a click saves the point.

The link in the browser bar keeps the filters and the open image: it can be copied and sent to
someone else.

### Table columns
| Column | Unit | Meaning |
|---|---|---|
| `reservoir` | - | Reservoir name. |
| `date` | YYYY-MM-DD | Date of the Sentinel-2 image (UTC). The satellite passes at about 15:15 UTC (11:15 local time). Use this date to compare with field samples taken the same day. |
| `ndci_p50` | index (-1 to 1) | Median NDCI over the cloud-free water of the reservoir. NDCI = (B5 - B4) / (B5 + B4), red-edge (705 nm) versus red (665 nm) reflectance. Typical chlorophyll level of the reservoir as a whole. Higher = greener water. |
| `ndci_p90` | index (-1 to 1) | 90th percentile of NDCI: the value exceeded by the greenest 10 % of the water. Chlorophyll in the greenest parts. Reacts to blooms that cover only part of the reservoir. |
| `ndci_mean` | index (-1 to 1) | Mean NDCI over the cloud-free water. Similar to the median, but more affected by a few extreme pixels. |
| `frac_ndci_gt_0.1` | fraction (0 to 1) | Share of the cloud-free water with NDCI > 0.1. How much of the reservoir is clearly green. 0.3 = 30 % of the surface. |
| `frac_ndci_gt_0.2` | fraction (0 to 1) | Share of the cloud-free water with NDCI > 0.2. How much of the reservoir is very green. |
| `b4_p50` | reflectance (0 to 1) | Median red reflectance (Sentinel-2 band B4, 665 nm). Rises with mud or sediment in the water. If it is high together with NDCI, the NDCI may be raised by sediment, not algae. |
| `b8_p50` | reflectance (0 to 1) | Median near-infrared reflectance (band B8, 842 nm). Clear water is dark in near-infrared (close to 0). |
| `frac_high_nir` | fraction (0 to 1) | Share of the cloud-free water with near-infrared reflectance above 0.05. Water should not be bright in near-infrared. Bright pixels are surface scum, floating plants (e.g. water hyacinth), sun glint or haze. Check the image. |
| `n_valid` | pixels (20 m) | Number of cloud-free water pixels used. |
| `n_total` | pixels (20 m) | Number of water pixels in the reservoir outline. |
| `frac_valid` | fraction (0 to 1) | Cloud-free share of the reservoir (n_valid / n_total). Below 0.5 (half the reservoir hidden by clouds), treat the values with caution. |
| `scene` | - | Identifier of the Sentinel-2 image in Google Earth Engine. |

**Water temperature** (`landsat_temperature.csv`, sheet "Temperatura · Temperature" of the Excel file):

| Column | Unit | Meaning |
|---|---|---|
| `reservoir` | - | Reservoir name. |
| `date` | YYYY-MM-DD | Date of the Landsat image (UTC). Landsat passes at about 15:00 UTC (11:00 local time). |
| `temp_p10` | °C | 10th percentile of the water surface temperature (cooler parts). |
| `temp_p50` | °C | Median water surface temperature. Temperature of the top millimetres of the water ('skin'), accuracy about 1 to 2 °C. Warm water favours algal and cyanobacterial blooms. |
| `temp_p90` | °C | 90th percentile of the water surface temperature (warmer parts). |
| `n_valid` | pixels (30 m) | Number of cloud-free water pixels used. |
| `n_total` | pixels (30 m) | Number of water pixels in the temperature outline (120 m inside the shore, because the thermal band is 100 m and would otherwise mix in warm land). |
| `frac_valid` | fraction (0 to 1) | Cloud-free share of the temperature outline. Below 0.5, treat the values with caution. |
| `spacecraft` | - | LANDSAT_8 or LANDSAT_9. |
| `scene` | - | Landsat product identifier. |

The same descriptions are in the "Metadatos · Metadata" sheet of the Excel file and in the first
lines of the CSV (those starting with `#`). To read the CSV: in R
`read.csv("reservoir_ndci.csv", comment.char = "#")`, in Python
`pandas.read_csv("reservoir_ndci.csv", comment="#")`. In Excel it is easier to open the `.xlsx` file.

### How to interpret
- NDCI is a **relative indicator** of algae, not a chlorophyll-a measurement. The atmospheric
  correction (Sen2Cor) is made for land and there is no local calibration. Compare each reservoir
  with itself over time.
- **Sediment:** if red reflectance (`b4_p50`) rises together with NDCI after rain, it is probably
  mud, not algae.
- **Bright surface** (`frac_high_nir`): algal scum, floating plants, sun glint or haze. Check the image.
- With less than ~50 % of the reservoir cloud-free (`frac_valid` < 0.5) values are not reliable.
- The satellite cannot tell cyanobacteria from other algae and does not measure toxins.

### Fixing a reservoir outline
The outline in use is in `data/aoi_Valdesia.geojson` and `data/aoi_Hatillo.geojson` (GitHub shows
it on a map). If it is wrong, draw one by hand: see
[data/aoi_overrides/README.md](data/aoi_overrides/README.md).

### If something fails
GitHub e-mails the repository owner when an update fails.
1. Go to the **Actions** tab → "Update data" → open the red run.
2. Typical errors:
   - *"Secret EE_SERVICE_ACCOUNT_KEY is missing"* or *"permission denied"*: the service-account key
     is missing, was revoked or lacks a permission. See [docs/SETUP.md](docs/SETUP.md).
   - Earth Engine errors (*"Too many concurrent aggregations"*, *"Computation timed out"*,
     *"503 Service Unavailable"*): usually temporary. Click **Re-run jobs**; otherwise the next
     day's run fixes it.
3. Data already published is not lost when an update fails.
4. GitHub disables scheduled workflows after 60 days without activity in the repository. If the
   dashboard stops updating: Actions → "Update data" → **Enable workflow**.

### Run manually
Actions → "Update data" → **Run workflow**. "full_rebuild" recomputes everything since 2017
(normally not needed: an outline change does this automatically). "max_images" limits how many
images are rendered in one run.

### For technical users
**Repository layout**
```
pipeline/        Python: Earth Engine queries (gee.py), tables (store.py),
                 column descriptions (metadata.py), image grid (grid.py),
                 settings (config.py), entry point (update.py)
dashboard/       static dashboard (HTML/JS/CSS, Plotly bundled, ES/EN text in i18n.js)
data/            outputs: CSV, XLSX, JSON for the dashboard, reservoir outlines
images/          <reservoir>/<date>_rgb.webp and _ndci.webp; maps/<reservoir>_freq.webp and _mean.webp
analysis/        R script for exploring the CSV (no Earth Engine needed)
tests/           automated tests
.github/workflows/
  update.yml     query every two hours + commit + publish (only when something is new)
  deploy.yml     publishes dashboard, data and images to GitHub Pages
  tests.yml      automated tests
docs/SETUP.md    one-time setup: service account, secret, Pages, first run
```

**Method**
- **Data:** `COPERNICUS/S2_SR_HARMONIZED` (L2A, Sen2Cor; the processing-baseline 04.00 offset is
  already removed in this collection).
- **Clouds:** `GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED`, pixels with `cs_cdf ≥ 0.6` are used.
- **Outline:** from Sentinel-2. For 2019–2025, the share of clear images in which each pixel is
  water (MNDWI = (B3 − B11)/(B3 + B11) > 0) is computed. Pixels that are water in ≥ 75 % of them
  form the reservoir, traced at 10 m and shrunk 20 m from the shore. Stored in `data/aoi_*.geojson`.
  A hand-drawn outline in `data/aoi_overrides/` replaces it. If the outline settings change, the
  next run rebuilds the outline and recomputes the whole series automatically.
- **Statistics:** at 20 m in UTM 19N: percentiles, mean and fractions of NDCI = (B5 − B4)/(B5 + B4);
  B4 and B8 medians; NIR flag. A pixel counts if its centre is inside the outline. If two images of
  the same day cover the reservoir, the one with more clear pixels is used.
- **Updates:** each run re-queries the last 45 days to include late or reprocessed images.
- **Images:** for dates with ≥ 30 % clear water, newest first.
- **Dashboard levels:** 50th, 75th and 90th percentiles of `ndci_p90` over the usable dates of the
  same reservoir.
- **Image grid:** all images of a reservoir share one exact UTM 19N grid (`data/image_grid.json`,
  10 to 15 m per pixel), so the dashboard can show coordinates.
- **Summary maps:** from the usable Sentinel-2 images (≥ 50 % cloud-free) since 2019: per pixel, the
  share of clear observations with NDCI > 0.1, and the mean NDCI (scaled to the reservoir's 2nd to
  98th percentile), over a cloud-free median of the last year. Renewed every 30 days (`data/maps.json`).
- **Temperature:** Landsat 8/9 Collection 2 Level 2, band ST_B10 (K × 0.00341802 + 149.0 − 273.15),
  pixels free of cloud, shadow and cirrus per QA_PIXEL, at 30 m, in the outline shrunk a further 100 m.
- **Upcoming passes:** acquisition dates of each spacecraft in the last 48 days (cloudy or not),
  repeated every 10 days (Sentinel-2) or 16 days (Landsat) (`data/passes.json`).

**Run on a computer**
```bash
pip install -r requirements.txt
python -m pipeline.update --project hab-quiz-ae5a8 --max-images 20   # browser login on first use
python -m pytest -q
cd dashboard && ln -s ../data data && ln -s ../images images && python -m http.server
```

**Limitations and next steps**
- NDCI from Sen2Cor over small, turbid reservoirs is relative only. A water-specific atmospheric
  correction (ACOLITE) and same-day chlorophyll-a samples would turn it into a calibrated product.
- The outline is fixed. When the water level drops, exposed shore inside the outline counts as
  cloud-free water with low NDCI and high B4/B8.
- The service-account key is long-lived. Workload Identity Federation would avoid storing a key
  (see docs/SETUP.md).
