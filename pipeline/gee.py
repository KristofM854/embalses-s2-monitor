"""Earth Engine part: outlines, per-scene statistics, thumbnails.

Backend:
  - COPERNICUS/S2_SR_HARMONIZED (L2A, Sen2Cor; offset of baseline 04.00 removed)
  - GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED (per-pixel cloud mask)
  - reservoir outline from Sentinel-2 MNDWI water frequency, or a hand-drawn override

Sen2Cor is a land atmospheric correction. NDCI here is a relative bloom
indicator, not calibrated chl-a.
"""
import hashlib
import io
import json
import math
import os
import time
from datetime import datetime, timezone

import ee
import pandas as pd
import requests
from PIL import Image

from . import config as C
from . import grid as G

S2 = "COPERNICUS/S2_SR_HARMONIZED"
LC08 = "LANDSAT/LC08/C02/T1_L2"
LC09 = "LANDSAT/LC09/C02/T1_L2"
CSP = "GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED"


def init(project=None):
    """Service account if EE_SERVICE_ACCOUNT_KEY holds the JSON key, else user login."""
    key = os.environ.get("EE_SERVICE_ACCOUNT_KEY", "").strip()
    project = project or os.environ.get("EE_PROJECT") or None
    if key:
        info = json.loads(key)
        creds = ee.ServiceAccountCredentials(info["client_email"], key_data=key)
        ee.Initialize(creds, project=project or info.get("project_id") or C.DEFAULT_PROJECT)
        return
    project = project or C.DEFAULT_PROJECT
    try:
        ee.Initialize(project=project)  # stored login or application-default credentials
    except Exception:
        if os.environ.get("CI"):
            raise RuntimeError("No Earth Engine credentials. Set EE_SERVICE_ACCOUNT_KEY.")
        ee.Authenticate()
        ee.Initialize(project=project)


class PermanentError(RuntimeError):
    """Retrying will not help (missing permission, bad project)."""


_PERMANENT = ("permission", "denied", "not authorized", "unauthorized", "not registered")


def retry(fn, *args, tries=4, **kw):
    for i in range(tries):
        try:
            return fn(*args, **kw)
        except (ee.EEException, requests.RequestException, OSError) as e:
            if any(w in str(e).lower() for w in _PERMANENT):
                raise PermanentError(str(e)) from e
            if i == tries - 1:
                raise
            wait = 15 * 2 ** i
            print(f"  retry in {wait}s after: {str(e)[:200]}", flush=True)
            time.sleep(wait)


# Outline ----------------------------------------------------------------------

def water_frequency(region):
    """Per pixel: share of clear Sentinel-2 looks that are water, and number of clear looks."""
    o = C.OUTLINE
    s2 = (ee.ImageCollection(S2).filterBounds(region).filterDate(o["start"], o["end"])
          .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 50))
          .linkCollection(ee.ImageCollection(CSP), ["cs_cdf"]))

    def wet(img):
        clear = img.select("cs_cdf").gte(C.CS_THRESHOLD)
        b11 = img.select("B11").resample("bilinear")
        mndwi = img.select("B3").subtract(b11).divide(img.select("B3").add(b11))
        return mndwi.gt(o["mndwi_min"]).rename("water").updateMask(clear)

    w = s2.map(wet)
    return w.mean(), w.count()


def _largest_water_body(region, scale):
    o = C.OUTLINE
    freq, n = water_frequency(region)
    water = freq.gte(o["water_freq_min"]).And(n.gte(o["min_obs"]))
    # close one-pixel gaps (a bridge, a noisy pixel) without merging real land
    water = (water.focalMax(scale, "circle", "meters")
             .focalMin(scale, "circle", "meters").selfMask())
    vecs = water.reduceToVectors(
        geometry=region, crs=C.CRS, scale=scale, geometryType="polygon",
        eightConnected=False, reducer=ee.Reducer.countEvery(),
        maxPixels=1e10, tileScale=4)
    return ee.Feature(vecs.sort("count", False).first()).geometry()


