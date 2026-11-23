"""Single source for what every column means.

Used for the Excel metadata sheets, the comment header of the CSV and
data/columns.json (read by the dashboard). Edit the text here only.
"""

REPO_URL = "https://github.com/KristofM854/embalses-s2-monitor"
DASHBOARD_URL = "https://kristofm854.github.io/embalses-s2-monitor/"

# name, unit, description EN, description ES, how to read it EN, how to read it ES
COLUMNS = [
    ("reservoir", "-",
     "Reservoir name.", "Nombre del embalse.",
     "", ""),
    ("date", "YYYY-MM-DD",
     "Date of the Sentinel-2 image (UTC). The satellite passes at about 15:15 UTC "
     "(11:15 local time).",
     "Fecha de la imagen Sentinel-2 (UTC). El satélite pasa a las 15:15 UTC aprox. "
     "(11:15 hora local).",
     "Use this date to compare with field samples taken the same day.",
     "Use esta fecha para comparar con muestras de campo del mismo día."),
    ("ndci_p50", "index (-1 to 1)",
     "Median NDCI over the cloud-free water of the reservoir. "
     "NDCI = (B5 - B4) / (B5 + B4), red-edge (705 nm) versus red (665 nm) reflectance.",
     "Mediana del NDCI sobre el agua sin nubes del embalse. "
     "NDCI = (B5 - B4) / (B5 + B4), reflectancia del borde rojo (705 nm) frente al rojo (665 nm).",
     "Typical chlorophyll level of the reservoir as a whole. Higher = greener water.",
     "Nivel típico de clorofila del embalse en conjunto. Más alto = agua más verde."),
    ("ndci_p90", "index (-1 to 1)",
     "90th percentile of NDCI: the value exceeded by the greenest 10 % of the water.",
     "Percentil 90 del NDCI: valor que supera el 10 % más verde del agua.",
     "Chlorophyll in the greenest parts. Reacts to blooms that cover only part of the reservoir.",
     "Clorofila en las zonas más verdes. Reacciona a floraciones que cubren solo una parte del embalse."),
    ("ndci_mean", "index (-1 to 1)",
     "Mean NDCI over the cloud-free water.", "Promedio del NDCI sobre el agua sin nubes.",
     "Similar to the median, but more affected by a few extreme pixels.",
     "Parecido a la mediana, pero más afectado por pocos píxeles extremos."),
    ("frac_ndci_gt_0.1", "fraction (0 to 1)",
     "Share of the cloud-free water with NDCI > 0.1.",
     "Fracción del agua sin nubes con NDCI > 0,1.",
     "How much of the reservoir is clearly green. 0.3 = 30 % of the surface.",
     "Cuánto del embalse está claramente verde. 0,3 = 30 % de la superficie."),
    ("frac_ndci_gt_0.2", "fraction (0 to 1)",
     "Share of the cloud-free water with NDCI > 0.2.",
     "Fracción del agua sin nubes con NDCI > 0,2.",
     "How much of the reservoir is very green.",
     "Cuánto del embalse está muy verde."),
    ("b4_p50", "reflectance (0 to 1)",
     "Median red reflectance (Sentinel-2 band B4, 665 nm).",
     "Mediana de la reflectancia roja (banda B4 de Sentinel-2, 665 nm).",
     "Rises with mud or sediment in the water. If it is high together with NDCI, "
     "the NDCI may be raised by sediment, not algae.",
     "Sube con barro o sedimento en el agua. Si está alta junto con el NDCI, "
     "el NDCI puede deberse a sedimento y no a algas."),
    ("b8_p50", "reflectance (0 to 1)",
     "Median near-infrared reflectance (band B8, 842 nm).",
     "Mediana de la reflectancia del infrarrojo cercano (banda B8, 842 nm).",
     "Clear water is dark in near-infrared (close to 0).",
     "El agua limpia es oscura en el infrarrojo cercano (cerca de 0)."),
    ("frac_high_nir", "fraction (0 to 1)",
     "Share of the cloud-free water with near-infrared reflectance above 0.05.",
     "Fracción del agua sin nubes con reflectancia infrarroja mayor que 0,05.",
     "Water should not be bright in near-infrared. Bright pixels are surface scum, "
     "floating plants (e.g. water hyacinth), sun glint or haze. Check the image.",
     "El agua no debería ser brillante en el infrarrojo. Los píxeles brillantes son nata "
     "de algas, plantas flotantes (p. ej. jacinto de agua), reflejo del sol o neblina. Revise la imagen."),
    ("n_valid", "pixels (20 m)",
     "Number of cloud-free water pixels used.", "Número de píxeles de agua sin nubes usados.",
     "", ""),
    ("n_total", "pixels (20 m)",
     "Number of water pixels in the reservoir outline.",
     "Número de píxeles de agua dentro del contorno del embalse.",
     "", ""),
    ("frac_valid", "fraction (0 to 1)",
     "Cloud-free share of the reservoir (n_valid / n_total).",
     "Fracción del embalse sin nubes (n_valid / n_total).",
     "Below 0.5 (half the reservoir hidden by clouds), treat the values with caution.",
     "Por debajo de 0,5 (la mitad del embalse cubierta por nubes), use los valores con cautela."),
    ("scene", "-",
     "Identifier of the Sentinel-2 image in Google Earth Engine.",
     "Identificador de la imagen Sentinel-2 en Google Earth Engine.",
     "", ""),
]

