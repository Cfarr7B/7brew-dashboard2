"""
7CREW ENTERPRISES — P&L Performance Dashboard (HTML Design)
Streamlit App  |  github.com/your-org/7brew-dashboard2
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
import glob
from pathlib import Path
from brew_extract import build_dataset

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG & DESIGN SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="7BREW | P&L Dashboard",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Design System (HTML Palette) ───────────────────────────────────────────
RED           = "#C8102E"
RED_DARK      = "#A00C24"
RED_GLOW      = "rgba(200,16,46,0.18)"
BLACK         = "#0D0D0D"
CHARCOAL      = "#1A1A1A"
STEEL         = "#252525"
MID           = "#333333"
BORDER        = "#3A3A3A"
AMBER         = "#F4A21E"
AMBER_LT      = "rgba(244,162,30,0.15)"
WHITE         = "#FAFAFA"
FOG           = "#B0B0B0"
DIM           = "#707070"

WIN_GREEN     = "#2ECC71"
WIN_GREEN_BG  = "rgba(46,204,113,0.12)"
WARN_YELLOW   = "#F4A21E"
WARN_BG       = "rgba(244,162,30,0.12)"
RISK_RED      = "#E74C3C"
RISK_BG       = "rgba(231,76,60,0.12)"
INFO_BLUE     = "#5B9BD5"
INFO_BG       = "rgba(91,155,213,0.12)"

Q4_COHORTS = {"Q4'24", "Q4'25"}
PLOTLY_COLORS = [RED, "#1565C0", "#2E7D32", WARN_YELLOW,
                 "#6A1B9A", "#00838F", "#4E342E", "#37474F"]

# ── Enhanced CSS with HTML Dashboard styling ────────────────────────────────
st.markdown(f"""
<style>
:root {{
  --brew-red:       {RED};
  --brew-charcoal:  {CHARCOAL};
  --brew-steel:     {STEEL};
  --brew-border:    {BORDER};
  --brew-amber:     {AMBER};
  --brew-white:     {WHITE};
  --brew-fog:       {FOG};
  --brew-dim:       {DIM};
  --radius-md:  10px;
  --shadow-card: 0 2px 16px rgba(0,0,0,0.5);
}}

[data-testid="stSidebar"] {{
    background: {BLACK};
    border-right: 1px solid {BORDER};
}}
[data-testid="stSidebar"] * {{ color: {FOG} !important; }}

.brew-header {{
    background: {CHARCOAL};
    border-bottom: 2px solid {RED};
    padding: 20px 24px;
    margin-bottom: 24px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.3);
}}
.brew-header h1 {{
    color: {WHITE};
    font-size: 26px;
    font-weight: 800;
    letter-spacing: 2px;
    margin: 0;
    text-transform: uppercase;
}}
.brew-header p {{
    color: {DIM};
    font-size: 11px;
    margin: 8px 0 0;
    font-family: monospace;
}}

.kpi-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 12px;
    margin-bottom: 24px;
}}
.kpi-card {{
    background: {CHARCOAL};
    border: 1px solid {BORDER};
    border-top: 3px solid {RED};
    border-radius: 10px;
    padding: 16px;
    text-align: center;
    transition: transform 0.2s;
}}
.kpi-card:hover {{
    transform: translateY(-2px);
    box-shadow: var(--shadow-card);
}}
.kpi-label {{ color: {DIM}; font-size: 9px; font-weight: 700; text-transform: uppercase; margin-bottom: 8px; }}
.kpi-value {{ font-size: 28px; font-weight: 800; color: {WHITE}; margin: 0; line-height: 1; }}
.kpi-sub {{ color: {DIM}; font-size: 10px; margin-top: 6px; font-family: monospace; }}
.kpi-good  {{ color: {WIN_GREEN}; }}
.kpi-warn  {{ color: {WARN_YELLOW}; }}
.kpi-bad   {{ color: {RISK_RED}; }}

.section-title {{
    font-size: 16px;
    font-weight: 700;
    color: {WHITE};
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 2px solid {RED};
}}

