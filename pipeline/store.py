"""Table handling without Earth Engine: merge, de-duplicate, export."""
import json
import os
from datetime import datetime, timezone

import pandas as pd
from openpyxl.styles import Alignment

from . import metadata as M

COLUMNS = [
    "reservoir", "date", "ndci_p50", "ndci_p90", "ndci_mean",
    "frac_ndci_gt_0.1", "frac_ndci_gt_0.2", "b4_p50", "b8_p50", "frac_high_nir",
    "n_valid", "n_total", "frac_valid", "scene",
]
ROUND = {"ndci_p50": 4, "ndci_p90": 4, "ndci_mean": 4, "frac_ndci_gt_0.1": 4,
         "frac_ndci_gt_0.2": 4, "b4_p50": 4, "b8_p50": 4, "frac_high_nir": 4,
         "frac_valid": 4}

def empty():
    return pd.DataFrame(columns=COLUMNS)


def load(path):
    if not os.path.exists(path):
        return empty()
    df = pd.read_csv(path, dtype={"date": str, "scene": str}, comment="#")
    return df.reindex(columns=COLUMNS)


def date_chunks(start, end, months):
    """[start, end) split at calendar month boundaries every `months` months."""
    edges = pd.date_range(start, end, freq=f"{months}MS").strftime("%Y-%m-%d").tolist()
    edges = [e for e in edges if start < e < end]
    edges = [start] + edges + [end]
    return list(zip(edges[:-1], edges[1:]))


