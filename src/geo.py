import pandas as pd


def add_zip_centroids(df: pd.DataFrame) -> pd.DataFrame:
    """Add approximate US ZIP centroids using pgeocode when available.

    The app still works if pgeocode is not installed; map-specific rows simply have
    missing coordinates.
    """
    out = df.copy()
    try:
        import pgeocode
    except Exception:
        out["latitude"] = pd.NA
        out["longitude"] = pd.NA
        return out

    unique_zips = sorted(out["POSTAL_CODE"].dropna().astype(str).unique())
    nomi = pgeocode.Nominatim("us")
    geo = nomi.query_postal_code(unique_zips)
    geo = geo[["postal_code", "latitude", "longitude", "place_name", "state_code", "county_name"]].copy()
    geo["postal_code"] = geo["postal_code"].astype(str).str.zfill(5)
    return out.merge(geo, left_on="POSTAL_CODE", right_on="postal_code", how="left").drop(columns=["postal_code"])