#MainMenu, footer {{ visibility: hidden; }}

::-webkit-scrollbar {{
    width: 8px;
    height: 8px;
}}
::-webkit-scrollbar-track {{
    background: {BLACK};
}}
::-webkit-scrollbar-thumb {{
    background: {STEEL};
    border-radius: 4px;
}}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# DATA LOADING & HELPERS
# ══════════════════════════════════════════════════════════════════════════════

DATA_DIR = Path(__file__).parent / "data"

@st.cache_data(show_spinner="Reading P&L files…", ttl=300)
def load_data(file_paths_key: str):
    """Load and cache the consolidated dataset."""
    return build_dataset(str(DATA_DIR))

def get_file_key():
    files = sorted(glob.glob(str(DATA_DIR / "7BREW Income Statement Side By Side PTD All*.xlsx")))
    key_parts = [f"{p}:{os.path.getmtime(p):.0f}" for p in files]
    stand_dates = DATA_DIR / "7Crew_Stand_Dates.xlsx"
    if stand_dates.exists():
        key_parts.append(f"{stand_dates}:{os.path.getmtime(stand_dates):.0f}")
    return "|".join(key_parts)

def safe_pct(num, den):
    try:
        v = num / den
        return v if np.isfinite(v) else None
    except:
        return None

def fmt_dollar(v, mm=False):
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return "—"
    if mm:
        return f"${v/1_000_000:.2f}M"
    return f"${v:,.0f}"

def fmt_pct(v):
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return "—"
    return f"{v:.1%}"

def kpi_card(label, value, sub="", cls="kpi-white"):
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value {cls}">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>"""

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR & FILE UPLOAD
# ══════════════════════════════════════════════════════════════════════════════

def sidebar_controls(df):
    with st.sidebar:
        logo_path = Path(__file__).parent / "assets" / "logo.png"
        if logo_path.exists():
            st.image(str(logo_path), use_container_width=True)
        else:
            st.markdown(f"## <span style='color:{RED}'>7CREW</span> ENTERPRISES", unsafe_allow_html=True)

        st.divider()

        # File uploader
        with st.expander("📂 Add New Period Files", expanded=True):
            st.caption("Drop a new P&L xlsx to add it to the dataset. Files save to data/ folder.")
            uploaded = st.file_uploader(
                "Upload Period File",
                type=["xlsx"],
                accept_multiple_files=True,
                label_visibility="collapsed",
            )
            if uploaded:
                for f in uploaded:
                    dest = DATA_DIR / f.name
                    if not dest.exists():
                        dest.write_bytes(f.read())
                        st.success(f"Saved {f.name}")
                st.rerun()

        st.divider()

        if st.button("🔄 Refresh Data Cache"):
            st.cache_data.clear()
            st.rerun()

        st.divider()

        periods = sorted(df['period_label'].unique(),
                        key=lambda p: df[df['period_label']==p]['sort_key'].iloc[0])
        selected_period = st.selectbox("📅 Current Period", periods,
                                      index=len(periods)-1)

        # Load official regions from Stand Dates file
        stand_dates_file = DATA_DIR / "7Crew_Stand_Dates.xlsx"
        region_list = ["All"]
        if stand_dates_file.exists():
            try:
                stand_dates = pd.read_excel(stand_dates_file)
                official_regions = stand_dates['Region'].dropna().unique().tolist()
                region_list.extend(official_regions)
            except:
                region_list.extend(sorted(df['region'].unique().tolist()))
        else:
            region_list.extend(sorted(df['region'].unique().tolist()))

        selected_region = st.selectbox("🗺️ Region", region_list)

        cohorts = ["All"] + sorted(
            df['cohort'].unique().tolist(),
            key=lambda c: (0 if c=="Legacy (Pre-Data)" else 1, c))
        selected_cohort = st.multiselect("📦 Cohort", cohorts[1:],
                                        placeholder="All cohorts")

        st.divider()
        st.caption(f"**{df['stand_id'].nunique()}** stands  |  "
                  f"**{df['period_label'].nunique()}** periods")
        st.caption(f"Updated: {pd.Timestamp.now().strftime('%m/%d/%Y')}")

    return selected_period, selected_region, selected_cohort, periods

