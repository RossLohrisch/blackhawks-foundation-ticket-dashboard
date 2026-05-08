import pandas as pd


def summarize(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    grouped = (
        df.groupby(group_cols, as_index=False)
        .agg(
            TOTAL_SEATS=("TOTAL_SEATS", "sum"),
            TOTAL_ACCOUNTS=("TOTAL_ACCOUNTS", "sum"),
            ROWS=("POSTAL_CODE", "size"),
        )
    )
    grouped["SEATS_PER_ACCOUNT"] = grouped["TOTAL_SEATS"] / grouped["TOTAL_ACCOUNTS"].where(
        grouped["TOTAL_ACCOUNTS"] != 0, pd.NA
    )
    return grouped


def by_product(df: pd.DataFrame) -> pd.DataFrame:
    return summarize(df, ["PRODUCT_TYPE"]).sort_values("TOTAL_SEATS", ascending=False)


def by_year(df: pd.DataFrame) -> pd.DataFrame:
    return summarize(df, ["SEASON_YEAR"]).sort_values("SEASON_YEAR")


def product_by_year(df: pd.DataFrame) -> pd.DataFrame:
    return summarize(df, ["SEASON_YEAR", "PRODUCT_TYPE"]).sort_values(
        ["SEASON_YEAR", "TOTAL_SEATS"], ascending=[True, False]
    )


def top_zips(df: pd.DataFrame, metric: str = "TOTAL_SEATS", limit: int = 25) -> pd.DataFrame:
    return summarize(df, ["POSTAL_CODE"]).sort_values(metric, ascending=False).head(limit)


def zip_product_summary(df: pd.DataFrame) -> pd.DataFrame:
    return summarize(df, ["POSTAL_CODE", "PRODUCT_TYPE"]).sort_values("TOTAL_SEATS", ascending=False)


def outlier_rows(df: pd.DataFrame, min_accounts: int = 1, limit: int = 50) -> pd.DataFrame:
    candidates = df[df["TOTAL_ACCOUNTS"] >= min_accounts].copy()
    return candidates.sort_values("SEATS_PER_ACCOUNT", ascending=False).head(limit)
