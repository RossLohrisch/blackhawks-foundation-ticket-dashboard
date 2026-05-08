from pathlib import Path
import pandas as pd

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "foundation_2026-05-04-1601.csv"


def load_foundation_data(path: Path = DATA_PATH) -> pd.DataFrame:
    """Load the Blackhawks ticket/account foundation CSV."""
    df = pd.read_csv(path, dtype={"POSTAL_CODE": "string"})
    df.columns = [c.strip().upper() for c in df.columns]
    return df