def build_city_to_region_map():
    """Create mapping from city to region based on Stand Dates file"""
    import re
    city_region_map = {}
    stand_dates_file = DATA_DIR / "7Crew_Stand_Dates.xlsx"

    if stand_dates_file.exists():
        try:
            sd = pd.read_excel(stand_dates_file)
            # Map cities to regions from Stand Dates
            for _, row in sd.iterrows():
                stand_name = str(row.get('Stand', ''))
                region = row.get('Region', '')
                # Extract city from stand name (e.g., "Cleburne (#516)" -> "cleburne")
                city = stand_name.split('(')[0].strip().lower()
                if city and region:
                    city_region_map[city] = region
        except Exception as e:
            st.warning(f"Could not load city-to-region mapping: {e}")

    return city_region_map

def apply_filters(df, period, region, cohorts):
    ldf = df[df['period_label'] == period].copy()

    # Use provided region for filtering
    if region != "All":
        # Check if filtering by the official regions
        stand_dates_file = DATA_DIR / "7Crew_Stand_Dates.xlsx"
        if stand_dates_file.exists():
            try:
                sd = pd.read_excel(stand_dates_file)
                official_regions = sd['Region'].dropna().unique()
                if region in official_regions:
                    # Filter by matching cities that belong to this region
                    matching_cities = sd[sd['Region'] == region]['Stand'].apply(
                        lambda x: x.split('(')[0].strip().lower()
                    ).unique()
                    ldf = ldf[ldf['city'].str.lower().isin(matching_cities)]
                else:
                    # Fall back to original region filter
                    ldf = ldf[ldf['region'] == region]
            except:
                ldf = ldf[ldf['region'] == region]
        else:
            ldf = ldf[ldf['region'] == region]

    if cohorts:
        ldf = ldf[ldf['cohort'].isin(cohorts)]
    ldf['ebitda_pct'] = ldf['Store Level EBITDA'] / ldf['Net Sales'].replace(0, np.nan)
    ldf['cogs_pct']   = ldf['COGS'] / ldf['Net Sales'].replace(0, np.nan)
    ldf['labor_pct']  = ldf['Total Labor & Benefits'] / ldf['Net Sales'].replace(0, np.nan)
    return ldf

