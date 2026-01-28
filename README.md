# ERA5 Hourly Weather Data Dashboard

A collaborative university project to visualize global weather patterns using the **ERA5 dataset** via **Google Earth Engine (GEE)**, built with **Streamlit** and **Plotly**.

**Live app**: https://dashboard-era5.streamlit.app/

---

## Overview
- Compare two ERA5 monthly aggregates side-by-side on synchronized maps.
- Explore time series and distributions through chart analysis.
- View month-by-month map evolution for any variable.
- Browse an in-app variables reference (band name, unit, description).

## Requirements
- Python 3.9+ (project tools target 3.9).
- Google Earth Engine access with a service account and JSON key.

## Quick Start
Clone and set up a virtual environment, preserving the original steps:
```bash
# Clone repo
git clone https://git.imp.fu-berlin.de/ct3828fu/dashboardera5.git
cd dashboardera5

# Create + activate venv
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Configure Google Earth Engine
1) Enable the Earth Engine API for your Google Cloud project and create a service account with the necessary roles.  
2) Download the service account JSON key.  
3) Create `.streamlit/secrets.toml` in the repo root with the key contents under `GEE_JSON`:
```toml
GEE_JSON = { 
  # paste the full JSON from your service account key here
  "type": "service_account",
  "project_id": "...",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n",
  "client_email": "...@....iam.gserviceaccount.com",
  "token_uri": "https://oauth2.googleapis.com/token"
}
```
The app reads `st.secrets["GEE_JSON"]` to initialize Earth Engine.

## Run the App
```bash
make run
```
Then open the local URL Streamlit prints. \
default: http://localhost:8501

## Project Structure
- `app.py` — Streamlit entry point and navigation.
- `src/modules/views/` — Pages: map comparison, chart analysis, map evolution, info, and variable dialog.
- `src/modules/gee_interface.py` — Earth Engine initialization and data access helpers.
- `src/modules/variables.py` — Variable catalog scraping and visualization presets.
- `docs/catalog_vars.json` — Cached band metadata generated on first run.

## Development Notes
- Formatting: `black` (line length 120).  
- Linting: `ruff` (E,F,I).  
- Optional: install `pre-commit` and run `pre-commit install` to enforce checks locally.

## Troubleshooting
- **GEE Initialization failed**: verify `.streamlit/secrets.toml` is present, the JSON is valid, and the service account has Earth Engine access.
- **Missing bands**: the first run may fetch catalog metadata and write `docs/catalog_vars.json`; rerun the app after the file is created.
