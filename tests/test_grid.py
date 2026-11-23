import json
import os

from pyproj import Transformer

from pipeline import grid

FIX = os.path.join(os.path.dirname(__file__), "fixtures")


def test_grid_bilinear_error_below_one_metre():
    from pipeline import gee
    for name in ("Hatillo", "Valdesia"):
        g = gee.polygons_only(json.load(open(f"{FIX}/aoi_{name}_v1.geojson"))["features"][0]["geometry"])
        gr = grid.image_grid(g, "EPSG:32619", 800)
        assert max(gr["width"], gr["height"]) <= 800 and gr["scale"] >= 10
        to_ll = Transformer.from_crs("EPSG:32619", "EPSG:4326", always_xy=True)
        to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32619", always_xy=True)
        worst = 0
        for px in (0, gr["width"] / 3, gr["width"] / 2, gr["width"]):
            for py in (0, gr["height"] / 2, gr["height"]):
                exact = (gr["x0"] + px * gr["scale"], gr["y0"] - py * gr["scale"])
                lon, lat = grid.pixel_to_lonlat(gr, px, py)
                x, y = to_utm.transform(lon, lat)
                worst = max(worst, abs(x - exact[0]), abs(y - exact[1]))
        assert worst < 1.0, (name, worst)
        assert to_ll  # corners exist
        p = grid.thumb_params(gr)
        assert p["dimensions"] == f"{gr['width']}x{gr['height']}"
