from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw"        # read files
PROC_DATA_PATH = PROJECT_ROOT / "data" / "processed" # write files
CRS = 3310                                           # "California Albers" projection mapping, since we're using CA data

PARCEL_COLS = ["APN", "UseCode", "Land", "Imps", "LatestDocu", "SitusCity"] # columns from parcels.geojson we plan to keep

# These have to do with parcel "use codes" (i.e. what sector is it based in).
# We refer to this: https://propinfo.acgov.org/UseCodeList/ in order to figure out what to drop.
# A use code is 4 digits.
DROP_SERIES   = {"4", "6"}            # DROP IF THIS IS FIRST DIGIT. industrial, institutional
DROP_PREFIXES = {"73", "74", "75"}    # "..." FIRST TWO DIGITS. ondos, co-ops, deed-restricted affordable
DROP_CODES    = {"1130", "1150", "1160", "1600", "3900", "9401", "9405", "9910"} # "..." ALL 4 DIGITS

# "DU" means "dwelling units"
# depending on the tier/category there is more DU.
DU_PER_ACRE = {
    "Tier 1 - 200ft": 160, "Tier 1 - Quarter Mile": 120, "Tier 1 - Half Mile": 100,
    "Tier 2 - 200ft": 140, "Tier 2 - Quarter Mile": 100, "Tier 2 - Half Mile": 80,
}

EPC_ORDER = ["Not EPC", "High", "Higher", "Highest"]


def inspect(df, name):
    # Return shape, columns, and heading row of a DataFrame / GeoDataFrame.
    print("Inspecting " + name + " dataset ...")
    print(df.shape)
    print(df.columns)
    try:
        from IPython.display import display
        display(df.head(1))
    except ImportError:
        print(df.head(1))


def points_within(gdf, polygons, cols, how="inner"):
    pts = gdf.copy()
    pts.geometry = gdf.representative_point()
    return gpd.sjoin(pts, polygons[cols + ["geometry"]], how=how, predicate="within")


def load_raw(raw_path=RAW_DATA_PATH):
    raw_path = Path(raw_path)
    epc_data = gpd.read_file(raw_path / "epc_data.geojson")
    tod_data = gpd.read_file(raw_path / "tod_zones.geojson")

    tod_mask = tod_data.to_crs(3857).union_all() # we want parcels in tod zones,
                                                 # so we would like to match projections (3857: spherical mercator)

    parcels_data = gpd.read_file(raw_path / "parcels.geojson", # takes a while to load... (> 1 GB!!)
                                 engine="pyogrio", use_arrow=True,
                                 columns=PARCEL_COLS, mask=tod_mask)

    parcels_data = (parcels_data
                    .set_crs(3857, allow_override=True)      # data is assumed be in CRS 4326, but actually 3857. so label accordingly first
                    .to_crs(CRS))                            # then reproject to 3310
    return epc_data, tod_data, parcels_data


def clean_parcels(parcels_data):
    parcels_data = parcels_data[parcels_data.geometry.notna()]
    parcels_data = parcels_data.drop_duplicates(subset=["geometry"])                          # avoid double-counting of parcels
    parcels_data = parcels_data[~((parcels_data["Land"] == 0) & (parcels_data["Imps"] == 0))] # remove exempt/public land

    code = parcels_data["UseCode"]
    drop = (
        code.isna()
        | code.str[0].isin(DROP_SERIES)
        | code.str[:2].isin(DROP_PREFIXES)
        | code.isin(DROP_CODES)
    )
    return parcels_data[~drop].copy()


def filter_epc(epc_data):
    return epc_data[(epc_data["county_fip"] == 1) | (epc_data["county_fip"] == 85)].copy() # keep only Alameda (1), Santa Clara (85)