# ══════════════════════════════════════════════════════════════════════════════
# TAB CONTENT FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def tab_overview(df, ldf, periods, selected_period):
    """Overview Tab - System KPIs and period comparison"""
    st.markdown('<div class="section-title">System Overview</div>', unsafe_allow_html=True)
    
    # KPIs
    first_period = periods[0]
    fdf = df[df['period_label'] == first_period]
    mature = ldf[~ldf['is_ramp']]
    
    total_stands = ldf['stand_id'].nunique()
    total_ns     = ldf['Net Sales'].sum()
    net_ebitda   = safe_pct(ldf['Store Level EBITDA'].sum(), total_ns)
    net_cogs     = safe_pct(ldf['COGS'].sum(), total_ns)
    net_labor    = safe_pct(ldf['Total Labor & Benefits'].sum(), total_ns)
    
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    cards = [
        (c1, "Total Stands", str(total_stands), "Active", "kpi-white"),
        (c2, "Network Sales", fmt_dollar(total_ns, mm=True), f"Period Total", "kpi-red"),
        (c3, "EBITDA %", fmt_pct(net_ebitda), "System Avg", "kpi-good" if (net_ebitda or 0) >= 0.12 else "kpi-bad"),
        (c4, "COGS %", fmt_pct(net_cogs), "System Avg", "kpi-warn"),
        (c5, "Labor %", fmt_pct(net_labor), "System Avg", "kpi-warn"),
        (c6, "Ramp Stands", f"{int(ldf['is_ramp'].sum())}", "< 4 periods", "kpi-warn"),
    ]
    for col, label, val, sub, cls in cards:
        col.markdown(kpi_card(label, val, sub, cls), unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Period trend
    st.markdown('<div class="section-title">Period-Over-Period Network Performance</div>', unsafe_allow_html=True)
    trend = (df.groupby(['period_label','sort_key'])
            .agg(net_sales=('Net Sales','sum'),
                 store_ebitda=('Store Level EBITDA','sum'),
                 stands=('stand_id','nunique'))
            .reset_index().sort_values('sort_key'))
    trend['ebitda_pct'] = trend['store_ebitda'] / trend['net_sales']
    
    col_chart, col_table = st.columns([3, 2])
    
    with col_chart:
        fig = go.Figure()
        fig.add_bar(x=trend['period_label'], y=trend['net_sales'],
                   name="Net Sales", marker_color=RED, opacity=0.85)
        fig.add_scatter(x=trend['period_label'], y=trend['store_ebitda'],
                       name="Store EBITDA", mode="lines+markers",
                       line=dict(color="#1565C0", width=2), yaxis="y2")
        fig.update_layout(
           template="plotly_dark",
            paper_bgcolor=CHARCOAL, plot_bgcolor=CHARCOAL,
            yaxis=dict(title="Net Sales ($)", gridcolor="#404040"),
            yaxis2=dict(title="Store EBITDA ($)", overlaying="y", side="right", gridcolor="#404040"),
            legend=dict(x=0, y=1.1, orientation="h"),
            margin=dict(l=0,r=0,t=20,b=0), height=280,
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col_table:
        tbl = trend[['period_label','stands','net_sales','ebitda_pct']].copy()
        tbl['weekly_avg'] = tbl['net_sales'] / tbl['stands'] / 4
        tbl['annual_run_rate'] = tbl['weekly_avg'] * 52
        tbl.columns = ["Period","Stands","Net Sales","EBITDA %","Weekly Avg/Stand","Annual Run Rate"]
        tbl["Net Sales"] = tbl["Net Sales"].apply(lambda x: fmt_dollar(x))
        tbl["Weekly Avg/Stand"] = tbl["Weekly Avg/Stand"].apply(lambda x: fmt_dollar(x))
        tbl["Annual Run Rate"] = tbl["Annual Run Rate"].apply(lambda x: fmt_dollar(x))
        tbl["EBITDA %"] = tbl["EBITDA %"].apply(fmt_pct)
        st.dataframe(tbl, use_container_width=True, hide_index=True, height=280)

def tab_trends(df, ldf, periods, selected_period):
    """Period Comparison Tab - Historical trends and changes"""
    st.markdown('<div class="section-title">Period Comparison</div>', unsafe_allow_html=True)

    # Period-over-period metrics
    trend_data = df.groupby('period_label').agg(
        net_sales=('Net Sales','sum'),
        cogs=('COGS','sum'),
        labor=('Total Labor & Benefits','sum'),
        store_ebitda=('Store Level EBITDA','sum'),
        stands=('stand_id','nunique')
    ).reset_index()

    # Sort by period order
    period_order = {p: i for i, p in enumerate(periods)}
    trend_data['period_order'] = trend_data['period_label'].map(period_order)
    trend_data = trend_data.sort_values('period_order').drop('period_order', axis=1)

    trend_data['cogs_pct'] = trend_data['cogs'] / trend_data['net_sales']
    trend_data['labor_pct'] = trend_data['labor'] / trend_data['net_sales']
    trend_data['ebitda_pct'] = trend_data['store_ebitda'] / trend_data['net_sales']

    # Metrics selector
    metric_choice = st.radio("Select Metric to Analyze",
                            ["EBITDA %", "COGS %", "Labor %", "Net Sales"],
                            horizontal=True)

    col_chart, col_stats = st.columns([3, 1])

    with col_chart:
        fig = go.Figure()

        if metric_choice == "EBITDA %":
            fig.add_scatter(x=trend_data['period_label'], y=trend_data['ebitda_pct']*100,
                          mode='lines+markers', name='EBITDA %',
                          line=dict(color=WIN_GREEN, width=3),
                          marker=dict(size=8))
        elif metric_choice == "COGS %":
            fig.add_scatter(x=trend_data['period_label'], y=trend_data['cogs_pct']*100,
                          mode='lines+markers', name='COGS %',
                          line=dict(color=WARN_YELLOW, width=3),
                          marker=dict(size=8))
        elif metric_choice == "Labor %":
            fig.add_scatter(x=trend_data['period_label'], y=trend_data['labor_pct']*100,
                          mode='lines+markers', name='Labor %',
                          line=dict(color=INFO_BLUE, width=3),
                          marker=dict(size=8))
        else:
            fig.add_bar(x=trend_data['period_label'], y=trend_data['net_sales'],
                       name='Net Sales', marker_color=RED, opacity=0.8)

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor=CHARCOAL, plot_bgcolor=CHARCOAL,
            hovermode='x unified',
            margin=dict(l=0,r=0,t=20,b=0), height=350,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_stats:
        if len(trend_data) > 1:
            latest = trend_data.iloc[-1]
            prior = trend_data.iloc[-2]

            if metric_choice == "EBITDA %":
                chg = latest['ebitda_pct'] - prior['ebitda_pct']
                val = f"{latest['ebitda_pct']:.1%}"
            elif metric_choice == "COGS %":
                chg = latest['cogs_pct'] - prior['cogs_pct']
                val = f"{latest['cogs_pct']:.1%}"
            elif metric_choice == "Labor %":
                chg = latest['labor_pct'] - prior['labor_pct']
                val = f"{latest['labor_pct']:.1%}"
            else:
                chg = latest['net_sales'] - prior['net_sales']
                val = fmt_dollar(latest['net_sales'], mm=True)

            st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Current</div>"
                       f"<div class='kpi-value'>{val}</div>"
                       f"<div class='kpi-sub'>Period {latest['period_label']}</div></div>",
                       unsafe_allow_html=True)

            arrow = "↑" if chg >= 0 else "↓"
            color = "green" if metric_choice in ["EBITDA %","Net Sales"] and chg >= 0 else "red"
            if metric_choice in ["COGS %","Labor %"]:
                color = "red" if chg >= 0 else "green"

            st.markdown(f"<div style='text-align:center;color:{color};font-size:18px;margin-top:12px;'>"
                       f"{arrow} {abs(chg):.2f}{'%' if '%' in metric_choice else ''}</div>",
                       unsafe_allow_html=True)

def tab_stands(df, ldf, periods, selected_period):
    """Stand Detail Tab - Individual store performance"""
    st.markdown('<div class="section-title">Stand Detail</div>', unsafe_allow_html=True)

    # Stand metrics
    stands_data = ldf[['stand_id', 'Net Sales', 'COGS', 'Total Labor & Benefits',
                       'Store Level EBITDA', 'region', 'cohort', 'is_ramp']].copy()
    stands_data['cogs_pct'] = stands_data['COGS'] / stands_data['Net Sales']
    stands_data['labor_pct'] = stands_data['Total Labor & Benefits'] / stands_data['Net Sales']
    stands_data['ebitda_pct'] = stands_data['Store Level EBITDA'] / stands_data['Net Sales']

    # Sorting options
    col1, col2, col3 = st.columns(3)
    with col1:
        sort_by = st.selectbox("Sort by",
                              ["EBITDA %", "Net Sales", "COGS %", "Labor %"],
                              key="stand_sort")
    with col2:
        sort_order = st.radio("Order", ["Descending", "Ascending"], horizontal=True, key="stand_order")
    with col3:
        min_sales = st.number_input("Min Sales ($)", value=0, step=1000)

    # Filter
    stands_data = stands_data[stands_data['Net Sales'] >= min_sales]

    # Sort
    if sort_by == "EBITDA %":
        stands_data = stands_data.sort_values('ebitda_pct', ascending=(sort_order=="Ascending"))
    elif sort_by == "Net Sales":
        stands_data = stands_data.sort_values('Net Sales', ascending=(sort_order=="Ascending"))
    elif sort_by == "COGS %":
        stands_data = stands_data.sort_values('cogs_pct', ascending=(sort_order=="Ascending"))
    else:
        stands_data = stands_data.sort_values('labor_pct', ascending=(sort_order=="Ascending"))

    # Display table
    display_data = stands_data[['stand_id', 'Net Sales', 'ebitda_pct', 'cogs_pct',
                               'labor_pct', 'region', 'cohort']].copy()
    display_data.columns = ['Stand', 'Net Sales', 'EBITDA %', 'COGS %', 'Labor %', 'Region', 'Cohort']

    # Format columns
    display_data['Net Sales'] = display_data['Net Sales'].apply(lambda x: fmt_dollar(x))
    display_data['EBITDA %'] = display_data['EBITDA %'].apply(fmt_pct)
    display_data['COGS %'] = display_data['COGS %'].apply(fmt_pct)
    display_data['Labor %'] = display_data['Labor %'].apply(fmt_pct)

    st.dataframe(display_data, use_container_width=True, hide_index=True, height=500)

    # Top/Bottom performers
    st.markdown('<div class="section-title" style="margin-top:24px;">Performance Rankings</div>',
               unsafe_allow_html=True)

    col_top, col_bottom = st.columns(2)

    with col_top:
        st.subheader("🏆 Top Performers (by EBITDA %)")
        top_5 = stands_data.nlargest(5, 'ebitda_pct')[['stand_id', 'ebitda_pct', 'Net Sales']]
        for i, (idx, row) in enumerate(top_5.iterrows(), 1):
            st.markdown(f"**{i}. {row['stand_id']}** — {row['ebitda_pct']:.1%} EBITDA | {fmt_dollar(row['Net Sales'])}")

    with col_bottom:
        st.subheader("⚠️ Bottom Performers (by EBITDA %)")
        bot_5 = stands_data.nsmallest(5, 'ebitda_pct')[['stand_id', 'ebitda_pct', 'Net Sales']]
        for i, (idx, row) in enumerate(bot_5.iterrows(), 1):
            st.markdown(f"**{i}. {row['stand_id']}** — {row['ebitda_pct']:.1%} EBITDA | {fmt_dollar(row['Net Sales'])}")

def tab_regions(df, ldf, periods, selected_period):
    """Regions Tab - Regional analysis and comparison"""
    st.markdown('<div class="section-title">Regional Analysis</div>', unsafe_allow_html=True)

    # Load region definitions and map cities to regions
    stand_dates_file = DATA_DIR / "7Crew_Stand_Dates.xlsx"
    city_to_region = {}
    region_order = []

    if stand_dates_file.exists():
        try:
            stand_dates = pd.read_excel(stand_dates_file)
            region_order = stand_dates['Region'].dropna().unique().tolist()
            # Map each city to its region
            for _, row in stand_dates.iterrows():
                stand_name = str(row.get('Stand', ''))
                region = row.get('Region', '')
                city = stand_name.split('(')[0].strip().lower()
                if city and region:
                    city_to_region[city] = region
        except Exception as e:
            st.warning(f"Could not load region definitions: {e}")

    # Add region mapping to ldf based on city
    if city_to_region:
        ldf['region_mapped'] = ldf['city'].str.lower().map(city_to_region).fillna(ldf['region'])
    else:
        ldf['region_mapped'] = ldf['region']

    # Regional metrics - group by mapped regions
    region_data = ldf.groupby('region_mapped').agg(
        net_sales=('Net Sales','sum'),
        store_ebitda=('Store Level EBITDA','sum'),
        cogs=('COGS','sum'),
        labor=('Total Labor & Benefits','sum'),
        stands=('stand_id','nunique')
    ).reset_index()

    region_data.columns = ['region', 'net_sales', 'store_ebitda', 'cogs', 'labor', 'stands']

    region_data['ebitda_pct'] = region_data['store_ebitda'] / region_data['net_sales']
    region_data['cogs_pct'] = region_data['cogs'] / region_data['net_sales']
    region_data['labor_pct'] = region_data['labor'] / region_data['net_sales']

    # Sort by region order if available, otherwise by net sales
    if region_order:
        region_data['region_order'] = region_data['region'].apply(
            lambda x: region_order.index(x) if x in region_order else 999
        )
        region_data = region_data.sort_values('region_order').drop('region_order', axis=1)
    else:
        region_data = region_data.sort_values('net_sales', ascending=False)

    # KPI comparison
    st.markdown('<div class="section-title">Regional KPIs</div>', unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(kpi_card("Total Regions", str(region_data['region'].nunique()), "Active", "kpi-white"),
                   unsafe_allow_html=True)
    with col2:
        st.markdown(kpi_card("Network Sales", fmt_dollar(region_data['net_sales'].sum(), mm=True),
                            "Period Total", "kpi-red"), unsafe_allow_html=True)
    with col3:
        avg_ebitda = region_data['ebitda_pct'].mean()
        st.markdown(kpi_card("Avg EBITDA %", fmt_pct(avg_ebitda),
                            "Across Regions", "kpi-good" if avg_ebitda >= 0.12 else "kpi-bad"),
                   unsafe_allow_html=True)
    with col4:
        st.markdown(kpi_card("Avg COGS %", fmt_pct(region_data['cogs_pct'].mean()),
                            "Across Regions", "kpi-warn"), unsafe_allow_html=True)
    with col5:
        st.markdown(kpi_card("Avg Labor %", fmt_pct(region_data['labor_pct'].mean()),
                            "Across Regions", "kpi-warn"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Regional comparison charts
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("💰 Net Sales by Region")
        fig1 = px.bar(region_data.sort_values('net_sales', ascending=True),
                     y='region', x='net_sales',
                     orientation='h',
                     labels={'net_sales':'Net Sales ($)', 'region':'Region'},
                     color='ebitda_pct',
                     color_continuous_scale=['#E74C3C', '#F4A21E', '#2ECC71'],
                     )
        fig1.update_layout(template="plotly_dark",
                          paper_bgcolor=CHARCOAL, plot_bgcolor=CHARCOAL,
                          margin=dict(l=0,r=0,t=20,b=0), height=320,
                          coloraxis_colorbar=dict(title="EBITDA %"))
        st.plotly_chart(fig1, use_container_width=True)

    with col_chart2:
        st.subheader("📊 EBITDA % by Region")
        fig2 = px.bar(region_data.sort_values('ebitda_pct'),
                     x='region', y='ebitda_pct',
                     labels={'ebitda_pct':'EBITDA %', 'region':'Region'},
                     color='ebitda_pct',
                     color_continuous_scale=['#E74C3C', '#F4A21E', '#2ECC71'],
                     )
        fig2.update_layout(template="plotly_dark",
                          paper_bgcolor=CHARCOAL, plot_bgcolor=CHARCOAL,
                          margin=dict(l=0,r=0,t=20,b=0), height=320,
                          coloraxis_showscale=False)
        fig2.update_yaxes(tickformat=".1%")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Regional details table
    st.markdown('<div class="section-title">Regional Details</div>', unsafe_allow_html=True)

    region_display = region_data[['region', 'stands', 'net_sales', 'ebitda_pct',
                                  'cogs_pct', 'labor_pct']].copy()
    region_display.columns = ['Region', 'Stands', 'Net Sales', 'EBITDA %', 'COGS %', 'Labor %']

    region_display['Net Sales'] = region_display['Net Sales'].apply(lambda x: fmt_dollar(x, mm=True))
    region_display['EBITDA %'] = region_display['EBITDA %'].apply(fmt_pct)
    region_display['COGS %'] = region_display['COGS %'].apply(fmt_pct)
    region_display['Labor %'] = region_display['Labor %'].apply(fmt_pct)

    st.dataframe(region_display, use_container_width=True, hide_index=True)

def tab_wins(df, ldf, periods, selected_period):
    """Wins & Opportunities Tab"""
    st.markdown('<div class="section-title">Wins & Opportunities</div>', unsafe_allow_html=True)
    st.info("🎯 Top performers and areas for improvement.")
    # Implementation would show best/worst performers

def tab_forecast(df, ldf, periods, selected_period):
    """Forecast Tab"""
    st.markdown('<div class="section-title">Forecast P3–P13 2026</div>', unsafe_allow_html=True)
    st.info("📈 Forward-looking financial projections.")
    # Implementation would show forecast data

def tab_potholes(df, ldf, periods, selected_period):
    """Pothole Watch Tab - Critical Alerts"""
    st.markdown('<div class="section-title">⚠️ Pothole Watch</div>', unsafe_allow_html=True)
    st.info("🚨 Critical issues requiring attention.")
    # Implementation would show critical metrics and alerts

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    # Check for data files
    files = sorted(glob.glob(str(DATA_DIR / "7BREW Income Statement Side By Side PTD All*.xlsx")))
    
    if not files:
        with st.sidebar:
            logo_path = Path(__file__).parent / "assets" / "logo.png"
            if logo_path.exists():
                st.image(str(logo_path), use_container_width=True)
            else:
                st.markdown(f"## <span style='color:{RED}'>7CREW</span> ENTERPRISES", unsafe_allow_html=True)
            st.divider()
            st.markdown("### 📂 Upload Period Files")
            st.caption("Drop your P&L Excel files here to get started.")
            uploaded = st.file_uploader(
                "Upload Period File",
                type=["xlsx"],
                accept_multiple_files=True,
                label_visibility="collapsed",
            )
            if uploaded:
                for f in uploaded:
                    dest = DATA_DIR / f.name
                    if not dest.exists():
                        dest.write_bytes(f.read())
                        st.success(f"Saved {f.name}")
                st.rerun()
        
        st.markdown('<div class="brew-header"><h1>7CREW Enterprises | P&L Dashboard</h1>'
                   '<p>No period files found — upload your first file to get started</p></div>',
                   unsafe_allow_html=True)
        st.info("👈 Use the sidebar on the left to upload your P&L Excel files.")
        return
    
    # Load data
    try:
        df = load_data(get_file_key())
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.exception(e)
        return
    
    # Sidebar controls
    selected_period, selected_region, selected_cohort, periods = sidebar_controls(df)
    
    # Apply filters
    ldf = apply_filters(df, selected_period, selected_region, selected_cohort)
    
    # Header
    st.markdown(
        f'<div class="brew-header">'
        f'<h1>7CREW Enterprises  |  P&L Performance Dashboard</h1>'
        f'<p>{df["stand_id"].nunique()} stands  |  {len(periods)} periods  |  '
        f'Period: {selected_period}  |  {ldf["stand_id"].nunique()} stands visible</p>'
        f'</div>', unsafe_allow_html=True)
    
    # Tabs matching HTML dashboard
    tabs = st.tabs([
        "Overview",
        "Period Comparison",
        "Stand Detail",
        "Regions",
        "Wins & Opportunities",
        "Forecast",
        "⚠️ Pothole Watch"
    ])
    
    with tabs[0]: tab_overview(df, ldf, periods, selected_period)
    with tabs[1]: tab_trends(df, ldf, periods, selected_period)
    with tabs[2]: tab_stands(df, ldf, periods, selected_period)
    with tabs[3]: tab_regions(df, ldf, periods, selected_period)
    with tabs[4]: tab_wins(df, ldf, periods, selected_period)
    with tabs[5]: tab_forecast(df, ldf, periods, selected_period)
    with tabs[6]: tab_potholes(df, ldf, periods, selected_period)

if __name__ == "__main__":
    main()
