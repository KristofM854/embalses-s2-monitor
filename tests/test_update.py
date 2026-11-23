"""End-to-end run of pipeline.update with Earth Engine mocked out."""
import json

import pandas as pd

from pipeline import gee, update

SQUARE = {"type": "Polygon", "coordinates": [[[-70.3, 18.3], [-70.2, 18.3], [-70.2, 18.4], [-70.3, 18.4], [-70.3, 18.3]]]}


def fake_stats(name, geom, n_total, start, end):
    # fixed 5-day orbit grid, independent of the query window
    grid = pd.date_range("2024-01-01", "2025-01-01", freq="5D")
    dates = [d.strftime("%Y-%m-%d") for d in grid if start <= d.strftime("%Y-%m-%d") < end]
    return pd.DataFrame({"reservoir": name, "date": dates, "ndci_p50": 0.05, "ndci_p90": 0.12,
                         "n_valid": 80, "n_total": n_total, "frac_valid": 0.8, "scene": "S"})


def test_full_then_incremental(tmp_path, monkeypatch):
    calls, rendered = [], []
    monkeypatch.setattr(gee, "init", lambda project=None: None)
    monkeypatch.setattr(gee, "load_or_build_outline", lambda name, d: (SQUARE, 100, False))
    monkeypatch.setattr(gee, "mark_backfilled", lambda name, d: None)
    monkeypatch.setattr(gee, "scene_stats",
                        lambda *a: calls.append(a[3:]) or fake_stats(*a))

    def fake_render(geom, date, rgb, ndci, grid):
        rendered.append(date)
        for p in (rgb, ndci):
            import os
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "wb").write(b"x")
    monkeypatch.setattr(gee, "render_images", fake_render)

    args = ["--data-dir", str(tmp_path / "data"), "--images-dir", str(tmp_path / "img"), "--skip-extras"]
    assert update.main(args + ["--start", "2024-01-01", "--end", "2024-07-01",
                               "--max-images", "10"]) == 0
    assert calls[0] == ("2024-01-01", "2024-04-01")
    assert len(rendered) == 10 and max(rendered) == "2024-06-29"  # newest first

    calls.clear()
    assert update.main(args + ["--end", "2024-07-15", "--max-images", "0"]) == 0
    assert calls[0][0] == "2024-05-15"  # last date (06-29) minus 45 days
    j = json.loads((tmp_path / "data" / "ndci.json").read_text())
    assert sum(j["img"]) == 10 and len(set(zip(j["reservoir"], j["date"]))) == len(j["date"])


def test_permission_error_stops_images_without_retry(tmp_path, monkeypatch):
    import ee
    calls = []
    monkeypatch.setattr(gee, "init", lambda project=None: None)
    monkeypatch.setattr(gee, "load_or_build_outline", lambda name, d: (SQUARE, 100, False))
    monkeypatch.setattr(gee, "mark_backfilled", lambda name, d: None)
    monkeypatch.setattr(gee, "scene_stats", fake_stats)
    monkeypatch.setattr(gee.time, "sleep", lambda s: calls.append("sleep"))

    def denied(geom, date, grid):
        calls.append(date)
        raise ee.EEException("Permission 'earthengine.thumbnails.create' denied")
    monkeypatch.setattr(gee, "thumb_urls", denied)
    args = ["--data-dir", str(tmp_path / "data"), "--images-dir", str(tmp_path / "img"),
            "--start", "2024-01-01", "--end", "2024-04-01", "--workers", "1", "--skip-extras"]
    assert update.main(args) == 1                       # run is marked failed ...
    assert "sleep" not in calls and len(calls) == 1     # ... after one attempt, no retries
    assert (tmp_path / "data" / "reservoir_ndci.csv").exists()  # data still written


def test_time_budget_leaves_images_for_next_run(tmp_path, monkeypatch):
    rendered = []
    monkeypatch.setattr(gee, "init", lambda project=None: None)
    monkeypatch.setattr(gee, "load_or_build_outline", lambda name, d: (SQUARE, 100, False))
    monkeypatch.setattr(gee, "mark_backfilled", lambda name, d: None)
    monkeypatch.setattr(gee, "scene_stats", fake_stats)
    monkeypatch.setattr(gee, "render_images", lambda *a: rendered.append(a))
    args = ["--data-dir", str(tmp_path / "data"), "--images-dir", str(tmp_path / "img"),
            "--start", "2024-01-01", "--end", "2024-04-01", "--time-budget-min", "0", "--skip-extras"]
    assert update.main(args) == 0 and rendered == []