def join_tod(parcels_data, tod_data):
    # SPATIAL JOIN 1: PARCELS + TOD ZONES
    tod_data = tod_data.copy()
    parcels_data = parcels_data.copy()
    tod_data["du_per_acre"] = tod_data["zone_label"].map(DU_PER_ACRE)
    parcels_data["acres"] = parcels_data.area / 4046.86

    pts = points_within(parcels_data, tod_data, ["zone_id", "zone_label", "du_per_acre"])

    # keep each parcel's most permissive zone
    pts = pts.sort_values("du_per_acre", ascending=False)
    pts = pts[~pts.index.duplicated()]

    pts["max_units"] = np.floor(pts["acres"] * pts["du_per_acre"]).astype(int)

    # This is where we track parcels in TOD zones (used pts as a temp variable)
    parcels_tod = parcels_data.join(pts[["zone_id", "zone_label", "du_per_acre", "max_units"]],
                                    how="inner")
    return parcels_tod[parcels_tod["max_units"] >= 5].copy() # SB 79 projects need at least 5 units


def join_epc(parcels_tod, epc_data):
    # SPATIAL JOIN 2: PARCELS / TOD ZONES + EPC DATA
    parcels_tod = parcels_tod.copy()
    reps = points_within(parcels_tod, epc_data, ["epc_class"], how="left")
    reps = reps[~reps.index.duplicated()]

    parcels_tod["epc_class"] = reps["epc_class"]
    parcels_tod["is_epc"] = parcels_tod["epc_class"].notna()
    parcels_tod["epc_class"] = pd.Categorical(parcels_tod["epc_class"].fillna("Not EPC"),
                                              categories=EPC_ORDER, ordered=True)
    return parcels_tod


def add_features(parcels_tod):
    parcels_tod = parcels_tod.copy()

    # numbers stored as text should be converted to actual numbers
    for col in ["Land", "Imps", "LatestDocu"]:
        parcels_tod[col] = pd.to_numeric(parcels_tod[col], errors="coerce")

    # soft sites are "buildings worth less than half the land"
    parcels_tod["il_ratio"] = parcels_tod["Imps"] / parcels_tod["Land"].replace(0, np.nan)
    parcels_tod["soft_site"] = parcels_tod["il_ratio"] < 0.5
    parcels_tod["soft_units"] = parcels_tod["max_units"].where(parcels_tod["soft_site"], 0)

    # recent activity: a recorded sale or document in the last 10 years
    parcels_tod["recent_activity"] = parcels_tod["LatestDocu"] >= 2016

    # "Tier 1 - Half Mile" becomes "Tier 1"
    parcels_tod["tier"] = parcels_tod["zone_label"].str[:6]
    return parcels_tod


def summarize(parcels_tod):
    print("total allowed units:", parcels_tod["max_units"].sum())
    print("share in an epc:", parcels_tod["is_epc"].mean().round(3))
    print(parcels_tod["zone_label"].value_counts())


def build_parcels_tod(raw_path=RAW_DATA_PATH, proc_path=PROC_DATA_PATH, save=True):
    proc_path = Path(proc_path)
    epc_data, tod_data, parcels_data = load_raw(raw_path)
    if save:
        proc_path.mkdir(parents=True, exist_ok=True)
        parcels_data.to_parquet(proc_path / "parcels_tod.parquet") # .parquet is faster to load

    epc_data = filter_epc(epc_data.to_crs(CRS))
    tod_data = tod_data.to_crs(CRS)
    parcels_data = clean_parcels(parcels_data)

    parcels_tod = join_tod(parcels_data, tod_data)
    parcels_tod = join_epc(parcels_tod, epc_data)
    parcels_tod = add_features(parcels_tod)

    if save:
        parcels_tod.to_parquet(proc_path / "parcels_tod_clean.parquet")
        print("saved to " + str(proc_path))
    return parcels_tod, epc_data, tod_data


def load_processed(proc_path=PROC_DATA_PATH):
    return gpd.read_parquet(Path(proc_path) / "parcels_tod_clean.parquet")


if __name__ == "__main__":
    parcels_tod, _, _ = build_parcels_tod()
    summarize(parcels_tod)
