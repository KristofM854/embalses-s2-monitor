"""Fetch new Sentinel-2 observations, render images, write the tables.

    python -m pipeline.update                    # incremental (normal use)
    python -m pipeline.update --full             # rebuild from config.FIRST_DATE
    python -m pipeline.update --max-images 0     # tables only
"""
import argparse
import os
import shutil
import time
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta

from . import config as C
from . import gee, store

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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
    ap.add_argument("--data-dir", default=os.path.join(ROOT, "data"))
    ap.add_argument("--images-dir", default=os.path.join(ROOT, "images"))
    a = ap.parse_args(argv)

    t0 = time.monotonic()
    gee.init(a.project)
    csv = os.path.join(a.data_dir, "reservoir_ndci.csv")
    df = store.load(csv)
    n_before = len(df)
    outlines = {}

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
            shutil.rmtree(os.path.join(a.images_dir, name), ignore_errors=True)
        print(f"{name}: {n_total} water pixels; querying {start} to {a.end}", flush=True)
        for s, e in store.date_chunks(start, a.end, C.CHUNK_MONTHS):
            new = gee.scene_stats(name, geom, n_total, s, e)
            df = store.upsert(df, new, name, s, e)
            print(f"  {s} to {e}: {len(new)} scenes", flush=True)
        # Write after every reservoir so a later failure keeps finished work
        store.write_outputs(df, a.data_dir, a.images_dir)
        if backfill:
            gee.mark_backfilled(name, a.data_dir)

    # Images: newest first, so the dashboard is current even during a backfill
    todo = [(r, d) for r, d, f in
            zip(df["reservoir"], df["date"], df["frac_valid"])
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
            gee.render_images(outlines[r], d, p("rgb"), p("ndci"))
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

    meta = store.write_outputs(df, a.data_dir, a.images_dir)
    if (df["frac_valid"] > 1.001).any():
        print("::warning::Some rows have frac_valid > 1: pixel counts of statistics and outline "
              "disagree.", flush=True)
    done = len(todo) - len(failed) - len(skipped)
    lines = [f"Rows: {n_before} -> {len(df)}",
             f"Images rendered: {done}, failed: {len(failed)}, left for later runs: {remaining}"]
    for name, m in meta["reservoirs"].items():
        lines.append(f"{name}: {m['first_date']} to {m['last_date']}, {m['n_dates']} dates, "
                     f"{m['n_dates_50pct_clear']} at >=50% clear, {m['n_images']} with images")
    print("\n".join(lines))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as fh:
            fh.write("### Sentinel-2 update\n\n" + "\n".join(f"- {l}" for l in lines) + "\n")
    # Fail the run only if many images failed (e.g. Earth Engine outage)
    attempted = len(todo) - len(skipped)
    return 1 if fatal or (attempted and len(failed) > 0.5 * attempted) else 0


if __name__ == "__main__":
    sys.exit(main())
