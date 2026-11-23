"""Landsat, summary maps, pass prediction and 'no new data -> no files written'."""
import json
import os

import pandas as pd

from pipeline import gee, store, update

SQUARE = {"type": "Polygon", "coordinates": [[[-70.3, 18.3], [-70.2, 18.3], [-70.2, 18.4],
                                              [-70.3, 18.4], [-70.3, 18.3]]]}


def test_predict_passes():
    recent = [("Sentinel-2B", "2026-11-08"), ("Sentinel-2C", "2026-11-11"), ("Sentinel-2B", "2026-11-18")]
    p = store.predict_passes(recent, 10, 20)
    assert ("2026-11-21", "Sentinel-2C") in p and ("2026-11-28", "Sentinel-2B") in p
    assert all(d > "2026-11-18" for d, _ in p)
    assert ("2026-11-18", "Sentinel-2B") not in p


def test_extras_and_no_op_run(tmp_path, monkeypatch):
    calls = {"maps": 0, "landsat": 0}
    monkeypatch.setattr(gee, "init", lambda project=None: None)
    monkeypatch.setattr(gee, "load_or_build_outline", lambda name, d: (SQUARE, 100, False))
    monkeypatch.setattr(gee, "mark_backfilled", lambda name, d: None)
    monkeypatch.setattr(gee, "scene_stats", lambda name, g, n, s, e: pd.DataFrame(
        {"reservoir": [name], "date": ["2024-02-01"], "ndci_p90": [0.1], "n_valid": [80],
         "n_total": [n], "scene": ["S2"]}) if s <= "2024-02-01" < e else pd.DataFrame())
    monkeypatch.setattr(gee, "landsat_outline", lambda g: (SQUARE, 50))

    def lstats(name, g, n, s, e):
        calls["landsat"] += 1
        if not s <= "2024-02-05" < e:
            return pd.DataFrame()
        return pd.DataFrame({"reservoir": [name], "date": ["2024-02-05"], "temp_p10": [26.0],
                             "temp_p50": [27.123], "temp_p90": [28.0], "n_valid": [40],
                             "n_total": [n], "spacecraft": ["LANDSAT_9"], "scene": ["LC09"]})
    monkeypatch.setattr(gee, "landsat_stats", lstats)

    def maps(geom, grid, ids, end, p1, p2):
        calls["maps"] += 1
        for p in (p1, p2):
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "wb").write(b"x")
        return [0.0, 0.1]
    monkeypatch.setattr(gee, "render_maps", maps)
    monkeypatch.setattr(gee, "recent_passes", lambda g: {
        "s2": [("Sentinel-2B", "2024-02-01")], "landsat": [("LANDSAT_9", "2024-02-05")]})
    monkeypatch.setattr(gee, "render_images", lambda *a: None)

    d = tmp_path / "data"
    args = ["--data-dir", str(d), "--images-dir", str(tmp_path / "img"), "--start", "2024-01-01",
            "--end", "2024-03-01", "--max-images", "0"]
    monkeypatch.setitem(update.C.LANDSAT, "first_date", "2024-01-01")
    assert update.main(args) == 0
    t = store.load_temp(d / "landsat_temperature.csv")
    assert len(t) == 2 and t["temp_p50"].iloc[0] == 27.12 and t["frac_valid"].iloc[0] == 0.8
    assert calls["maps"] == 2
    grids = json.loads((d / "image_grid.json").read_text())
    assert set(grids) == {"Valdesia", "Hatillo"} and grids["Hatillo"]["scale"] >= 10
    passes = json.loads((d / "passes.json").read_text())
    assert passes["Hatillo"]["s2"][0] == ["2024-02-11", "Sentinel-2B"]
    assert "Temperatura · Temperature" in pd.ExcelFile(d / "reservoir_ndci.xlsx").sheet_names

    # Second run, nothing new: no file is touched, maps are not re-rendered
    stamp = {f: os.path.getmtime(d / f) for f in os.listdir(d)}
    assert update.main(args) == 0
    assert calls["maps"] == 2
    assert {f: os.path.getmtime(d / f) for f in os.listdir(d)} == stamp
