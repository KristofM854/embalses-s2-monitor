import json

import pandas as pd

from pipeline import store


def rows(reservoir, dates, n_valid=100, p90=0.1):
    return pd.DataFrame({"reservoir": reservoir, "date": dates, "ndci_p50": 0.0,
                         "ndci_p90": p90, "n_valid": n_valid, "n_total": 200,
                         "frac_valid": n_valid / 200, "scene": "x"})


def test_date_chunks_cover_range_without_gaps():
    ch = store.date_chunks("2017-01-15", "2017-08-02", 3)
    assert ch[0][0] == "2017-01-15" and ch[-1][1] == "2017-08-02"
    assert all(a[1] == b[0] for a, b in zip(ch, ch[1:]))
    assert store.date_chunks("2024-01-01", "2024-01-10", 3) == [("2024-01-01", "2024-01-10")]


def test_incremental_start():
    df = store.tidy(rows("A", ["2024-03-01", "2024-05-01"]))
    assert store.incremental_start(df, "A", 45, "2017-01-01") == "2024-03-17"
    assert store.incremental_start(df, "B", 45, "2017-01-01") == "2017-01-01"


def test_upsert_replaces_window_only_and_keeps_other_reservoir():
    old = store.tidy(pd.concat([rows("A", ["2024-01-01", "2024-02-01", "2024-03-01"]),
                                rows("B", ["2024-02-01"])]))
    new = rows("A", ["2024-02-05"], p90=0.3)
    out = store.upsert(old, new, "A", "2024-02-01", "2024-03-01")
    a = out[out.reservoir == "A"]
    assert a.date.tolist() == ["2024-01-01", "2024-02-05", "2024-03-01"]
    assert (out.reservoir == "B").sum() == 1


def test_dedupe_keeps_granule_with_more_clear_pixels_and_drops_empty():
    df = pd.concat([rows("A", ["2024-01-01"], n_valid=50, p90=0.1),
                    rows("A", ["2024-01-01"], n_valid=150, p90=0.2),
                    rows("A", ["2024-01-06"], n_valid=0)])
    out = store.tidy(df)
    assert len(out) == 1 and out.ndci_p90.iloc[0] == 0.2


def test_write_outputs(tmp_path):
    df = store.tidy(rows("Hatillo", ["2024-01-01", "2024-01-06"]))
    img = tmp_path / "img" / "Hatillo"
    img.mkdir(parents=True)
    for k in ("rgb", "ndci"):
        (img / f"2024-01-06_{k}.webp").write_bytes(b"x")
    meta = store.write_outputs(df, tmp_path / "data", tmp_path / "img")
    j = json.loads((tmp_path / "data" / "ndci.json").read_text())
    assert j["img"] == [False, True] and j["n_valid"] == [100, 100]
    assert meta["reservoirs"]["Hatillo"]["n_images"] == 1
    back = store.load(tmp_path / "data" / "reservoir_ndci.csv")
    assert len(back) == 2 and (tmp_path / "data" / "reservoir_ndci.xlsx").exists()


def test_metadata_in_csv_and_excel(tmp_path):
    from openpyxl import load_workbook
    from pipeline import metadata as M
    df = store.tidy(rows("Hatillo", ["2024-01-01"]))
    store.write_outputs(df, tmp_path, tmp_path / "img")
    text = (tmp_path / "reservoir_ndci.csv").read_text(encoding="utf-8")
    header = [l for l in text.splitlines() if l.startswith("#")]
    assert all(l.startswith("# ") for l in header) and any("frac_high_nir |" in l for l in header)
    assert text.splitlines()[len(header)].startswith("reservoir,date,")
    assert len(store.load(tmp_path / "reservoir_ndci.csv")) == 1   # header skipped on read
    wb = load_workbook(tmp_path / "reservoir_ndci.xlsx")
    assert wb.sheetnames[:2] == ["Léame · Read me", "Metadatos · Metadata"]
    meta_cols = [r[0].value for r in wb["Metadatos · Metadata"].iter_rows(min_row=2)]
    assert meta_cols == [c[0] for c in M.COLUMNS] == store.COLUMNS
    cols = json.loads((tmp_path / "columns.json").read_text())
    assert [c["name"] for c in cols] == store.COLUMNS
