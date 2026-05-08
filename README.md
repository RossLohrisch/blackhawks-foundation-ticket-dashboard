# Blackhawks Foundation Ticket Dashboard

Early Streamlit dashboard for exploring Blackhawks ticket/account foundation data by season, ZIP code, and product type.

## Quick start

### Mac / Linux / WSL

```bash
cd Blackhawks_Project
./run_app.sh
```

On Mac, you can also double-click:

```text
run_app_mac.command
```

### Windows

Double-click:

```text
run_app_windows.bat
```

Or from PowerShell:

```powershell
cd "$env:USERPROFILE\Desktop\Blackhawks_Project"
.\run_app_windows.bat
```

The scripts will:

1. Check for Python.
2. Attempt to install Python if it is missing:
   - Windows: `winget install --id Python.Python.3.12 -e`
   - Mac: `brew install python`
   - Ubuntu/WSL: `sudo apt-get install python3 python3-pip python3-venv`
3. Create a local `.venv`.
4. Install dependencies.
5. Launch Streamlit.

Streamlit will print a local URL, usually:

```text
http://localhost:8501
```

## Manual Python install fallback

If auto-install does not work:

- Mac: install Homebrew then `brew install python`, or install from <https://www.python.org/downloads/>
- Windows: install from <https://www.python.org/downloads/> and check **Add Python to PATH**
- Ubuntu/WSL: `sudo apt-get update && sudo apt-get install python3 python3-pip python3-venv`

## Data

Current input file:

```text
data/foundation_2026-05-04-1601.csv
```

Expected columns:

- `SEASON_YEAR`
- `POSTAL_CODE`
- `PRODUCT_TYPE`
- `TOTAL_SEATS`
- `TOTAL_ACCOUNTS`

See `DATA_DICTIONARY.md` for current assumptions and open questions.

## App tabs

- **ZIP map** — approximate ZIP centroid bubble map with simple hotspot coloring
- **Overview** — seats/accounts by product and year
- **ZIP analysis** — top ZIP tables and ZIP/product breakdown
- **Outliers / QA** — high seats-per-account rows and distribution
- **Data** — filtered table and CSV export

## Current caveat

The map uses ZIP centroids, not ZIP boundary polygons. That is good for quick exploration, but a true choropleth should be a next step.