GENERAL = [
    ("Dataset", "Datos",
     "Sentinel-2 chlorophyll indicator (NDCI) for the Valdesia and Hatillo reservoirs, "
     "Dominican Republic. One row per reservoir and satellite image.",
     "Indicador de clorofila (NDCI) de Sentinel-2 para los embalses Valdesia y Hatillo, "
     "República Dominicana. Una fila por embalse e imagen de satélite."),
    ("Source", "Fuente",
     "Copernicus Sentinel-2 L2A (COPERNICUS/S2_SR_HARMONIZED), cloud mask Google Cloud Score+ "
     "(cs_cdf >= 0.6), processed in Google Earth Engine.",
     "Copernicus Sentinel-2 L2A (COPERNICUS/S2_SR_HARMONIZED), máscara de nubes Google "
     "Cloud Score+ (cs_cdf >= 0,6), procesado en Google Earth Engine."),
    ("Area", "Área",
     "Reservoir outline from Sentinel-2 water frequency 2019-2025, 20 m inside the shore "
     "(data/aoi_<reservoir>.geojson).",
     "Contorno del embalse a partir de la frecuencia de agua de Sentinel-2 2019-2025, "
     "20 m hacia dentro de la orilla (data/aoi_<embalse>.geojson)."),
    ("Important", "Importante",
     "NDCI is a relative indicator, not a chlorophyll-a concentration. It has not been "
     "calibrated with samples from these reservoirs. Compare each reservoir with itself over time.",
     "El NDCI es un indicador relativo, no una concentración de clorofila-a. No ha sido "
     "calibrado con muestras de estos embalses. Compare cada embalse consigo mismo en el tiempo."),
    ("Not included", "No incluye",
     "Satellite data cannot tell cyanobacteria from other algae, and cannot measure toxins. "
     "It sees only the upper water layer.",
     "Los datos de satélite no distinguen cianobacterias de otras algas ni miden toxinas. "
     "Solo ven la capa superior del agua."),
    ("Updates", "Actualización",
     "Checked for new images every two hours. Sentinel-2 images every 2-5 days; "
     "a new image usually appears here within a day after it was taken.",
     "Se buscan imágenes nuevas cada dos horas. Imágenes Sentinel-2 cada 2-5 días; "
     "una imagen nueva suele aparecer aquí en menos de un día después de tomarla."),
    ("More", "Más",
     f"Dashboard: {DASHBOARD_URL}  Code and documentation: {REPO_URL}",
     f"Panel: {DASHBOARD_URL}  Código y documentación: {REPO_URL}"),
]