def build_outline(lon, lat, radius_m):
    """Largest Sentinel-2 water body near the seed, buffered inward.

    Two passes to keep the request small: find the reservoir at 30 m in the
    search circle, then trace it at OUTLINE["scale"] only inside its bounding box.
    Returns (GeoJSON geometry in EPSG:4326, True if it touches the search circle).
    """
    o = C.OUTLINE
    region = ee.Geometry.Point([lon, lat]).buffer(radius_m)
    coarse = _largest_water_body(region, 30)
    box = coarse.bounds(1).buffer(300, 1).intersection(region, 1)
    fine = _largest_water_body(box, o["scale"])
    inside = region.buffer(-100).contains(fine, 1)
    aoi = (fine.buffer(-o["shore_buffer_m"], 2).simplify(o["simplify_m"])
           .transform("EPSG:4326", 1))
    res = ee.Dictionary({"aoi": aoi, "inside": inside}).getInfo()
    return polygons_only(res["aoi"]), not res["inside"]


def _ring_area_m2(ring):
    """Approximate area of a lon/lat ring in m² (fine for small areas)."""
    lat0 = math.radians(sum(p[1] for p in ring) / len(ring))
    kx, ky = 111320 * math.cos(lat0), 110540
    a = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(ring, ring[1:]))
    return abs(a) / 2 * kx * ky


def polygons_only(geom, min_area_m2=10000):
    """Drop points, lines and slivers that a negative buffer can leave behind."""
    if geom["type"] == "Polygon":
        polys = [geom["coordinates"]]
    elif geom["type"] == "MultiPolygon":
        polys = geom["coordinates"]
    elif geom["type"] == "GeometryCollection":
        polys = []
        for g in geom["geometries"]:
            if g["type"] == "Polygon":
                polys.append(g["coordinates"])
            elif g["type"] == "MultiPolygon":
                polys.extend(g["coordinates"])
    else:
        polys = []
    polys = [p for p in polys if _ring_area_m2(p[0]) >= min_area_m2]
    if not polys:
        raise ValueError("outline has no polygon larger than the minimum area")
    return ({"type": "Polygon", "coordinates": polys[0]} if len(polys) == 1
            else {"type": "MultiPolygon", "coordinates": polys})


def count_pixels(geom):
    return ee.Image(1).reduceRegion(reducer=ee.Reducer.count().unweighted(),
                                    geometry=ee.Geometry(geom),
                                    scale=C.SCALE, crs=C.CRS, maxPixels=1e9
                                    ).get("constant").getInfo()


def read_override(path):
    """Hand-drawn outline: all (Multi)Polygons in a GeoJSON file merged into one geometry."""
    with open(path, "rb") as fh:
        raw = fh.read()
    gj = json.loads(raw)
    if gj.get("type") == "FeatureCollection":
        geoms = [f["geometry"] for f in gj["features"]]
    elif gj.get("type") == "Feature":
        geoms = [gj["geometry"]]
    else:
        geoms = [gj]
    geom = polygons_only({"type": "GeometryCollection", "geometries": geoms}, 0)
    return geom, hashlib.sha1(raw).hexdigest()


def outline_params(name, override_sha=None):
    """What the cached outline was built from. A difference triggers a rebuild."""
    if override_sha:
        return {"method": "override", "sha1": override_sha, "version": C.OUTLINE_VERSION}
    return {"method": "s2_mndwi", "seed": C.RESERVOIRS[name], **C.OUTLINE,
            "version": C.OUTLINE_VERSION}


