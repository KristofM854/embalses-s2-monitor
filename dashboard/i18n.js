// All visible text, Spanish and English. Keep both languages in step.
const I18N = {
  es: {
    title: "Embalses Valdesia y Hatillo: clorofila vista desde el satélite",
    updated: "Actualizado:",
    source_short: "imágenes Sentinel-2 (Copernicus, ESA)",
    nav_download: "Descargar datos", nav_how: "¿Cómo funciona?", lang: "English",
    lead: `Esta página muestra <b>qué tan verde está el agua</b> de los embalses en imágenes de satélite.
      Agua más verde suele significar <b>más algas</b> (más clorofila). Sirve para ver cuándo y dónde
      hay más algas y para <b>planificar el muestreo</b>. No reemplaza los análisis de laboratorio.
      <a href="#como-funciona">¿Cómo funciona?</a>`,

    h_now: "1. Situación actual",
    now_help: "La última imagen útil de cada embalse (al menos la mitad del embalse sin nubes). El nivel compara esa imagen con todas las imágenes anteriores del mismo embalse.",
    last_image: "Última imagen útil", days_ago: "hace {n} días", today: "hoy", yesterday: "ayer",
    visible: "visible",
    card_sentence: "Las zonas más verdes del embalse están más verdes que en el {p} % de las imágenes anteriores.",
    see_images: "Ver imágenes de este día",
    no_recent: "No hay imágenes útiles recientes.",

    lvl_1: "Bajo", lvl_2: "Medio", lvl_3: "Elevado", lvl_4: "Muy alto",
    lvl_1_long: "menos verde que en la mitad de las imágenes",
    lvl_2_long: "dentro de lo normal para este embalse",
    lvl_3_long: "entre el 25 % más verde de las imágenes",
    lvl_4_long: "entre el 10 % más verde de las imágenes",

    note_clouds: "Muchas nubes: solo se ve el {p} % del embalse. Valor poco fiable.",
    note_sediment: "Agua turbia (sedimento): el valor puede estar alto por barro y no por algas.",
    note_surface: "Superficie brillante en infrarrojo en el {p} % del agua: puede ser nata de algas, plantas flotantes (jacinto de agua), reflejo del sol o neblina. Revise la foto.",

    prev: "◀ Anterior", next: "Siguiente ▶", close: "Cerrar",
    cap_rgb: "Foto del satélite (colores reales)",
    cap_ndci: "Mapa de clorofila sobre el agua. Sin color = nubes, sombra o fuera del área analizada.",
    noimg: "No hay imagen para esta fecha (demasiadas nubes o aún no generada).",
    leg_low: "poca clorofila", leg_mid: "moderada", leg_high: "mucha clorofila",
    leg_note: "Azul = agua clara · verde = algo de algas · amarillo y rojo = mucha clorofila.",
    leg_numbers: "Valores del índice y clorofila aproximada",
    leg_numbers_note: "Arriba: valor del índice NDCI. Abajo: clorofila-a aproximada en µg/L según una fórmula publicada para otros lagos (Mishra & Mishra 2012). No está calibrada para estos embalses: úsela solo como orden de magnitud.",
    tech_values: "Valores técnicos de esta fecha",
    v_summary: "Nivel {lvl}: {long}. {vis} % del embalse visible.",

    h_season: "2. ¿En qué meses suele haber más algas?",
    season_help: "Valor típico de las zonas más verdes en cada mes, de todas las imágenes útiles desde 2017. Las barras más altas indican los meses en que el agua suele estar más verde. Útil para decidir cuándo muestrear.",
    season_top: "Meses más verdes",
    season_n: "imágenes",

    h_history: "3. Historial",
    history_help: "Cada punto es una imagen de satélite. Naranja = zonas más verdes del embalse; azul = valor típico de todo el embalse. Las líneas punteadas marcan los niveles Elevado y Muy alto. Haga clic en un punto para ver las imágenes de ese día.",
    f_res: "Embalse", both: "Ambos",
    r_3m: "Últimos 3 meses", r_1y: "Último año", r_all: "Todo",
    f_high: "Solo niveles Elevado y Muy alto", f_img: "Solo fechas con imagen",
    advanced: "Opciones avanzadas",
    f_from: "Desde", f_to: "Hasta", f_clear: "Mínimo visible (sin nubes)",
    s_p90: "Zonas más verdes", s_p50: "Típico del embalse",
    axis_ndci: "Índice de clorofila (NDCI)",
    line_l3: "Elevado", line_l4: "Muy alto",
    h_b4: "Avanzado: gráfico de turbidez (reflectancia roja B4)",
    b4_help: "El barro y el sedimento hacen que el agua refleje más luz roja. Si este valor y el índice de clorofila suben juntos después de lluvias, el aumento probablemente se debe a sedimento y no a algas.",

    h_table: "4. Lista de fechas",
    table_help: "Haga clic en una fila para ver las imágenes. Haga clic en un encabezado para ordenar.",
    c_date: "Fecha", c_res: "Embalse", c_lvl: "Nivel", c_p90: "Zonas más verdes (NDCI)",
    c_p50: "Típico (NDCI)", c_vis: "Visible", c_notes: "Avisos", c_img: "Imagen",
    n_clouds: "nubes", n_sediment: "sedimento", n_surface: "superficie",
    yes: "sí", no: "–",

    h_download: "5. Descargar datos",
    dl_xlsx: "Excel (recomendado)",
    dl_xlsx_help: "Todas las fechas, una hoja por embalse, con hojas que explican cada columna.",
    dl_csv: "CSV",
    dl_csv_help: "Para R, Python u otros programas. Las primeras líneas, que empiezan con #, explican los datos (en R: read.csv(..., comment.char = \"#\")).",
    dl_filtered: "Selección actual (CSV)",
    dl_filtered_help: "Solo las fechas que se ven ahora en la lista, con los filtros aplicados.",
    dl_aoi_help: "Contornos de los embalses usados en el análisis, para QGIS u otros SIG.",

    h_how: "6. ¿Cómo funciona? Explicación sencilla",
    footer: `Datos: Copernicus Sentinel-2 (ESA), procesados con Google Earth Engine. Código y documentación:
      <a href="https://github.com/KristofM854/embalses-s2-monitor">github.com/KristofM854/embalses-s2-monitor</a>.`,

    explain: [
      ["¿Qué mide el satélite?", `
        <p>Sentinel-2 son satélites europeos (programa Copernicus) que fotografían la Tierra.
        Pasan sobre los embalses cerca de las <b>11:15 de la mañana</b> (hora local), y hay una imagen nueva
        cada <b>2 a 5 días</b>. Cada píxel de la imagen mide 10 a 20 m.</p>
        <p>El satélite no mide la clorofila directamente: mide <b>cuánta luz del sol refleja</b> la superficie,
        en 13 "colores" (bandas). Algunos los vemos (azul, verde, rojo) y otros son invisibles para nosotros
        (el "borde rojo" y el infrarrojo). Las nubes tapan la vista: con nubes no hay dato.</p>`],
      ["¿Cómo se relaciona la luz con la clorofila?", `
        <p>La clorofila de las algas <b>absorbe la luz roja</b> (665 nm). Justo después del rojo, en el
        <b>"borde rojo"</b> (705 nm), el agua con muchas algas <b>refleja más</b> luz.</p>
        <p>El índice <b>NDCI</b> compara estas dos luces: NDCI = (borde rojo − rojo) / (borde rojo + rojo).</p>
        <table class="mini"><tr><th>Agua</th><th>NDCI aproximado</th></tr>
        <tr><td>Clara, con pocas algas</td><td>menor que 0</td></tr>
        <tr><td>Con algo de algas</td><td>0 a 0,1</td></tr>
        <tr><td>Verde, muchas algas</td><td>0,1 a 0,3</td></tr>
        <tr><td>Floración intensa</td><td>más de 0,3</td></tr></table>
        <p>Estos rangos son orientativos. Como el índice no está calibrado con muestras de estos embalses,
        los <b>niveles</b> de esta página (Bajo, Medio, Elevado, Muy alto) comparan cada imagen con la
        historia del mismo embalse.</p>`],
      ["¿Qué puede engañar al satélite?", `
        <ul>
        <li><b>Sedimento</b> (agua marrón después de lluvias): también cambia el color del agua y puede subir el índice.
          Aviso "sedimento".</li>
        <li><b>Nata de algas, plantas flotantes</b> (por ejemplo jacinto de agua): son brillantes en infrarrojo,
          como la vegetación. Pueden dar valores muy altos. Aviso "superficie". Revise la foto.</li>
        <li><b>Nubes, sombras de nubes y neblina</b>: las nubes se quitan automáticamente, pero sombras o neblina
          pueden quedar. Si una mancha roja coincide con una sombra en la foto, no la tome en cuenta.</li>
        <li><b>Reflejo del sol</b> en el agua, y <b>zonas poco profundas</b> donde se ve el fondo.</li>
        <li><b>Orillas</b>: se excluye una franja de 20 m para no mezclar tierra y agua. Las colas de los embalses
          (entradas de los ríos) solo se incluyen donde casi siempre hay agua.</li>
        </ul>`],
      ["¿Qué NO puede decir el satélite?", `
        <ul>
        <li>No da la <b>concentración exacta</b> de clorofila-a en µg/L. Para eso hace falta calibrar con muestras de campo.</li>
        <li>No distingue <b>cianobacterias</b> de otras algas, y no mide <b>toxinas</b>.</li>
        <li>Solo ve la <b>capa superior</b> del agua (aprox. el primer metro, menos en agua turbia).</li>
        <li>Es una foto de un momento (11:15). Las algas se mueven con el viento durante el día.</li>
        </ul>`],
      ["¿Cómo usarlo para planificar el muestreo?", `
        <ol>
        <li><b>Cuándo:</b> mire el gráfico "¿En qué meses...?" para ver la temporada con más algas.</li>
        <li><b>Dónde:</b> abra imágenes recientes y de la misma temporada de años anteriores. Busque dónde se
          acumula el agua verde (brazos, entrada del río, cerca de la presa). Elija puntos en zonas verdes
          <b>y</b> en zonas claras, para comparar.</li>
        <li><b>Mismo día que el satélite:</b> si es posible, muestree un día con paso del satélite y cielo
          despejado, cerca de las 11:15. Así cada muestra se puede comparar con la imagen.</li>
        <li><b>Anote:</b> coordenadas GPS, hora, profundidad (superficie, 0 a 0,5 m) y observaciones
          (color del agua, nata, plantas, lluvia reciente).</li>
        <li><b>Después:</b> con suficientes muestras de clorofila-a del mismo día, el índice se puede calibrar
          y convertir en µg/L para estos embalses.</li>
        </ol>`],
      ["Glosario", `
        <dl>
        <dt>Píxel</dt><dd>Cuadrado más pequeño de la imagen (aquí 20 × 20 m).</dd>
        <dt>Reflectancia</dt><dd>Fracción de la luz del sol que la superficie refleja (0 = nada, 1 = todo).</dd>
        <dt>Banda</dt><dd>Un "color" que mide el satélite, por ejemplo rojo (B4) o borde rojo (B5).</dd>
        <dt>NDCI</dt><dd>Índice de clorofila: compara borde rojo y rojo. Más alto = agua más verde.</dd>
        <dt>Zonas más verdes</dt><dd>Percentil 90: el valor que supera el 10 % más verde del agua del embalse.
          Detecta floraciones que cubren solo una parte del embalse.</dd>
        <dt>Típico del embalse</dt><dd>Mediana: la mitad del agua tiene un valor más alto y la otra mitad más bajo.</dd>
        <dt>Visible</dt><dd>Parte del embalse sin nubes en la imagen.</dd>
        <dt>Sedimento / turbidez</dt><dd>Barro y partículas en el agua, sobre todo después de lluvias.</dd>
        <dt>Nata</dt><dd>Capa de algas acumuladas en la superficie.</dd>
        </dl>`],
    ],
  },

  en: {
    title: "Valdesia and Hatillo reservoirs: chlorophyll seen from space",
    updated: "Updated:",
    source_short: "Sentinel-2 images (Copernicus, ESA)",
    nav_download: "Download data", nav_how: "How does it work?", lang: "Español",
    lead: `This page shows <b>how green the water</b> of the reservoirs is in satellite images.
      Greener water usually means <b>more algae</b> (more chlorophyll). Use it to see when and where
      there are more algae and to <b>plan sampling</b>. It does not replace laboratory analyses.
      <a href="#como-funciona">How does it work?</a>`,

    h_now: "1. Current situation",
    now_help: "The latest usable image of each reservoir (at least half of the reservoir cloud-free). The level compares that image with all earlier images of the same reservoir.",
    last_image: "Latest usable image", days_ago: "{n} days ago", today: "today", yesterday: "yesterday",
    visible: "visible",
    card_sentence: "The greenest parts of the reservoir are greener than in {p} % of earlier images.",
    see_images: "See images of this day",
    no_recent: "No recent usable images.",

    lvl_1: "Low", lvl_2: "Medium", lvl_3: "Elevated", lvl_4: "Very high",
    lvl_1_long: "less green than in half of the images",
    lvl_2_long: "within the normal range for this reservoir",
    lvl_3_long: "among the greenest 25 % of images",
    lvl_4_long: "among the greenest 10 % of images",

    note_clouds: "Many clouds: only {p} % of the reservoir is visible. Value not reliable.",
    note_sediment: "Turbid water (sediment): the value may be high because of mud, not algae.",
    note_surface: "Surface bright in infrared on {p} % of the water: may be algal scum, floating plants (water hyacinth), sun glint or haze. Check the photo.",

    prev: "◀ Previous", next: "Next ▶", close: "Close",
    cap_rgb: "Satellite photo (true colours)",
    cap_ndci: "Chlorophyll map on the water. No colour = clouds, shadow or outside the analysed area.",
    noimg: "No image for this date (too cloudy or not rendered yet).",
    leg_low: "little chlorophyll", leg_mid: "moderate", leg_high: "much chlorophyll",
    leg_note: "Blue = clear water · green = some algae · yellow and red = much chlorophyll.",
    leg_numbers: "Index values and approximate chlorophyll",
    leg_numbers_note: "Top: NDCI index value. Bottom: approximate chlorophyll-a in µg/L from a formula published for other lakes (Mishra & Mishra 2012). It is not calibrated for these reservoirs: use it only as an order of magnitude.",
    tech_values: "Technical values for this date",
    v_summary: "Level {lvl}: {long}. {vis} % of the reservoir visible.",

    h_season: "2. In which months are there usually more algae?",
    season_help: "Typical value of the greenest parts in each month, from all usable images since 2017. Taller bars mark the months when the water is usually greener. Useful for deciding when to sample.",
    season_top: "Greenest months",
    season_n: "images",

    h_history: "3. History",
    history_help: "Each point is a satellite image. Orange = greenest parts of the reservoir; blue = typical value of the whole reservoir. Dotted lines mark the Elevated and Very high levels. Click a point to see the images of that day.",
    f_res: "Reservoir", both: "Both",
    r_3m: "Last 3 months", r_1y: "Last year", r_all: "All",
    f_high: "Only Elevated and Very high levels", f_img: "Only dates with image",
    advanced: "Advanced options",
    f_from: "From", f_to: "To", f_clear: "Minimum visible (cloud-free)",
    s_p90: "Greenest parts", s_p50: "Typical for the reservoir",
    axis_ndci: "Chlorophyll index (NDCI)",
    line_l3: "Elevated", line_l4: "Very high",
    h_b4: "Advanced: turbidity chart (red reflectance B4)",
    b4_help: "Mud and sediment make the water reflect more red light. If this value and the chlorophyll index rise together after rain, the rise is probably sediment, not algae.",

    h_table: "4. List of dates",
    table_help: "Click a row to see the images. Click a column header to sort.",
    c_date: "Date", c_res: "Reservoir", c_lvl: "Level", c_p90: "Greenest parts (NDCI)",
    c_p50: "Typical (NDCI)", c_vis: "Visible", c_notes: "Warnings", c_img: "Image",
    n_clouds: "clouds", n_sediment: "sediment", n_surface: "surface",
    yes: "yes", no: "–",

    h_download: "5. Download data",
    dl_xlsx: "Excel (recommended)",
    dl_xlsx_help: "All dates, one sheet per reservoir, with sheets that explain every column.",
    dl_csv: "CSV",
    dl_csv_help: "For R, Python or other software. The first lines, starting with #, describe the data (in R: read.csv(..., comment.char = \"#\")).",
    dl_filtered: "Current selection (CSV)",
    dl_filtered_help: "Only the dates currently shown in the list, with the filters applied.",
    dl_aoi_help: "Reservoir outlines used in the analysis, for QGIS or other GIS.",

    h_how: "6. How does it work? A simple explanation",
    footer: `Data: Copernicus Sentinel-2 (ESA), processed with Google Earth Engine. Code and documentation:
      <a href="https://github.com/KristofM854/embalses-s2-monitor">github.com/KristofM854/embalses-s2-monitor</a>.`,

    explain: [
      ["What does the satellite measure?", `
        <p>Sentinel-2 are European satellites (Copernicus programme) that photograph the Earth.
        They pass over the reservoirs at about <b>11:15 in the morning</b> (local time), with a new image
        every <b>2 to 5 days</b>. Each image pixel is 10 to 20 m wide.</p>
        <p>The satellite does not measure chlorophyll directly: it measures <b>how much sunlight the surface
        reflects</b>, in 13 "colours" (bands). Some we can see (blue, green, red), others are invisible to us
        (the "red edge" and infrared). Clouds block the view: under clouds there is no data.</p>`],
      ["How is light related to chlorophyll?", `
        <p>The chlorophyll in algae <b>absorbs red light</b> (665 nm). Just beyond red, at the
        <b>"red edge"</b> (705 nm), water with many algae <b>reflects more</b> light.</p>
        <p>The <b>NDCI</b> index compares these two: NDCI = (red edge − red) / (red edge + red).</p>
        <table class="mini"><tr><th>Water</th><th>Approximate NDCI</th></tr>
        <tr><td>Clear, few algae</td><td>below 0</td></tr>
        <tr><td>Some algae</td><td>0 to 0.1</td></tr>
        <tr><td>Green, many algae</td><td>0.1 to 0.3</td></tr>
        <tr><td>Intense bloom</td><td>above 0.3</td></tr></table>
        <p>These ranges are a rough guide. Because the index is not calibrated with samples from these
        reservoirs, the <b>levels</b> on this page (Low, Medium, Elevated, Very high) compare each image
        with the history of the same reservoir.</p>`],
      ["What can mislead the satellite?", `
        <ul>
        <li><b>Sediment</b> (brown water after rain): it also changes the water colour and can raise the index.
          Warning "sediment".</li>
        <li><b>Algal scum, floating plants</b> (e.g. water hyacinth): they are bright in infrared, like vegetation,
          and can give very high values. Warning "surface". Check the photo.</li>
        <li><b>Clouds, cloud shadows and haze</b>: clouds are removed automatically, but shadows or haze can remain.
          If a red patch matches a shadow in the photo, ignore it.</li>
        <li><b>Sun glint</b> on the water, and <b>shallow areas</b> where the bottom is visible.</li>
        <li><b>Shores</b>: a 20 m strip is excluded so land and water do not mix. The tails of the reservoirs
          (river inflows) are only included where there is almost always water.</li>
        </ul>`],
      ["What can the satellite NOT tell?", `
        <ul>
        <li>It does not give the <b>exact concentration</b> of chlorophyll-a in µg/L. That needs calibration with field samples.</li>
        <li>It cannot tell <b>cyanobacteria</b> from other algae, and it does not measure <b>toxins</b>.</li>
        <li>It only sees the <b>upper layer</b> of the water (roughly the first metre, less in turbid water).</li>
        <li>It is a snapshot of one moment (11:15). Algae move with the wind during the day.</li>
        </ul>`],
      ["How to use it to plan sampling?", `
        <ol>
        <li><b>When:</b> look at the "In which months..." chart to see the season with most algae.</li>
        <li><b>Where:</b> open recent images, and images from the same season in earlier years. Look for where
          green water gathers (arms, river inflow, near the dam). Choose points in green areas <b>and</b>
          in clear areas, for comparison.</li>
        <li><b>Same day as the satellite:</b> if possible, sample on a day with a satellite pass and clear sky,
          around 11:15. Then every sample can be compared with the image.</li>
        <li><b>Record:</b> GPS coordinates, time, depth (surface, 0 to 0.5 m) and observations
          (water colour, scum, plants, recent rain).</li>
        <li><b>Afterwards:</b> with enough chlorophyll-a samples from the same days, the index can be calibrated
          and converted to µg/L for these reservoirs.</li>
        </ol>`],
      ["Glossary", `
        <dl>
        <dt>Pixel</dt><dd>Smallest square of the image (here 20 × 20 m).</dd>
        <dt>Reflectance</dt><dd>Share of the sunlight that the surface reflects (0 = none, 1 = all).</dd>
        <dt>Band</dt><dd>A "colour" measured by the satellite, e.g. red (B4) or red edge (B5).</dd>
        <dt>NDCI</dt><dd>Chlorophyll index: compares red edge and red. Higher = greener water.</dd>
        <dt>Greenest parts</dt><dd>90th percentile: the value exceeded by the greenest 10 % of the reservoir water.
          Detects blooms that cover only part of the reservoir.</dd>
        <dt>Typical for the reservoir</dt><dd>Median: half of the water has a higher value, half a lower one.</dd>
        <dt>Visible</dt><dd>Part of the reservoir without clouds in the image.</dd>
        <dt>Sediment / turbidity</dt><dd>Mud and particles in the water, especially after rain.</dd>
        <dt>Scum</dt><dd>Layer of algae gathered at the surface.</dd>
        </dl>`],
    ],
  },
};
