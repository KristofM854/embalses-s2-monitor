"""Fetch new satellite observations, render images and maps, write the tables.

    python -m pipeline.update                    # incremental (normal use)
    python -m pipeline.update --full             # rebuild from config.FIRST_DATE
    python -m pipeline.update --max-images 0     # tables only

Runs every two hours. When nothing new has arrived, no file is written, so
there is nothing to commit and the dashboard is not redeployed.
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone

from . import config as C
from . import gee, store
from . import grid as G

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path) as fh:
        return json.load(fh)


def write_json_if_changed(path, obj):
    text = json.dumps(obj, indent=1, sort_keys=True)
    if os.path.exists(path) and open(path).read() == text:
        return False
    with open(path, "w") as fh:
        fh.write(text)
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--project", help="Earth Engine Cloud project (default: key or config)")
    ap.add_argument("--full", action="store_true", help=f"re-query everything from {C.FIRST_DATE}")
    ap.add_argument("--start", help="re-query from this date (YYYY-MM-DD)")
    ap.add_argument("--end", default=(date.today() + timedelta(days=1)).isoformat())
    ap.add_argument("--max-images", type=int, default=300,
                    help="max reservoir-dates to render this run (newest first)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--time-budget-min", type=float, default=240,
                    help="stop starting new images after this many minutes (rest: next run)")
    ap.add_argument("--skip-extras", action="store_true",
                    help="skip Landsat, summary maps and pass prediction")
    ap.add_argument("--data-dir", default=os.path.join(ROOT, "data"))
    ap.add_argument("--images-dir", default=os.path.join(ROOT, "images"))
    a = ap.parse_args(argv)

    t0 = time.monotonic()
    gee.init(a.project)
    os.makedirs(a.data_dir, exist_ok=True)
    df = store.load(os.path.join(a.data_dir, "reservoir_ndci.csv"))
    temp = store.load_temp(os.path.join(a.data_dir, "landsat_temperature.csv"))
    before = (store.tidy(df).to_csv(index=False), store.tidy_temp(temp).to_csv(index=False))
    n_before = len(df)
    grids_path = os.path.join(a.data_dir, "image_grid.json")
    grids = read_json(grids_path, {})
    lsat_path = os.path.join(a.data_dir, "landsat_outline.json")
    lsat = read_json(lsat_path, {})
    outlines, backfilled, files_changed = {}, set(), False

    for name in C.RESERVOIRS:
        geom, n_total, backfill = gee.load_or_build_outline(name, a.data_dir)
        outlines[name] = geom
        start = (C.FIRST_DATE if a.full else
                 a.start or store.incremental_start(df, name, C.LOOKBACK_DAYS, C.FIRST_DATE))
        if backfill:
            # New outline: old rows and images were computed on the old one
            print(f"{name}: new outline, computing the whole series", flush=True)
            start = C.FIRST_DATE
            df = df[df["reservoir"] != name]
            backfilled.add(name)
        print(f"{name}: {n_total} water pixels; querying {start} to {a.end}", flush=True)
        for s, e in store.date_chunks(start, a.end, C.CHUNK_MONTHS):
            new = gee.scene_stats(name, geom, n_total, s, e)
            df = store.upsert(df, new, name, s, e)
            print(f"  {s} to {e}: {len(new)} scenes", flush=True)

        # Image grid: all images of a reservoir share it; a new grid means re-rendering
        grid = G.image_grid(geom, C.CRS, C.IMG_DIM)
        if backfill or grids.get(name) != grid:
            print(f"{name}: new image grid, images will be re-rendered", flush=True)
            shutil.rmtree(os.path.join(a.images_dir, name), ignore_errors=True)
            for k in ("mean", "freq"):
                p = os.path.join(a.images_dir, "maps", f"{name}_{k}.webp")
                if os.path.exists(p):
                    os.remove(p)
            grids[name] = grid
            files_changed = True

        # Landsat water temperature
        if not a.skip_extras:
            key = hashlib.sha1(json.dumps([geom, C.LANDSAT["extra_buffer_m"]]).encode()).hexdigest()
            if lsat.get(name, {}).get("key") != key:
                g_t, n_t = gee.landsat_outline(geom)
                lsat[name] = {"key": key, "geometry": g_t, "n_total": n_t}
                temp = temp[temp["reservoir"] != name]
                files_changed = True
            g_t, n_t = lsat[name]["geometry"], lsat[name]["n_total"]
            lstart = (C.LANDSAT["first_date"] if a.full else
                      store.incremental_start(temp, name, C.LANDSAT["lookback_days"],
                                              C.LANDSAT["first_date"]))
            print(f"{name}: Landsat temperature, {n_t} pixels; querying {lstart} to {a.end}", flush=True)
            for s, e in store.date_chunks(lstart, a.end, C.LANDSAT["chunk_months"]):
                new = gee.landsat_stats(name, g_t, n_t, s, e)
                temp = store.upsert_temp(temp, new, name, s, e)
        if backfill:
            store.write_outputs(df, a.data_dir, a.images_dir, temp)  # keep finished work
            gee.mark_backfilled(name, a.data_dir)

    df = store.tidy(df)
    temp = store.tidy_temp(temp)
    data_changed = (df.to_csv(index=False), temp.to_csv(index=False)) != before

    # Daily images: newest first, so the dashboard is current even during a backfill
    todo = [(r, d) for r, d, f in zip(df["reservoir"], df["date"], df["frac_valid"])
            if f >= C.IMG_MIN_VALID and not store.has_images(a.images_dir, r, d)]
    todo.sort(key=lambda t: t[1], reverse=True)
    remaining = max(len(todo) - a.max_images, 0)
    todo = todo[:a.max_images]
    print(f"Rendering {len(todo)} image pairs ({remaining} left for later runs)", flush=True)
    failed, skipped, fatal, reported = [], [], [], []
    deadline = t0 + 60 * a.time_budget_min

    def job(r, d):
        if fatal or time.monotonic() > deadline:
            return "skipped"
        p = lambda k: os.path.join(a.images_dir, store.image_name(r, d, k))
        try:
            gee.render_images(outlines[r], d, p("rgb"), p("ndci"), grids[r])
        except gee.PermanentError:
            fatal.append((r, d))  # set in the worker, so other workers stop at once
            raise
        return "ok"

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(job, r, d): (r, d) for r, d in todo}
        for i, f in enumerate(as_completed(futs), 1):
            try:
                if f.result() == "skipped":
                    skipped.append(futs[f])
            except gee.PermanentError as e:
                if not reported:
                    print(f"::error::Images stopped: {str(e)[:300]}. The service account needs the "
                          "role 'Earth Engine Resource Writer' (see docs/SETUP.md).", flush=True)
                    reported.append(True)
            except Exception as e:  # one bad scene must not stop the run
                failed.append(futs[f])
                print(f"  image failed {futs[f]}: {str(e)[:200]}", flush=True)
            if i % 25 == 0:
                print(f"  {i}/{len(todo)} images", flush=True)
    remaining += len(skipped) + len(fatal)
    failed += fatal
    done = len(todo) - len(failed) - len(skipped)

    if not a.skip_extras and not fatal:
        files_changed |= update_maps(a, df, outlines, grids, backfilled)
        files_changed |= update_passes(a, outlines)
    files_changed |= write_json_if_changed(grids_path, grids)
    files_changed |= write_json_if_changed(lsat_path, lsat)

    if data_changed or done or files_changed:
        meta = store.write_outputs(df, a.data_dir, a.images_dir, temp)
    else:
        print("No new data: nothing written.", flush=True)
        meta = read_json(os.path.join(a.data_dir, "meta.json"), {"reservoirs": {}})
    if (df["frac_valid"] > 1.001).any():
        print("::warning::Some rows have frac_valid > 1: pixel counts of statistics and outline "
              "disagree.", flush=True)

    lines = [f"Rows: {n_before} -> {len(df)}; Landsat rows: {len(temp)}",
             f"Images rendered: {done}, failed: {len(failed)}, left for later runs: {remaining}"]
    for name, m in meta.get("reservoirs", {}).items():
        lines.append(f"{name}: {m['first_date']} to {m['last_date']}, {m['n_dates']} dates, "
                     f"{m['n_dates_50pct_clear']} at >=50% clear, {m['n_images']} with images")
    print("\n".join(lines))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as fh:
            fh.write("### Satellite update\n\n" + "\n".join(f"- {l}" for l in lines) + "\n")
    attempted = len(todo) - len(skipped)
    return 1 if fatal or (attempted and len(failed) > 0.5 * attempted) else 0


def update_maps(a, df, outlines, grids, backfilled):
    """Summary maps (typical NDCI, how often clearly green). Re-rendered monthly."""
    path = os.path.join(a.data_dir, "maps.json")
    maps = read_json(path, {})
    now = datetime.now(timezone.utc)
    changed = False
    for name, geom in outlines.items():
        m = maps.get(name, {})
        files = [os.path.join(a.images_dir, "maps", f"{name}_{k}.webp") for k in ("mean", "freq")]
        fresh = (m.get("grid") == grids[name] and name not in backfilled
                 and all(os.path.exists(f) for f in files)
                 and now - datetime.fromisoformat(m["rendered_utc"]) < timedelta(days=C.MAPS["refresh_days"]))
        if fresh:
            continue
        good = df[(df["reservoir"] == name) & (df["frac_valid"] >= 0.5) & (df["date"] >= C.MAPS["start"])]
        ids = good["scene"].dropna().tolist()
        print(f"{name}: rendering summary maps from {len(ids)} usable images", flush=True)
        try:
            rng = gee.render_maps(geom, grids[name], ids, now.strftime("%Y-%m-%d"), *files)
        except Exception as e:  # maps are optional; try again next run
            print(f"::warning::{name}: summary maps failed: {str(e)[:200]}", flush=True)
            continue
        maps[name] = {"rendered_utc": now.isoformat(timespec="seconds"), "grid": grids[name],
                      "n_images": len(ids), "period": [good["date"].min(), good["date"].max()],
                      "mean_range": rng, "green_ndci": C.MAPS["green_ndci"],
                      "freq_max": C.MAPS["freq_max"], "palette": C.MAPS["palette"]}
        changed = True
    return write_json_if_changed(path, maps) or changed


def update_passes(a, outlines):
    """Predicted Sentinel-2 and Landsat passes for the next weeks."""
    out = {}
    for name, geom in outlines.items():
        try:
            recent = gee.retry(gee.recent_passes, geom)
        except Exception as e:
            print(f"::warning::{name}: pass prediction failed: {str(e)[:200]}", flush=True)
            return False
        out[name] = {k: store.predict_passes(v, C.PASS_REPEAT_DAYS[k], C.PASS_HORIZON_DAYS)
                     for k, v in recent.items()}
    return write_json_if_changed(os.path.join(a.data_dir, "passes.json"), out)


if __name__ == "__main__":
    sys.exit(main())