def load_or_build_outline(name, data_dir):
    """Returns (geometry, n_total, needs_backfill).

    Order: data/aoi_overrides/<name>.geojson if present, else the Sentinel-2 outline.
    The result is cached in data/aoi_<name>.geojson together with the parameters it
    was built from, so n_total stays fixed until those parameters change.
    """
    path = os.path.join(data_dir, f"aoi_{name}.geojson")
    override = os.path.join(data_dir, "aoi_overrides", f"{name}.geojson")
    geom = sha = None
    if os.path.exists(override):
        geom, sha = read_override(override)
    params = json.loads(json.dumps(outline_params(name, sha)))  # normalise tuples etc.

    if os.path.exists(path):
        with open(path) as fh:
            feat = json.load(fh)["features"][0]
        if feat["properties"].get("params") == params:
            # still True if a previous run died before finishing the full re-query
            return (feat["geometry"], feat["properties"]["n_total"],
                    not feat["properties"].get("backfilled", False))

    touches = False
    if geom is None:
        r = C.RESERVOIRS[name]
        geom, touches = retry(build_outline, r["lon"], r["lat"], r["radius_m"])
        if touches:
            print(f"::warning::{name}: outline reaches the edge of the {r['radius_m']} m search "
                  f"circle; the reservoir may be cut off. Increase radius_m in config.py.", flush=True)
    n_total = retry(count_pixels, geom)
    os.makedirs(data_dir, exist_ok=True)
    with open(path, "w") as fh:
        json.dump({"type": "FeatureCollection", "features": [{
            "type": "Feature", "geometry": geom,
            "properties": {"reservoir": name, "n_total": n_total, "scale_m": C.SCALE,
                           "touches_search_edge": touches, "params": params,
                           "backfilled": False}}]}, fh)
    print(f"{name}: new outline ({params['method']}), {n_total} water pixels at {C.SCALE} m",
          flush=True)
    return geom, n_total, True


def mark_backfilled(name, data_dir):
    """Record that the whole series has been computed on the current outline."""
    path = os.path.join(data_dir, f"aoi_{name}.geojson")
    with open(path) as fh:
        gj = json.load(fh)
    gj["features"][0]["properties"]["backfilled"] = True
    with open(path, "w") as fh:
        json.dump(gj, fh)


# Statistics -------------------------------------------------------------------

def _scene_stats(aoi, start, end):
    s2 = ee.ImageCollection(S2).filterBounds(aoi).filterDate(start, end)
    # unweighted: a pixel counts if its centre is inside the outline, as in count_pixels()
    reducer = (ee.Reducer.percentile([50, 90])
               .combine(ee.Reducer.mean(), sharedInputs=True)
               .combine(ee.Reducer.count(), sharedInputs=True)).unweighted()
    lo, hi = C.NDCI_FLAGS

    def to_feature(img):
        clear = img.select("cs_cdf").gte(C.CS_THRESHOLD)
        refl = img.select(["B4", "B5", "B8"]).divide(10000)
        ndci = refl.normalizedDifference(["B5", "B4"]).rename("NDCI")
        stack = (ndci
                 .addBands(refl.select(["B4", "B8"]))
                 .addBands(refl.select("B8").gt(C.NIR_FLAG).rename("HINIR"))
                 .addBands(ndci.gt(lo).rename("GTLO"))
                 .addBands(ndci.gt(hi).rename("GTHI"))
                 .updateMask(clear))
        s = stack.reduceRegion(reducer=reducer, geometry=aoi, scale=C.SCALE, crs=C.CRS,
                               maxPixels=1e9, tileScale=4)
        return ee.Feature(None, s).set({"date": img.date().format("YYYY-MM-dd"),
                                        "scene": img.get("system:index")})

    feats = s2.linkCollection(ee.ImageCollection(CSP), ["cs_cdf"]).map(to_feature).getInfo()
    return pd.DataFrame([f["properties"] for f in feats["features"]])


def scene_stats(name, geom, n_total, start, end):
    """One row per reservoir-date in [start, end). Same-day granules are merged later."""
    df = retry(_scene_stats, ee.Geometry(geom), start, end)
    if df.empty:
        return df
    df = df.reindex(columns=["date", "scene", "NDCI_count", "NDCI_p50", "NDCI_p90", "NDCI_mean",
                             "GTLO_mean", "GTHI_mean", "B4_p50", "B8_p50", "HINIR_mean"])
    out = pd.DataFrame({
        "reservoir": name,
        "date": df["date"],
        "ndci_p50": df["NDCI_p50"],
        "ndci_p90": df["NDCI_p90"],
        "ndci_mean": df["NDCI_mean"],
        "frac_ndci_gt_0.1": df["GTLO_mean"],
        "frac_ndci_gt_0.2": df["GTHI_mean"],
        "b4_p50": df["B4_p50"],
        "b8_p50": df["B8_p50"],
        "frac_high_nir": df["HINIR_mean"],
        "n_valid": pd.to_numeric(df["NDCI_count"]).fillna(0).astype(int),
        "n_total": n_total,
        "scene": df["scene"],
    })
    out["frac_valid"] = out["n_valid"] / n_total
    return out


