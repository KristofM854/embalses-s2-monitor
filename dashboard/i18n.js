// All visible text. Add a key here and use data-i18n="key" in index.html.
const I18N = {
  es: {
    title: "Monitor de embalses Sentinel-2",
    subtitle: "NDCI (indicador de clorofila) en Valdesia y Hatillo",
    updated: "Actualizado:",
    dl_csv: "Descargar CSV", dl_xlsx: "Descargar Excel", lang: "English",
    f_res: "Embalse", both: "Ambos", f_from: "Desde", f_to: "Hasta",
    r_3m: "3 meses", r_1y: "1 año", r_all: "Todo",
    f_clear: "Mín. sin nubes", f_thr: "Umbral NDCI p90", f_high: "Solo fechas ≥ umbral",
    f_img: "Solo fechas con imagen",
    prev: "◀ Anterior", next: "Siguiente ▶", close: "Cerrar",
    cap_rgb: "Color verdadero", cap_ndci: "NDCI sobre el agua despejada (nubes sin color)",
    noimg: "No hay imagen para esta fecha (demasiado nublado o aún no generada).",
    legend_note: "Arriba: NDCI. Abajo: clorofila-a indicativa (µg/L), Mishra & Mishra 2012, sin calibración local.",
    h_ndci: "Serie temporal de NDCI",
    ndci_help: "Azul = mediana, naranja = percentil 90 (manchas de floración). Línea roja punteada = umbral. Puntos con anillo = sobre el umbral. Haga clic en un punto para ver las imágenes.",
    h_b4: "Reflectancia roja (B4): control de turbidez",
    b4_help: "Si B4 y NDCI suben juntos después de lluvias, el pico de NDCI probablemente es sedimento, no floración.",
    h_table: "Observaciones", dl_filtered: "Descargar selección (CSV)",
    c_res: "Embalse", c_date: "Fecha", c_p50: "NDCI p50", c_p90: "NDCI p90",
    c_gt: "% NDCI>0.1", c_b4: "B4", c_nir: "% NIR alto", c_clear: "% sin nubes", c_img: "Imagen",
    latest: "Última observación útil", pct_of: "más alto que el {p} % de las observaciones", 
    clear: "sin nubes", above: "sobre umbral",
    median: "mediana", p90: "p90", threshold: "umbral",
    yes: "sí", no: "–",
    h_about: "Cómo leer estos datos",
    about: `<ul>
<li><b>NDCI</b> = (B5 − B4) / (B5 + B4) de Sentinel-2. Valores altos indican más clorofila. Es un <b>indicador relativo</b>: la corrección atmosférica (Sen2Cor) está hecha para tierra, no para agua, y no hay calibración local. Compare un embalse consigo mismo en el tiempo.</li>
<li><b>p90</b> responde a floraciones en parches; la <b>mediana</b> al estado general del embalse.</li>
<li><b>% sin nubes</b>: fracción del embalse visible (Cloud Score+ ≥ 0.6). Con menos de ~50 % los valores son menos fiables.</li>
<li><b>% NIR alto</b>: píxeles con B8 &gt; 0.05: espuma o nata de algas, plantas acuáticas, reflejo solar o neblina. Revise la imagen.</li>
<li><b>B4</b> alto junto con NDCI alto tras lluvias suele ser sedimento.</li>
<li>Los datos se actualizan automáticamente cada día con GitHub Actions. Sentinel-2 pasa cada ~5 días; las imágenes llegan con 1–3 días de retraso.</li>
<li>Fuentes: Copernicus Sentinel-2 L2A (COPERNICUS/S2_SR_HARMONIZED), Google Cloud Score+, JRC Global Surface Water, vía Google Earth Engine.</li>
</ul>`,
  },
  en: {
    title: "Sentinel-2 reservoir monitor",
    subtitle: "NDCI (chlorophyll indicator) for Valdesia and Hatillo",
    updated: "Updated:",
    dl_csv: "Download CSV", dl_xlsx: "Download Excel", lang: "Español",
    f_res: "Reservoir", both: "Both", f_from: "From", f_to: "To",
    r_3m: "3 months", r_1y: "1 year", r_all: "All",
    f_clear: "Min. cloud-free", f_thr: "NDCI p90 threshold", f_high: "Only dates ≥ threshold",
    f_img: "Only dates with image",
    prev: "◀ Previous", next: "Next ▶", close: "Close",
    cap_rgb: "True colour", cap_ndci: "NDCI on clear water (clouds uncoloured)",
    noimg: "No image for this date (too cloudy or not rendered yet).",
    legend_note: "Top: NDCI. Bottom: indicative chl-a (µg/L), Mishra & Mishra 2012, not locally calibrated.",
    h_ndci: "NDCI time series",
    ndci_help: "Blue = median, orange = 90th percentile (patchy blooms). Dotted red line = threshold. Ringed points = above threshold. Click a point to see the images.",
    h_b4: "Red reflectance (B4): turbidity check",
    b4_help: "If B4 and NDCI rise together after rain, the NDCI peak is probably sediment, not a bloom.",
    h_table: "Observations", dl_filtered: "Download selection (CSV)",
    c_res: "Reservoir", c_date: "Date", c_p50: "NDCI p50", c_p90: "NDCI p90",
    c_gt: "% NDCI>0.1", c_b4: "B4", c_nir: "% high NIR", c_clear: "% cloud-free", c_img: "Image",
    latest: "Latest usable observation", pct_of: "higher than {p} % of observations",
    clear: "cloud-free", above: "above threshold",
    median: "median", p90: "p90", threshold: "threshold",
    yes: "yes", no: "–",
    h_about: "How to read this data",
    about: `<ul>
<li><b>NDCI</b> = (B5 − B4) / (B5 + B4) from Sentinel-2. Higher means more chlorophyll. It is a <b>relative indicator</b>: the atmospheric correction (Sen2Cor) is made for land, not water, and there is no local calibration. Compare a reservoir with itself over time.</li>
<li><b>p90</b> responds to patchy blooms; the <b>median</b> to the reservoir as a whole.</li>
<li><b>% cloud-free</b>: share of the reservoir visible (Cloud Score+ ≥ 0.6). Below ~50 % values are less reliable.</li>
<li><b>% high NIR</b>: pixels with B8 &gt; 0.05: surface scum, floating plants, sun glint or haze. Check the image.</li>
<li>High <b>B4</b> together with high NDCI after rain is usually sediment.</li>
<li>Data update automatically every day via GitHub Actions. Sentinel-2 passes every ~5 days; scenes arrive 1–3 days late.</li>
<li>Sources: Copernicus Sentinel-2 L2A (COPERNICUS/S2_SR_HARMONIZED), Google Cloud Score+, JRC Global Surface Water, via Google Earth Engine.</li>
</ul>`,
  },
};
