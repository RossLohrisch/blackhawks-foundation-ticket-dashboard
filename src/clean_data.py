import pandas as pd

REQUIRED_COLUMNS = [
    "SEASON_YEAR",
    "POSTAL_CODE",
    "PRODUCT_TYPE",
    "TOTAL_SEATS",
    "TOTAL_ACCOUNTS",
]


def clean_foundation_data(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize types and add derived ticket/account metrics."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    out = df.copy()
    out["POSTAL_CODE"] = out["POSTAL_CODE"].astype("string").str.strip().str.zfill(5)
    out["PRODUCT_TYPE"] = out["PRODUCT_TYPE"].astype("string").str.strip()
    out["SEASON_YEAR"] = pd.to_numeric(out["SEASON_YEAR"], errors="coerce").astype("Int64")
    out["TOTAL_SEATS"] = pd.to_numeric(out["TOTAL_SEATS"], errors="coerce").fillna(0).astype(int)
    out["TOTAL_ACCOUNTS"] = pd.to_numeric(out["TOTAL_ACCOUNTS"], errors="coerce").fillna(0).astype(int)

    out = out.dropna(subset=["SEASON_YEAR", "POSTAL_CODE", "PRODUCT_TYPE"])
    out = out[out["TOTAL_ACCOUNTS"] >= 0]
    out = out[out["TOTAL_SEATS"] >= 0]

    out["SEATS_PER_ACCOUNT"] = out.apply(
        lambda r: r["TOTAL_SEATS"] / r["TOTAL_ACCOUNTS"] if r["TOTAL_ACCOUNTS"] else 0,
        axis=1,
    )
    return out
