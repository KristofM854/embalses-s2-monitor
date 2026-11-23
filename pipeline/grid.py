"""Exact pixel grid for the rendered images, so the dashboard can turn a
mouse position into latitude/longitude.

Every image of a reservoir (daily pair and summary maps) is rendered on the
same grid: north-up in UTM 19N, `scale` metres per pixel, top-left corner at
(x0, y0). The four corners are also stored in lat/lon; inside one image the
UTM -> lat/lon mapping is close enough to bilinear (error well below 1 m).
"""
import math

from pyproj import Transformer

GRID_VERSION = 1   # bump to force all images to be re-rendered


def _coords(geom):
    if geom["type"] == "Polygon":
        polys = [geom["coordinates"]]
    elif geom["type"] == "MultiPolygon":
        polys = geom["coordinates"]
    else:
        raise ValueError(f"unexpected geometry {geom['type']}")
    return [pt for poly in polys for ring in poly for pt in ring]


def image_grid(geom, crs, max_dim, pad_m=1000, min_scale=10):
    to_utm = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    to_ll = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
    lon, lat = zip(*_coords(geom))
    xs, ys = to_utm.transform(lon, lat)
    xmin, xmax = min(xs) - pad_m, max(xs) + pad_m
    ymin, ymax = min(ys) - pad_m, max(ys) + pad_m
    scale = max(min_scale, math.ceil(max(xmax - xmin, ymax - ymin) / max_dim))
    x0 = math.floor(xmin / scale) * scale
    y0 = math.ceil(ymax / scale) * scale
    w = math.ceil((xmax - x0) / scale)
    h = math.ceil((y0 - ymin) / scale)
    x1, y1 = x0 + w * scale, y0 - h * scale
    corners = {k: [round(v, 7) for v in to_ll.transform(x, y)]
               for k, (x, y) in {"nw": (x0, y0), "ne": (x1, y0), "sw": (x0, y1), "se": (x1, y1)}.items()}
    return {"crs": crs, "scale": scale, "x0": x0, "y0": y0, "width": w, "height": h,
            "corners_lonlat": corners, "version": GRID_VERSION}


def thumb_params(grid):
    """Earth Engine getThumbURL parameters for exactly this grid."""
    s = grid["scale"]
    return {"crs": grid["crs"], "crs_transform": [s, 0, grid["x0"], 0, -s, grid["y0"]],
            "dimensions": f"{grid['width']}x{grid['height']}", "format": "png"}


def pixel_to_lonlat(grid, px, py):
    """Bilinear interpolation of the corners, the same formula the dashboard uses."""
    fx, fy = px / grid["width"], py / grid["height"]
    c = grid["corners_lonlat"]
    top = [c["nw"][i] + (c["ne"][i] - c["nw"][i]) * fx for i in (0, 1)]
    bot = [c["sw"][i] + (c["se"][i] - c["sw"][i]) * fx for i in (0, 1)]
    return [top[i] + (bot[i] - top[i]) * fy for i in (0, 1)]
