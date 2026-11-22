"""Outline caching, hand-drawn overrides and automatic rebuild (Earth Engine mocked)."""
import json

import pandas as pd
import pytest

from pipeline import config as C
from pipeline import gee, update

SQUARE = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}


@pytest.fixture
def mocked(monkeypatch):
    calls = {"build": 0, "count": 0}

    def build(lon, lat, r):
        calls["build"] += 1
        return SQUARE, False

    def count(geom):
        calls["count"] += 1
        return 500 if geom["type"] == "MultiPolygon" else 1000

    monkeypatch.setattr(gee, "build_outline", build)
    monkeypatch.setattr(gee, "count_pixels", count)
    return calls


def test_cache_and_rebuild_on_param_change(tmp_path, mocked, monkeypatch):
    g, n, backfill = gee.load_or_build_outline("Hatillo", tmp_path)
    assert (n, backfill, mocked["build"]) == (1000, True, 1)
    # until the series is backfilled, keep asking for it
    assert gee.load_or_build_outline("Hatillo", tmp_path)[2] is True
    gee.mark_backfilled("Hatillo", tmp_path)
    assert gee.load_or_build_outline("Hatillo", tmp_path)[2] is False
    assert mocked["build"] == 1
    monkeypatch.setitem(C.OUTLINE, "water_freq_min", 0.6)
    assert gee.load_or_build_outline("Hatillo", tmp_path)[2] is True
    assert mocked["build"] == 2


def test_override_used_and_merged(tmp_path, mocked):
    (tmp_path / "aoi_overrides").mkdir()
    fc = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {}, "geometry": SQUARE},
        {"type": "Feature", "properties": {}, "geometry": SQUARE}]}
    (tmp_path / "aoi_overrides" / "Valdesia.geojson").write_text(json.dumps(fc))
    g, n, backfill = gee.load_or_build_outline("Valdesia", tmp_path)
    assert g["type"] == "MultiPolygon" and n == 500 and backfill and mocked["build"] == 0
    cached = json.loads((tmp_path / "aoi_Valdesia.geojson").read_text())
    assert cached["features"][0]["properties"]["params"]["method"] == "override"


def test_update_recomputes_series_after_outline_change(tmp_path, mocked, monkeypatch):
    queried = []
    monkeypatch.setattr(gee, "init", lambda project=None: None)
    monkeypatch.setattr(gee, "render_images", lambda *a: None)
    monkeypatch.setattr(gee, "scene_stats", lambda name, geom, n, s, e: queried.append((name, s))
                        or pd.DataFrame({"reservoir": [name], "date": [s], "ndci_p90": [0.1],
                                         "n_valid": [n // 2], "n_total": [n], "scene": ["S"]}))
    monkeypatch.setattr(C, "FIRST_DATE", "2024-01-01")
    args = ["--data-dir", str(tmp_path), "--images-dir", str(tmp_path / "img"),
            "--end", "2024-07-01", "--max-images", "0"]
    update.main(args)
    first = [s for _, s in queried]
    assert first.count("2024-01-01") == 2           # both reservoirs from FIRST_DATE
    queried.clear()
    update.main(args)
    assert all(s > "2024-01-01" for _, s in queried)  # incremental now

    # A team member adds a hand-drawn outline for Valdesia
    (tmp_path / "aoi_overrides").mkdir()
    (tmp_path / "aoi_overrides" / "Valdesia.geojson").write_text(json.dumps(SQUARE))
    queried.clear()
    update.main(args)
    assert ("Valdesia", "2024-01-01") in queried and ("Hatillo", "2024-01-01") not in queried
    df = pd.read_csv(tmp_path / "reservoir_ndci.csv")
    assert set(df[df.reservoir == "Valdesia"].n_total) == {1000}  # SQUARE -> 1000 in mock