# Images -----------------------------------------------------------------------

def thumb_urls(geom, date, grid):
    """True colour, and true colour with NDCI on clear water, for one date, on `grid`."""
    aoi = ee.Geometry(geom)
    d = ee.Date(date)
    img = ee.ImageCollection(S2).filterBounds(aoi).filterDate(d, d.advance(1, "day")).mosaic()
    cs = (ee.ImageCollection(CSP).filterBounds(aoi).filterDate(d, d.advance(1, "day"))
          .mosaic().select("cs_cdf"))
    rgb = img.visualize(bands=["B4", "B3", "B2"], min=0, max=1500, gamma=1.4)
    ndci = (img.normalizedDifference(["B5", "B4"])
            .updateMask(cs.gte(C.CS_THRESHOLD)).clip(aoi))
    overlay = rgb.blend(ndci.visualize(min=C.NDCI_VIS[0], max=C.NDCI_VIS[1],
                                       palette=C.NDCI_PALETTE))
    params = G.thumb_params(grid)
    return {"rgb": rgb.getThumbURL(params), "ndci": overlay.getThumbURL(params)}


def _fetch_webp(url, path):
    r = requests.get(url, timeout=180)
    r.raise_for_status()
    im = Image.open(io.BytesIO(r.content)).convert("RGB")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    im.save(tmp, "WEBP", quality=C.IMG_QUALITY, method=6)
    os.replace(tmp, path)


def render_images(geom, date, rgb_path, ndci_path, grid):
    urls = retry(thumb_urls, geom, date, grid)
    retry(_fetch_webp, urls["rgb"], rgb_path)
    retry(_fetch_webp, urls["ndci"], ndci_path)


# Summary maps -------------------------------------------------------------------

def _clear_ndci(scene_ids, aoi):
    """NDCI on clear pixels of the given (usable) scenes."""
    s2 = (ee.ImageCollection(S2).filterBounds(aoi)
          .filter(ee.Filter.inList("system:index", scene_ids))
          .linkCollection(ee.ImageCollection(CSP), ["cs_cdf"]))
    return s2.map(lambda img: img.normalizedDifference(["B5", "B4"]).rename("ndci")
                  .updateMask(img.select("cs_cdf").gte(C.CS_THRESHOLD)))


def _basemap(aoi, end):
    """Cloud-free true-colour background: per-pixel median of the clear looks of one year."""
    s2 = (ee.ImageCollection(S2).filterBounds(aoi)
          .filterDate(ee.Date(end).advance(-1, "year"), end)
          .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60))
          .linkCollection(ee.ImageCollection(CSP), ["cs_cdf"]))
    med = s2.map(lambda i: i.select(["B4", "B3", "B2"])
                 .updateMask(i.select("cs_cdf").gte(C.CS_THRESHOLD))).median()
    return med.visualize(bands=["B4", "B3", "B2"], min=0, max=1500, gamma=1.4)


def _map_urls(geom, grid, scene_ids, end):
    o = C.MAPS
    aoi = ee.Geometry(geom)
    ndci = _clear_ndci(scene_ids, aoi)
    n = ndci.count()
    ok = n.gte(o["min_obs"])
    mean = ndci.mean().updateMask(ok).clip(aoi)
    freq = ndci.map(lambda i: i.gt(o["green_ndci"])).mean().updateMask(ok).clip(aoi)
    # stretch the typical-value map to this reservoir's own range
    rng = mean.reduceRegion(ee.Reducer.percentile([2, 98]), aoi, C.SCALE, crs=C.CRS,
                            maxPixels=1e9, tileScale=4).getInfo()
    lo, hi = rng.get("ndci_p2"), rng.get("ndci_p98")
    if lo is None or hi is None:
        raise ValueError("not enough clear observations for the summary maps")
    hi = max(hi, lo + 0.02)
    base = _basemap(aoi, end)
    params = G.thumb_params(grid)
    pal = o["palette"]
    return {
        "mean": base.blend(mean.visualize(min=lo, max=hi, palette=pal)).getThumbURL(params),
        "freq": base.blend(freq.visualize(min=0, max=o["freq_max"], palette=pal)).getThumbURL(params),
        "mean_range": [round(lo, 3), round(hi, 3)],
    }