# Landsat 8/9 water surface temperature table (data/landsat_temperature.csv)
TEMP_COLUMNS = [
    ("reservoir", "-", "Reservoir name.", "Nombre del embalse.", "", ""),
    ("date", "YYYY-MM-DD",
     "Date of the Landsat image (UTC). Landsat passes at about 15:00 UTC (11:00 local time).",
     "Fecha de la imagen Landsat (UTC). Landsat pasa a las 15:00 UTC aprox. (11:00 hora local).",
     "", ""),
    ("temp_p10", "°C", "10th percentile of the water surface temperature (cooler parts).",
     "Percentil 10 de la temperatura de la superficie del agua (zonas más frías).", "", ""),
    ("temp_p50", "°C", "Median water surface temperature.",
     "Mediana de la temperatura de la superficie del agua.",
     "Temperature of the top millimetres of the water ('skin'), accuracy about 1 to 2 °C. "
     "Warm water favours algal and cyanobacterial blooms.",
     "Temperatura de los primeros milímetros del agua ('piel'), exactitud de 1 a 2 °C aprox. "
     "El agua cálida favorece las floraciones de algas y cianobacterias."),
    ("temp_p90", "°C", "90th percentile of the water surface temperature (warmer parts).",
     "Percentil 90 de la temperatura de la superficie del agua (zonas más cálidas).", "", ""),
    ("n_valid", "pixels (30 m)", "Number of cloud-free water pixels used.",
     "Número de píxeles de agua sin nubes usados.", "", ""),
    ("n_total", "pixels (30 m)",
     "Number of water pixels in the temperature outline (120 m inside the shore, because the "
     "thermal band is 100 m and would otherwise mix in warm land).",
     "Número de píxeles de agua en el contorno de temperatura (120 m dentro de la orilla, porque la "
     "banda térmica es de 100 m y si no mezclaría tierra caliente).", "", ""),
    ("frac_valid", "fraction (0 to 1)", "Cloud-free share of the temperature outline.",
     "Fracción sin nubes del contorno de temperatura.",
     "Below 0.5, treat the values with caution.", "Por debajo de 0,5, use los valores con cautela."),
    ("spacecraft", "-", "LANDSAT_8 or LANDSAT_9.", "LANDSAT_8 o LANDSAT_9.", "", ""),
    ("scene", "-", "Landsat product identifier.", "Identificador del producto Landsat.", "", ""),
]

TEMP_GENERAL = [
    ("Dataset", "Datos",
     "Water surface temperature from Landsat 8/9 for the Valdesia and Hatillo reservoirs. "
     "One row per reservoir and Landsat image.",
     "Temperatura de la superficie del agua de Landsat 8/9 para los embalses Valdesia y Hatillo. "
     "Una fila por embalse e imagen Landsat."),
    ("Source", "Fuente",
     "USGS Landsat Collection 2 Level-2 surface temperature (ST_B10), LANDSAT/LC08 and LC09 "
     "C02/T1_L2, cloud mask from QA_PIXEL, processed in Google Earth Engine.",
     "Temperatura de superficie Landsat Colección 2 Nivel 2 del USGS (ST_B10), LANDSAT/LC08 y LC09 "
     "C02/T1_L2, máscara de nubes de QA_PIXEL, procesado en Google Earth Engine."),
    ("Important", "Importante",
     "Skin temperature of the surface, not the temperature at depth. Images every 8 days "
     "(two satellites); new images can take days to weeks to appear.",
     "Temperatura de la piel de la superficie, no la temperatura en profundidad. Imágenes cada 8 días "
     "(dos satélites); las imágenes nuevas pueden tardar días o semanas en aparecer."),
]
