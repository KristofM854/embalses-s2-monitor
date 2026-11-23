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
import os
import time

import ee
import pandas as pd
import requests
from PIL import Image

from . import config as C

S2 = "COPERNICUS/S2_SR_HARMONIZED"
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
    inside = region.buffer(-100).contains(coarse, 1)
    aoi = (fine.buffer(-o["shore_buffer_m"], 2).simplify(o["simplify_m"])
           .transform("EPSG:4326", 1))
    res = ee.Dictionary({"aoi": aoi, "inside": inside}).getInfo()
    return res["aoi"], not res["inside"]


def count_pixels(geom):
    return ee.Image(1).reduceRegion(reducer=ee.Reducer.count(), geometry=ee.Geometry(geom),
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
    polys = []
    for g in geoms:
        if g["type"] == "Polygon":
            polys.append(g["coordinates"])
        elif g["type"] == "MultiPolygon":
            polys.extend(g["coordinates"])
    if not polys:
        raise ValueError(f"{path}: no Polygon or MultiPolygon found")
    geom = ({"type": "Polygon", "coordinates": polys[0]} if len(polys) == 1
            else {"type": "MultiPolygon", "coordinates": polys})
    return geom, hashlib.sha1(raw).hexdigest()


def outline_params(name, override_sha=None):
    """What the cached outline was built from. A difference triggers a rebuild."""
    if override_sha:
        return {"method": "override", "sha1": override_sha}
    return {"method": "s2_mndwi", "seed": C.RESERVOIRS[name], **C.OUTLINE}


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
    reducer = (ee.Reducer.percentile([50, 90])
               .combine(ee.Reducer.mean(), sharedInputs=True)
               .combine(ee.Reducer.count(), sharedInputs=True))
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

def thumb_urls(geom, date):
    """True colour, and true colour with NDCI on clear water, for one date."""
    aoi = ee.Geometry(geom)
    region = aoi.bounds().buffer(1000).bounds()
    d = ee.Date(date)
    img = ee.ImageCollection(S2).filterBounds(aoi).filterDate(d, d.advance(1, "day")).mosaic()
    cs = (ee.ImageCollection(CSP).filterBounds(aoi).filterDate(d, d.advance(1, "day"))
          .mosaic().select("cs_cdf"))
    rgb = img.visualize(bands=["B4", "B3", "B2"], min=0, max=1500, gamma=1.4)
    ndci = (img.normalizedDifference(["B5", "B4"])
            .updateMask(cs.gte(C.CS_THRESHOLD)).clip(aoi))
    overlay = rgb.blend(ndci.visualize(min=C.NDCI_VIS[0], max=C.NDCI_VIS[1],
                                       palette=C.NDCI_PALETTE))
    params = {"region": region, "dimensions": C.IMG_DIM, "format": "png", "crs": C.CRS}
    return {"rgb": rgb.getThumbURL(params), "ndci": overlay.getThumbURL(params)}


def _fetch_webp(url, path):
    r = requests.get(url, timeout=180)
    r.raise_for_status()
    im = Image.open(io.BytesIO(r.content)).convert("RGB")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    im.save(tmp, "WEBP", quality=C.IMG_QUALITY, method=6)
    os.replace(tmp, path)


def render_images(geom, date, rgb_path, ndci_path):
    urls = retry(thumb_urls, geom, date)
    retry(_fetch_webp, urls["rgb"], rgb_path)
    retry(_fetch_webp, urls["ndci"], ndci_path)
