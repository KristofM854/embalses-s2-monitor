"""All tunable settings in one place.

Changing a reservoir seed or OUTLINE, or adding a hand-drawn outline in
data/aoi_overrides/, is detected on the next run: the outline is rebuilt and
that reservoir's whole series and images are recomputed automatically.
"""

DEFAULT_PROJECT = "hab-quiz-ae5a8"   # overridden by EE_PROJECT or the service account key

# Seeds near each dam. The outline is the largest Sentinel-2 water body
# within radius_m of the seed (see OUTLINE). The radius only limits the search;
# a run warns if the reservoir reaches the edge of the search circle.
# Valdesia: hydro plant location (Global Energy Monitor). Hatillo: dam (Wikipedia).
RESERVOIRS = {
    "Valdesia": {"lon": -70.2762, "lat": 18.3917, "radius_m": 12000},
    "Hatillo": {"lon": -70.2004, "lat": 19.0336, "radius_m": 20000},
}

FIRST_DATE = "2017-01-01"  # S2 L2A in Earth Engine is sparse before late 2018; empty chunks are fine
LOOKBACK_DAYS = 45         # each run re-queries this window to catch late / reprocessed scenes

# Outline from Sentinel-2 itself: share of clear observations in which a pixel
# is water (MNDWI = (B3 - B11)/(B3 + B11) > mndwi_min). MNDWI stays positive
# over algae much better than NIR-based indices, so blooms are not cut out.
# A fixed period keeps the outline reproducible.
# Bump to force every outline (and with it every series) to be recomputed after a
# change in how outlines or pixel counts are computed.
# 2: polygons only, edge check on final outline, unweighted pixel counts.
OUTLINE_VERSION = 2

OUTLINE = {
    "start": "2019-01-01", "end": "2026-01-01",
    "mndwi_min": 0.0,
    "water_freq_min": 0.75,   # water in >= 75 % of clear looks; lower = include more drawdown zone
    "min_obs": 20,            # clear looks needed for a pixel to count
    "scale": 10,              # m, vectorisation grid (B11 is resampled bilinearly from 20 m)
    "shore_buffer_m": 20,     # inward buffer against mixed shore pixels (one 20 m pixel)
    "simplify_m": 10,
}
CS_THRESHOLD = 0.6    # Cloud Score+ cs_cdf, higher = clearer
SCALE = 20            # m, native resolution of B5
CRS = "EPSG:32619"    # UTM 19N, covers both reservoirs
NIR_FLAG = 0.05       # B8 reflectance above this = scum, vegetation, glint or residual cloud
NDCI_FLAGS = (0.1, 0.2)  # report fraction of clear water pixels above these NDCI values
CHUNK_MONTHS = 3      # months per Earth Engine request

# Images
IMG_MIN_VALID = 0.3   # render images only when at least this fraction of the water is clear
IMG_DIM = 800         # px, longest side
IMG_QUALITY = 80      # WebP quality
NDCI_VIS = (-0.1, 0.4)
NDCI_PALETTE = ["0000ff", "00ffff", "00ff00", "ffff00", "ff0000"]
