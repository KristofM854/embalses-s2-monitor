# Contornos dibujados a mano · Hand-drawn outlines

**ES.** Si el contorno automático de un embalse no es correcto, se puede dibujar uno a mano:

1. Abra https://geojson.io, busque el embalse y active la capa satelital (abajo a la izquierda).
2. Dibuje el polígono con la herramienta de polígono. Quédese **unos 20 m dentro de la
   orilla** (aprox. un píxel de Sentinel-2) para evitar píxeles mezclados de tierra y agua.
   Se pueden dibujar varios polígonos; se unen.
3. *Save → GeoJSON*. Renombre el archivo exactamente como el embalse: `Valdesia.geojson`
   o `Hatillo.geojson`.
4. En GitHub, abra esta carpeta → *Add file → Upload files* → suba el archivo → *Commit*.

En la siguiente actualización (cada dos horas, o al ejecutar "Update data" a mano) se usa el nuevo
contorno y **toda la serie y las imágenes de ese embalse se recalculan automáticamente**.
Para volver al contorno automático, borre el archivo.

**EN.** To replace the automatic outline, draw a polygon at geojson.io about 20 m inside
the shore, save it as `<Reservoir>.geojson` (exact name as in `pipeline/config.py`) and
upload it here. The next run uses it and recomputes that reservoir's whole series and
images. Delete the file to go back to the automatic outline.

The outline actually in use is always `data/aoi_<Reservoir>.geojson`. GitHub shows it on a
map when you open the file.
