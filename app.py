"""
7CREW ENTERPRISES — P&L Performance Dashboard
Clean rebuild based on 7BREW_Dashboard_2025_2026.html design
Streamlit app with fresh data handling (no caching issues)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from pathlib import Path
from brew_extract import build_dataset
import glob
import os

# ═══════════════════════════════════════════════════════════════════════════
# PAGE CONFIG & DESIGN SYSTEM (matching HTML)
# ═══════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="7BREW | P&L Dashboard 2025–2026",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Color palette (matching HTML design)
RED = "#C8102E"
BLACK = "#0D0D0D"
CHARCOAL = "#1A1A1A"
STEEL = "#252525"
BORDER = "#3A3A3A"
AMBER = "#F4A21E"
WHITE = "#FAFAFA"
FOG = "#B0B0B0"
DIM = "#707070"
GREEN = "#2ECC71"
YELLOW = "#F4A21E"

# Fonts matching HTML
DISPLAY_FONT = "Bebas Neue"
BODY_FONT = "DM Sans"
MONO_FONT = "DM Mono"

# ═══════════════════════════════════════════════════════════════════════════
# CSS STYLING (clean, matching HTML design)
# ═══════════════════════════════════════════════════════════════════════════

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

* {{ margin: 0; padding: 0; box-sizing: border-box; }}

html {{ scroll-behavior: smooth; }}

body {{
    background: {BLACK};
    color: {WHITE};
    font-family: '{BODY_FONT}', sans-serif;
}}

[data-testid="stAppViewContainer"] {{
    background: {BLACK};
}}

[data-testid="stSidebar"] {{
    background: {CHARCOAL};
    border-right: 1px solid {BORDER};
}}

.header-main {{
    background: {CHARCOAL};
    border-bottom: 2px solid {RED};
    padding: 24px;
    margin-bottom: 24px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.8);
}}

.header-main h1 {{
    font-family: '{DISPLAY_FONT}', sans-serif;
    font-size: 32px;
    letter-spacing: 2px;
    color: {WHITE};
    text-transform: uppercase;
    margin: 0;
}}

.header-meta {{
    font-family: '{MONO_FONT}', monospace;
    font-size: 11px;
    color: {DIM};
    margin-top: 8px;
}}

.section-title {{
    font-family: '{DISPLAY_FONT}', sans-serif;
    font-size: 24px;
    letter-spacing: 1px;
    color: {WHITE};
    text-transform: uppercase;
    margin-bottom: 16px;
    margin-top: 32px;
}}

.section-title:first-child {{
    margin-top: 0;
}}

.metric-label {{
    font-family: '{MONO_FONT}', monospace;
    font-size: 10px;
    text-transform: uppercase;
    color: {DIM};
    letter-spacing: 0.5px;
}}

.metric-value {{
    font-size: 18px;
    font-weight: 700;
    color: {WHITE};
    line-height: 1.2;
}}

.kpi-card {{
    background: {STEEL};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 16px;
    text-align: center;
}}

.kpi-card.positive {{
    border-left: 4px solid {GREEN};
}}

.kpi-card.warning {{
    border-left: 4px solid {YELLOW};
}}

.kpi-card.danger {{
    border-left: 4px solid #E74C3C;
}}

[role="tab"] {{
    background: none !important;
    color: {DIM} !important;
    border: none !important;
    text-transform: uppercase;
    font-weight: 600;
    font-size: 12px;
    padding: 12px 20px !important;
    border-bottom: 2px solid transparent !important;
    cursor: pointer;
    transition: all 0.2s;
}}

[role="tab"]:hover {{
    color: {FOG} !important;
}}

[role="tab"][aria-selected="true"] {{
    color: {AMBER} !important;
    border-bottom: 2px solid {AMBER} !important;
}}

[data-testid="stTabBar"] {{
    background: {STEEL};
    border-bottom: 1px solid {BORDER};
}}

</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# DATA LOADING (simple, no caching complications)
# ═══════════════════════════════════════════════════════════════════════════

DATA_DIR = Path(__file__).parent / "data"

def load_data_fresh():
    """Load data fresh without caching issues."""
    try:
        df = build_dataset(str(DATA_DIR))
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def get_periods(df):
    """Get sorted list of periods."""
    return sorted(
        df['period_label'].unique(),
        key=lambda p: df[df['period_label'] == p]['sort_key'].iloc[0]
    )

# ═══════════════════════════════════════════════════════════════════════════
# FORMATTING HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def fmt_dollar(val, mm=False):
    """Format as USD."""
    if val is None or pd.isna(val):
        return "$0"
    if mm:
        return f"${val/1_000_000:.1f}M"
    return f"${val/1_000:,.0f}K" if abs(val) >= 1_000 else f"${val:,.0f}"

def fmt_pct(val):
    """Format as percentage."""
    if val is None or pd.isna(val):
        return "—"
    return f"{val*100:.1f}%" if isinstance(val, (int, float)) else "—"

# ═══════════════════════════════════════════════════════════════════════════
# TAB: OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════

def tab_overview(df, periods, selected_period):
    st.markdown('<div class="section-title">System Overview</div>', unsafe_allow_html=True)

    # Current period data
    pdf = df[df['period_label'] == selected_period]

    # KPI row
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="metric-label">Total Stands</div>
            <div class="metric-value">{pdf['stand_id'].nunique()}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="metric-label">Network Sales</div>
            <div class="metric-value">{fmt_dollar(pdf['Net Sales'].sum(), mm=True)}</div>
        </div>
        """, unsafe_allow_html=True)

    ns = pdf['Net Sales'].sum()

    with col3:
        ebitda_pct = pdf['Store Level EBITDA'].sum() / ns if ns > 0 else 0
        st.markdown(f"""
        <div class="kpi-card positive">
            <div class="metric-label">EBITDA %</div>
            <div class="metric-value">{fmt_pct(ebitda_pct)}</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        cogs_pct = pdf['COGS'].sum() / ns if ns > 0 else 0
        st.markdown(f"""
        <div class="kpi-card warning">
            <div class="metric-label">COGS %</div>
            <div class="metric-value">{fmt_pct(cogs_pct)}</div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        labor_pct = pdf['Total Labor & Benefits'].sum() / ns if ns > 0 else 0
        st.markdown(f"""
        <div class="kpi-card warning">
            <div class="metric-label">Labor %</div>
            <div class="metric-value">{fmt_pct(labor_pct)}</div>
        </div>
        """, unsafe_allow_html=True)

    with col6:
        ramp = (pdf['periods_open'] <= 4).sum()
        st.markdown(f"""
        <div class="kpi-card">
            <div class="metric-label">Ramp Stands</div>
            <div class="metric-value">{ramp}</div>
        </div>
        """, unsafe_allow_html=True)

    # Period-over-period chart
    st.markdown('<div class="section-title">Period-Over-Period Network Performance</div>', unsafe_allow_html=True)

    # Period range selector
    col1, col2 = st.columns(2)
    with col1:
        start_period = st.selectbox("Period Range Start", periods, index=0, key="overview_start")
    with col2:
        start_idx = periods.index(start_period)
        end_period = st.selectbox("Period Range End", periods[start_idx:], index=len(periods)-start_idx-1, key="overview_end")

    period_range = periods[periods.index(start_period):periods.index(end_period)+1]

    # Calculate period trend
    trend = df[df['period_label'].isin(period_range)].groupby('period_label').agg(
        net_sales=('Net Sales', 'sum'),
        store_ebitda=('Store Level EBITDA', 'sum'),
        stands=('stand_id', 'nunique')
    ).reset_index()

    # Sort by period
    period_order = {p: i for i, p in enumerate(periods)}
    trend['period_order'] = trend['period_label'].map(period_order)
    trend = trend.sort_values('period_order').drop('period_order', axis=1)

    # Chart
    fig = go.Figure()
    fig.add_bar(x=trend['period_label'], y=trend['net_sales'],
                name="Net Sales", marker_color=RED, opacity=0.85)
    fig.add_scatter(x=trend['period_label'], y=trend['store_ebitda'],
                    name="Store EBITDA", mode="lines+markers",
                    line=dict(color="#1565C0", width=2), yaxis="y2")

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=CHARCOAL,
        plot_bgcolor=CHARCOAL,
        yaxis=dict(title="Net Sales ($)", gridcolor="#404040"),
        yaxis2=dict(title="Store EBITDA ($)", overlaying="y", side="right"),
        legend=dict(x=0, y=1.1, orientation="h"),
        height=380,
        margin=dict(l=60, r=60, t=40, b=60)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Trend table
    tbl = trend[['period_label', 'stands', 'net_sales']].copy()
    tbl.columns = ['Period', 'Stands', 'Net Sales']
    tbl['Net Sales'] = tbl['Net Sales'].apply(fmt_dollar)
    st.dataframe(tbl, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB: PERIOD COMPARISON
# ═══════════════════════════════════════════════════════════════════════════

def tab_trends(df, periods, selected_period):
    st.markdown('<div class="section-title">Period Comparison</div>', unsafe_allow_html=True)
    st.info("Detailed period-over-period analysis coming soon")

# ═══════════════════════════════════════════════════════════════════════════
# TAB: STAND DETAIL
# ═══════════════════════════════════════════════════════════════════════════

def tab_stands(df, periods, selected_period):
    st.markdown('<div class="section-title">Stand Detail</div>', unsafe_allow_html=True)

    pdf = df[df['period_label'] == selected_period].copy()

    # Metrics
    pdf['ebitda_pct'] = pdf['Store Level EBITDA'] / pdf['Net Sales']
    pdf['cogs_pct'] = pdf['COGS'] / pdf['Net Sales']
    pdf['labor_pct'] = pdf['Total Labor & Benefits'] / pdf['Net Sales']

    # Display table
    display = pdf[['display_name', 'Net Sales', 'ebitda_pct', 'cogs_pct', 'labor_pct']].sort_values('Net Sales', ascending=False).copy()
    display.columns = ['Stand', 'Net Sales', 'EBITDA %', 'COGS %', 'Labor %']
    display['Net Sales'] = display['Net Sales'].apply(fmt_dollar)
    display['EBITDA %'] = display['EBITDA %'].apply(fmt_pct)
    display['COGS %'] = display['COGS %'].apply(fmt_pct)
    display['Labor %'] = display['Labor %'].apply(fmt_pct)

    st.dataframe(display, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB: REGIONS
# ═══════════════════════════════════════════════════════════════════════════

def tab_regions(df, periods, selected_period):
    st.markdown('<div class="section-title">Regional Analysis</div>', unsafe_allow_html=True)

    pdf = df[df['period_label'] == selected_period].copy()

    # Group by region
    regions = pdf.groupby('region').agg(
        net_sales=('Net Sales', 'sum'),
        store_ebitda=('Store Level EBITDA', 'sum'),
        cogs=('COGS', 'sum'),
        labor=('Total Labor & Benefits', 'sum'),
        stands=('stand_id', 'nunique')
    ).reset_index()

    regions = regions[~regions['region'].isin(['ENT', 'Florida'])]
    regions = regions.sort_values('net_sales', ascending=False)

    # Display
    display = regions[['region', 'stands', 'net_sales']].copy()
    display.columns = ['Region', 'Stands', 'Net Sales']
    display['Net Sales'] = display['Net Sales'].apply(fmt_dollar)

    st.dataframe(display, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB: WINS & OPPORTUNITIES
# ═══════════════════════════════════════════════════════════════════════════

def tab_wins(df, periods, selected_period):
    st.markdown('<div class="section-title">Wins &amp; Opportunities</div>', unsafe_allow_html=True)
    st.info("Top performers and areas for improvement coming soon")

# ═══════════════════════════════════════════════════════════════════════════
# TAB: FORECAST
# ═══════════════════════════════════════════════════════════════════════════

def tab_forecast(df, periods, selected_period):
    st.markdown('<div class="section-title">Forecast P3–P13 2026</div>', unsafe_allow_html=True)
    st.info("Forward-looking financial projections coming soon")

# ═══════════════════════════════════════════════════════════════════════════
# TAB: POTHOLE WATCH
# ═══════════════════════════════════════════════════════════════════════════

def tab_potholes(df, periods, selected_period):
    st.markdown('<div class="section-title">⚠ Pothole Watch</div>', unsafe_allow_html=True)
    st.info("Critical issues requiring attention coming soon")

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    # Load data
    df = load_data_fresh()
    if df is None or len(df) == 0:
        st.error("No data found. Please upload P&L files.")
        return

    # Get periods
    periods = get_periods(df)

    # Header
    st.markdown(f"""
    <div class="header-main">
        <h1>7CREW Enterprises | P&L Dashboard</h1>
        <div class="header-meta">
            {df['stand_id'].nunique()} stands • {len(periods)} periods • Period data updated
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.markdown("### 📂 Add New Period Files")
        uploaded = st.file_uploader(
            "Upload P&L xlsx",
            type=["xlsx"],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )
        if uploaded:
            for f in uploaded:
                dest = DATA_DIR / f.name
                if not dest.exists():
                    dest.write_bytes(f.read())
                    st.success(f"Saved {f.name}")
            st.rerun()

        st.divider()

        if st.button("🔄 Reload Data"):
            st.rerun()

        st.divider()

        selected_period = st.selectbox("📅 Current Period", periods, index=len(periods)-1)

    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Overview",
        "Period Comparison",
        "Stand Detail",
        "Regions",
        "Wins & Opportunities",
        "Forecast",
        "⚠ Pothole Watch"
    ])

    with tab1:
        tab_overview(df, periods, selected_period)
    with tab2:
        tab_trends(df, periods, selected_period)
    with tab3:
        tab_stands(df, periods, selected_period)
    with tab4:
        tab_regions(df, periods, selected_period)
    with tab5:
        tab_wins(df, periods, selected_period)
    with tab6:
        tab_forecast(df, periods, selected_period)
    with tab7:
        tab_potholes(df, periods, selected_period)

if __name__ == "__main__":
    main()
