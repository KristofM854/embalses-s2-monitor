"""All tunable settings in one place.

Changing RESERVOIRS, OCC_MIN or SHORE_BUFFER_M changes the outline. Delete
data/aoi_<name>.geojson afterwards so it is rebuilt, and rebuild the whole
series (workflow input "full_rebuild"), otherwise frac_valid is inconsistent.
"""

DEFAULT_PROJECT = "hab-quiz-ae5a8"   # overridden by EE_PROJECT or the service account key

# Seeds near each dam. The outline is the largest JRC water body
# (occurrence >= OCC_MIN) within radius_m of the seed.
# Valdesia: hydro plant location (Global Energy Monitor). Hatillo: dam (Wikipedia).
RESERVOIRS = {
    "Valdesia": {"lon": -70.2762, "lat": 18.3917, "radius_m": 7000},
    "Hatillo": {"lon": -70.2004, "lat": 19.0336, "radius_m": 20000},
}

FIRST_DATE = "2017-01-01"  # S2 L2A in Earth Engine is sparse before late 2018; empty chunks are fine
LOOKBACK_DAYS = 45         # each run re-queries this window to catch late / reprocessed scenes

OCC_MIN = 80          # % of time the pixel was water in the JRC record
SHORE_BUFFER_M = 60   # inward buffer to drop mixed land/water pixels
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