def render_maps(geom, grid, scene_ids, end, mean_path, freq_path):
    r = retry(_map_urls, geom, grid, scene_ids, end)
    retry(_fetch_webp, r["mean"], mean_path)
    retry(_fetch_webp, r["freq"], freq_path)
    return r["mean_range"]


# Landsat 8/9 surface temperature -----------------------------------------------

def _landsat(aoi, start, end):
    col = (ee.ImageCollection(LC08).merge(ee.ImageCollection(LC09))
           .filterBounds(aoi).filterDate(start, end))
    return col


def _landsat_stats(geom, start, end):
    aoi = ee.Geometry(geom)
    reducer = (ee.Reducer.percentile([10, 50, 90])
               .combine(ee.Reducer.count(), sharedInputs=True)).unweighted()

    def to_feature(img):
        qa = img.select("QA_PIXEL")
        clear = qa.bitwiseAnd(0b11111).eq(0)  # fill, dilated cloud, cirrus, cloud, shadow
        lst = (img.select("ST_B10").multiply(0.00341802).add(149.0).subtract(273.15)
               .rename("LST").updateMask(clear))
        s = lst.reduceRegion(reducer=reducer, geometry=aoi, scale=30, crs=C.CRS,
                             maxPixels=1e9, tileScale=4)
        return ee.Feature(None, s).set({
            "date": img.date().format("YYYY-MM-dd"),
            "scene": img.get("LANDSAT_PRODUCT_ID"),
            "spacecraft": img.get("SPACECRAFT_ID")})

    feats = _landsat(aoi, start, end).map(to_feature).getInfo()["features"]
    return pd.DataFrame([f["properties"] for f in feats])


def landsat_aoi(geom):
    """Outline shrunk further, because the thermal band is 100 m and mixes in warm land."""
    return ee.Geometry(geom).buffer(-C.LANDSAT["extra_buffer_m"], 5).transform("EPSG:4326", 1)


def landsat_stats(name, geom_t, n_total, start, end):
    df = retry(_landsat_stats, geom_t, start, end)
    if df.empty:
        return df
    df = df.reindex(columns=["date", "scene", "spacecraft", "LST_count", "LST_p10", "LST_p50", "LST_p90"])
    out = pd.DataFrame({
        "reservoir": name, "date": df["date"],
        "temp_p10": df["LST_p10"], "temp_p50": df["LST_p50"], "temp_p90": df["LST_p90"],
        "n_valid": pd.to_numeric(df["LST_count"]).fillna(0).astype(int),
        "n_total": n_total, "spacecraft": df["spacecraft"], "scene": df["scene"]})
    return out


def landsat_outline(geom):
    g = retry(lambda: landsat_aoi(geom).getInfo())
    g = polygons_only(g, 0)
    n = retry(lambda: ee.Image(1).reduceRegion(
        reducer=ee.Reducer.count().unweighted(), geometry=ee.Geometry(g), scale=30,
        crs=C.CRS, maxPixels=1e9).get("constant").getInfo())
    return g, n


# Satellite passes ---------------------------------------------------------------

def recent_passes(geom, days=48):
    """Acquisition dates per spacecraft over the reservoir in the last `days` days,
    clouds or not. Used to predict the next passes (repeat cycles are fixed)."""
    aoi = ee.Geometry(geom)
    end = ee.Date(datetime.now(timezone.utc).strftime("%Y-%m-%d")).advance(1, "day")
    start = end.advance(-days, "day")
    s2 = ee.ImageCollection(S2).filterBounds(aoi).filterDate(start, end)
    ls = _landsat(aoi, start, end)
    fmt = lambda c, key: c.map(lambda i: ee.Feature(None, {
        "d": i.date().format("YYYY-MM-dd"), "sat": i.get(key)})).distinct(["d", "sat"])
    res = ee.Dictionary({"s2": fmt(s2, "SPACECRAFT_NAME").toList(500),
                         "landsat": fmt(ls, "SPACECRAFT_ID").toList(500)}).getInfo()
    return {k: sorted({(f["properties"]["sat"], f["properties"]["d"]) for f in v})
            for k, v in res.items()}
