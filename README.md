# 7CREW Enterprises — P&L Performance Dashboard

Interactive Streamlit dashboard for period-over-period P&L analysis across all stands.

## Features

- **CEO Summary** — Network KPIs, period trend, top/bottom performers, cohort comparison
- **COO Scorecard** — Per-stand traffic-light view (COGS %, Labor %, EBITDA %)
- **Q4 Class Watch** — Dedicated monitoring for Q4-opened stands with ramp benchmarks
- **EBITDA Trend** — Traffic-light heatmap across all stands × all periods
- **Cohort Analysis** — Ramp curves by opening cohort (Net Sales + EBITDA %)
- **Revenue Trend** — Net Sales by stand × period, sortable/filterable
- **Stand Directory** — Master stand list with metadata and current performance

---

## Quick Start (Local)

### 1. Clone the repo
```bash
git clone https://github.com/YOUR-ORG/7brew-dashboard.git
cd 7brew-dashboard
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Add your P&L data files
Drop your period files into the `data/` folder. Files must match the naming pattern:
```
7BREW Income Statement Side By Side PTD All P#'YY.xlsx
```
Example:
```
data/7BREW Income Statement Side By Side PTD All P1'25.xlsx
data/7BREW Income Statement Side By Side PTD All P13'25.xlsx
data/7BREW Income Statement Side By Side PTD All P1'26.xlsx
```

### 4. Run the app
```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`

---

## Adding a New Period

Two options:

**Option A — Drop and go (easiest):**
1. Drop the new `*.xlsx` file into the `data/` folder
2. Refresh the Streamlit page — it auto-detects new files

**Option B — In-app upload:**
1. Open the app
2. Expand "📂 Add New Period Files" in the sidebar
3. Upload the file — it's saved to `data/` automatically

---

## Deploying to Streamlit Cloud

1. Push the repo to GitHub (private recommended — your P&L files are proprietary)
2. Go to [share.streamlit.io](https://share.streamlit.io) → "New app"
3. Connect your GitHub repo, set `app.py` as the main file
4. Deploy

**Important for Streamlit Cloud:**
Since `data/*.xlsx` is gitignored, use the in-app file uploader to load your period files
after each new deploy, OR commit the data files to a private repo branch.

---

## File Structure

```
7brew-dashboard/
├── app.py                  # Main Streamlit application
├── brew_extract.py         # P&L data extraction engine
├── requirements.txt        # Python dependencies
├── .gitignore
├── .streamlit/
│   └── config.toml         # 7Crew brand theme
├── assets/
│   └── logo.png            # 7Crew logo
└── data/                   # P&L Excel files go here (gitignored)
    └── .gitkeep
```

---

## Updating to a New Build (Excel Dashboard)

The Excel dashboard is also generated from the same extraction engine.
To regenerate it, run:
```bash
python update_dashboard.py
```

---

## Brand & Design

- **Primary:** Crimson Red `#C8102E`
- **Background:** Near-black `#1A1A1A`
- **Typography:** DM Sans / system sans-serif
- **ADA:** All color pairs verified ≥ 4.5:1 WCAG 2.1 AA contrast ratio
- **Q4 Watch:** Steel blue `#1565C0` accent for Q4/Q1 class stands
