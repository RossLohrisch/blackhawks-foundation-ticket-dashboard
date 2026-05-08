import pandas as pd


def build_metrics(df: pd.DataFrame) -> dict:
    total_seats = int(df["TOTAL_SEATS"].sum()) if not df.empty else 0
    total_accounts = int(df["TOTAL_ACCOUNTS"].sum()) if not df.empty else 0
    seats_per_account = total_seats / total_accounts if total_accounts else 0
    return {
        "rows": len(df),
        "zip_count": int(df["POSTAL_CODE"].nunique()) if not df.empty else 0,
        "total_seats": total_seats,
        "total_accounts": total_accounts,
        "seats_per_account": seats_per_account,
    }