def incremental_start(df, reservoir, lookback_days, default):
    d = df.loc[df["reservoir"] == reservoir, "date"]
    if d.empty:
        return default
    s = (pd.Timestamp(d.max()) - pd.Timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    return max(s, default)


def dedupe(df):
    """Same reservoir seen in two granules on one day: keep the one with more clear pixels."""
    df = df[df["n_valid"] > 0]
    df = df.sort_values("n_valid", ascending=False, kind="stable")
    return df.drop_duplicates(subset=["reservoir", "date"], keep="first")


def upsert(old, new, reservoir, start, end):
    """Replace rows of `reservoir` in [start, end) by `new`."""
    in_window = ((old["reservoir"] == reservoir) & (old["date"] >= start) & (old["date"] < end))
    parts = [p for p in (old[~in_window], new) if not p.empty]
    if not parts:
        return empty()
    df = pd.concat([p.reindex(columns=COLUMNS) for p in parts], ignore_index=True)
    return tidy(df)


def tidy(df):
    df = dedupe(df.reindex(columns=COLUMNS))
    df = df.sort_values(["reservoir", "date"]).reset_index(drop=True)
    for c, n in ROUND.items():
        df[c] = pd.to_numeric(df[c], errors="coerce").round(n)
    for c in ("n_valid", "n_total"):
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
    df["frac_valid"] = (df["n_valid"] / df["n_total"]).astype(float).round(ROUND["frac_valid"])
    return df.reindex(columns=COLUMNS)


TEMP_SHEET = "Temperatura · Temperature"
TEMP_COLUMNS = [c[0] for c in M.TEMP_COLUMNS]


def load_temp(path):
    if not os.path.exists(path):
        return pd.DataFrame(columns=TEMP_COLUMNS)
    return pd.read_csv(path, dtype={"date": str, "scene": str}, comment="#").reindex(columns=TEMP_COLUMNS)


def tidy_temp(df):
    df = df.reindex(columns=TEMP_COLUMNS)
    for c in ("n_valid", "n_total"):
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
    df = df[df["n_valid"] > 0]
    df["frac_valid"] = (df["n_valid"] / df["n_total"]).astype(float).round(4)
    for c in ("temp_p10", "temp_p50", "temp_p90"):
        df[c] = pd.to_numeric(df[c], errors="coerce").round(2)
    df = (df.sort_values("n_valid", ascending=False, kind="stable")
            .drop_duplicates(subset=["reservoir", "date"], keep="first"))
    return df.sort_values(["reservoir", "date"]).reset_index(drop=True)


def upsert_temp(old, new, reservoir, start, end):
    keep = ~((old["reservoir"] == reservoir) & (old["date"] >= start) & (old["date"] < end))
    parts = [p.reindex(columns=TEMP_COLUMNS) for p in (old[keep], new) if not p.empty]
    return tidy_temp(pd.concat(parts, ignore_index=True)) if parts else old.iloc[0:0]


def write_columnar(df, path):
    cols = {c: [None if pd.isna(v) else (int(v) if c in ("n_valid", "n_total") else v)
                for v in df[c].tolist()] for c in df.columns}
    with open(path, "w") as fh:
        json.dump(cols, fh, separators=(",", ":"))


def predict_passes(recent, repeat_days, horizon_days):
    """Future pass dates from recent acquisitions: each spacecraft repeats its
    ground track every `repeat_days`. Anchored on the last observed date, so the
    result only changes when new acquisitions are seen."""
    from datetime import date, timedelta
    out = set()
    for sat, d in recent:
        t = date.fromisoformat(d)
        for k in range(1, horizon_days // repeat_days + 2):
            out.add(((t + timedelta(days=k * repeat_days)).isoformat(), sat))
    last = max((d for _, d in recent), default=None)
    seen = {(d, s) for s, d in recent}
    # keep only dates after the last observation that have not been observed
    return sorted(p for p in out if last is None or (p[0] > last and p not in seen))


def image_name(reservoir, date, kind):
    return f"{reservoir}/{date}_{kind}.webp"


def has_images(images_dir, reservoir, date):
    return all(os.path.exists(os.path.join(images_dir, image_name(reservoir, date, k)))
               for k in ("rgb", "ndci"))


def csv_header(updated, general=M.GENERAL, columns=M.COLUMNS, title="Sentinel-2 NDCI, Valdesia y Hatillo"):
    """Comment lines above the CSV table. Read with comment="#" (pandas) or
    comment.char = "#" (R)."""
    lines = [f"{title}. Updated / Actualizado: {updated}",
             "Lines starting with # are metadata / Las líneas que empiezan con # son metadatos."]
    for en, es, txt_en, txt_es in general:
        lines += [f"{en}: {txt_en}", f"{es}: {txt_es}"]
    lines += ["Columns / Columnas: name | unit | description, how to read / "
              "nombre | unidad | descripción, cómo leerlo"]
    for n, u, en, es, r_en, r_es in columns:
        lines += [f"  {n} | {u} | EN: {en}" + (f" {r_en}" if r_en else ""),
                  f"  {n} | {u} | ES: {es}" + (f" {r_es}" if r_es else "")]
    return "".join(f"# {l}\n" for l in lines)


def write_csv(df, path, updated, **header):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(csv_header(updated, **header))
        df.to_csv(fh, index=False)


def write_xlsx(df, path, updated, temp=None):
    readme = pd.DataFrame(
        [("Updated", "Actualizado", updated, updated)] + list(M.GENERAL)
        + [(f"Temperature: {a}", f"Temperatura: {b}", c, d) for a, b, c, d in M.TEMP_GENERAL],
        columns=["Item", "Tema", "English", "Español"])
    cols = ["Column / Columna", "Unit / Unidad", "Description", "Descripción",
            "How to read it", "Cómo leerlo"]
    meta = pd.concat([
        pd.DataFrame(M.COLUMNS, columns=cols).assign(**{"Sheet / Hoja": "Valdesia, Hatillo"}),
        pd.DataFrame(M.TEMP_COLUMNS, columns=cols).assign(**{"Sheet / Hoja": TEMP_SHEET})])
    meta = meta[["Sheet / Hoja"] + cols]
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        readme.to_excel(xw, sheet_name="Léame · Read me", index=False)
        meta.to_excel(xw, sheet_name="Metadatos · Metadata", index=False)
        for name, g in df.groupby("reservoir"):
            g.to_excel(xw, sheet_name=name[:31], index=False)
        if temp is not None and not temp.empty:
            temp.to_excel(xw, sheet_name=TEMP_SHEET, index=False)
        for ws in xw.book.worksheets:  # readable column widths, wrapped text
            for col in ws.columns:
                width = min(max(len(str(c.value or "")) for c in col) + 2, 70)
                ws.column_dimensions[col[0].column_letter].width = width
                if width == 70:
                    for c in col:
                        c.alignment = Alignment(wrap_text=True, vertical="top")
            ws.freeze_panes = "A2"


def write_outputs(df, data_dir, images_dir, temp=None):
    os.makedirs(data_dir, exist_ok=True)
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    write_csv(df, os.path.join(data_dir, "reservoir_ndci.csv"), updated)
    if temp is not None:
        write_csv(temp, os.path.join(data_dir, "landsat_temperature.csv"), updated,
                  general=M.TEMP_GENERAL, columns=M.TEMP_COLUMNS,
                  title="Landsat 8/9 water surface temperature, Valdesia y Hatillo")
        write_columnar(temp, os.path.join(data_dir, "temperature.json"))
    write_xlsx(df, os.path.join(data_dir, "reservoir_ndci.xlsx"), updated, temp)
    keys = ("name", "unit", "en", "es", "read_en", "read_es")
    with open(os.path.join(data_dir, "columns.json"), "w") as fh:
        json.dump([dict(zip(keys, c)) for c in M.COLUMNS], fh, ensure_ascii=False, indent=1)

    # Compact column-oriented JSON for the dashboard
    img = [has_images(images_dir, r, d) for r, d in zip(df["reservoir"], df["date"])]
    cols = {c: [None if pd.isna(v) else (int(v) if c in ("n_valid", "n_total") else v)
                for v in df[c].tolist()] for c in COLUMNS}
    cols["img"] = img
    with open(os.path.join(data_dir, "ndci.json"), "w") as fh:
        json.dump(cols, fh, separators=(",", ":"))

    meta = {"updated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "reservoirs": {}}
    for name, g in df.groupby("reservoir"):
        meta["reservoirs"][name] = {
            "first_date": g["date"].min(), "last_date": g["date"].max(),
            "n_dates": int(len(g)), "n_dates_50pct_clear": int((g["frac_valid"] >= 0.5).sum()),
            "n_images": int(sum(i for i, r in zip(img, df["reservoir"]) if r == name)),
        }
    with open(os.path.join(data_dir, "meta.json"), "w") as fh:
        json.dump(meta, fh, indent=2)
    return meta
