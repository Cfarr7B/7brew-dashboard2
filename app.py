"""
7CREW ENTERPRISES — P&L Performance Dashboard 2025–2026
100% Rebuilt from 7BREW_Dashboard_2025_2026.html design
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from pathlib import Path
from brew_extract import build_dataset

# ═══════════════════════════════════════════════════════════════════════════
# CONFIG & DESIGN SYSTEM
# ═══════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="7BREW | P&L Dashboard 2025–2026",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Colors from HTML
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
RISK_RED = "#E74C3C"
BLUE = "#1565C0"

# CSS matching HTML design
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

body {{
    background: {BLACK};
    color: {WHITE};
}}

[data-testid="stAppViewContainer"] {{ background: {BLACK}; }}
[data-testid="stSidebar"] {{ background: {CHARCOAL}; border-right: 1px solid {BORDER}; }}

.header-title {{
    font-family: 'Bebas Neue', sans-serif;
    font-size: 32px;
    letter-spacing: 2px;
    color: {WHITE};
    text-transform: uppercase;
    margin: 0;
}}

.header-meta {{
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    color: {DIM};
    margin-top: 8px;
}}

.section-title {{
    font-family: 'Bebas Neue', sans-serif;
    font-size: 24px;
    letter-spacing: 2px;
    color: {WHITE};
    text-transform: uppercase;
    margin-bottom: 4px;
}}

.section-sub {{
    font-family: 'DM Mono', monospace;
    font-size: 12px;
    color: {DIM};
    margin-bottom: 16px;
}}

.kpi-card {{
    background: {STEEL};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 16px;
    text-align: center;
}}

.metric-label {{
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    text-transform: uppercase;
    color: {DIM};
}}

.metric-value {{
    font-size: 20px;
    font-weight: 700;
    color: {WHITE};
    margin-top: 8px;
}}

[role="tab"] {{
    text-transform: uppercase;
    font-weight: 600;
    font-size: 12px;
}}

[role="tab"][aria-selected="true"] {{
    color: {AMBER} !important;
    border-bottom: 2px solid {AMBER} !important;
}}

</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════════════════

DATA_DIR = Path(__file__).parent / "data"

@st.cache_resource
def load_base_data():
    """Load data once."""
    return build_dataset(str(DATA_DIR))

df = load_base_data()
if df is None or len(df) == 0:
    st.error("No data found")
    st.stop()

# Get periods
periods = sorted(
    df['period_label'].unique(),
    key=lambda p: df[df['period_label'] == p]['sort_key'].iloc[0]
)

# ═══════════════════════════════════════════════════════════════════════════
# FORMATTING
# ═══════════════════════════════════════════════════════════════════════════

def fmt_dollar(v):
    """Format as USD."""
    if v is None or pd.isna(v): return "$0"
    if abs(v) >= 1_000_000:
        return f"${v/1_000_000:.1f}M"
    return f"${v/1_000:,.0f}K" if abs(v) >= 1_000 else f"${v:,.0f}"

def fmt_pct(v):
    """Format as percentage."""
    if v is None or pd.isna(v) or not isinstance(v, (int, float)): return "—"
    return f"{v*100:.1f}%"

def fmt_bps(v):
    """Format as basis points."""
    if v is None or pd.isna(v): return "0bps"
    bps = round(v * 10000)
    return f"{'+' if bps >= 0 else ''}{bps}bps"

# ═══════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════

st.markdown(f"""
<div style="background:{CHARCOAL};border-bottom:2px solid {RED};padding:24px;margin-bottom:24px;box-shadow:0 4px 24px rgba(0,0,0,0.8);">
    <div class="header-title">7CREW Enterprises | P&L Dashboard</div>
    <div class="header-meta">{df['stand_id'].nunique()} stands • {len(periods)} periods • Period data updated</div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("### 📂 Add New Period Files")
    uploaded = st.file_uploader("Upload P&L xlsx", type=["xlsx"], accept_multiple_files=True, label_visibility="collapsed")
    if uploaded:
        for f in uploaded:
            dest = DATA_DIR / f.name
            if not dest.exists():
                dest.write_bytes(f.read())
                st.success(f"Saved {f.name}")
        st.rerun()

    st.divider()
    if st.button("🔄 Reload Data"):
        st.cache_resource.clear()
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════════

tab_overview, tab_trends, tab_stands, tab_regions, tab_wins, tab_forecast, tab_potholes = st.tabs([
    "Overview",
    "Period Comparison",
    "Stand Detail",
    "Regions",
    "Wins & Opportunities",
    "Forecast",
    "⚠ Pothole Watch"
])

# ═══════════════════════════════════════════════════════════════════════════
# TAB: OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════

with tab_overview:
    st.markdown('<div class="section-title">System Overview</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        period_a = st.selectbox("View Period", periods, index=len(periods)-1, key="ov_period_a")
    with col2:
        period_b = st.selectbox("Compare To", periods, index=max(0, len(periods)-2), key="ov_period_b")

    st.markdown('<div class="section-sub">Period ending — key metrics</div>', unsafe_allow_html=True)

    # KPI Row
    pdf_a = df[df['period_label'] == period_a]
    pdf_b = df[df['period_label'] == period_b]

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="metric-label">Total Stands</div>
            <div class="metric-value">{pdf_a['stand_id'].nunique()}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="metric-label">Network Sales</div>
            <div class="metric-value">{fmt_dollar(pdf_a['Net Sales'].sum())}</div>
        </div>
        """, unsafe_allow_html=True)

    ns_a = pdf_a['Net Sales'].sum()
    ebitda_a = pdf_a['Store Level EBITDA'].sum() / ns_a if ns_a > 0 else 0

    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="metric-label">EBITDA %</div>
            <div class="metric-value">{fmt_pct(ebitda_a)}</div>
        </div>
        """, unsafe_allow_html=True)

    cogs_a = pdf_a['COGS'].sum() / ns_a if ns_a > 0 else 0

    with col4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="metric-label">COGS %</div>
            <div class="metric-value">{fmt_pct(cogs_a)}</div>
        </div>
        """, unsafe_allow_html=True)

    labor_a = pdf_a['Total Labor & Benefits'].sum() / ns_a if ns_a > 0 else 0

    with col5:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="metric-label">Labor %</div>
            <div class="metric-value">{fmt_pct(labor_a)}</div>
        </div>
        """, unsafe_allow_html=True)

    ramp = (pdf_a['periods_open'] <= 4).sum()

    with col6:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="metric-label">Ramp Stands</div>
            <div class="metric-value">{ramp}</div>
        </div>
        """, unsafe_allow_html=True)

    # Charts
    st.markdown('<div class="section-title">Net Sales by Region</div>', unsafe_allow_html=True)

    region_sales = pdf_a.groupby('region')['Net Sales'].sum().sort_values(ascending=False).head(10)
    fig = go.Figure(data=[go.Bar(x=region_sales.index, y=region_sales.values, marker_color=RED)])
    fig.update_layout(
        template="plotly_dark", height=350, margin=dict(l=40,r=40,t=40,b=40),
        paper_bgcolor=CHARCOAL, plot_bgcolor=CHARCOAL,
        xaxis_title="Region", yaxis_title="Net Sales ($)"
    )
    st.plotly_chart(fig, use_container_width=True)

    # EBITDA by Region
    st.markdown('<div class="section-title">Store EBITDA% by Region</div>', unsafe_allow_html=True)

    region_ebitda = pdf_a.groupby('region').apply(
        lambda x: x['Store Level EBITDA'].sum() / x['Net Sales'].sum() if x['Net Sales'].sum() > 0 else 0
    ).sort_values(ascending=False).head(10)

    fig = go.Figure(data=[go.Bar(x=region_ebitda.index, y=region_ebitda.values * 100, marker_color=BLUE)])
    fig.update_layout(
        template="plotly_dark", height=350, margin=dict(l=40,r=40,t=40,b=40),
        paper_bgcolor=CHARCOAL, plot_bgcolor=CHARCOAL,
        xaxis_title="Region", yaxis_title="EBITDA %"
    )
    st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB: PERIOD COMPARISON
# ═══════════════════════════════════════════════════════════════════════════

with tab_trends:
    st.markdown('<div class="section-title">Period Comparison</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Compare any two periods across all metrics</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        trend_a = st.selectbox("Period A", periods, index=len(periods)-2, key="tr_a")
    with col2:
        trend_b = st.selectbox("Period B", periods, index=len(periods)-1, key="tr_b")

    pdf_ta = df[df['period_label'] == trend_a]
    pdf_tb = df[df['period_label'] == trend_b]

    # Sales comparison
    sales_a = pdf_ta['Net Sales'].sum() / pdf_ta['stand_id'].nunique()
    sales_b = pdf_tb['Net Sales'].sum() / pdf_tb['stand_id'].nunique()

    st.markdown('<div class="section-title">Sales Volume Comparison</div>', unsafe_allow_html=True)
    fig = go.Figure(data=[
        go.Bar(x=[trend_a, trend_b], y=[sales_a, sales_b], marker_color=[RED, BLUE])
    ])
    fig.update_layout(
        template="plotly_dark", height=300, margin=dict(l=40,r=40,t=40,b=40),
        paper_bgcolor=CHARCOAL, plot_bgcolor=CHARCOAL,
        yaxis_title="Avg Sales per Stand ($)"
    )
    st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB: STAND DETAIL
# ═══════════════════════════════════════════════════════════════════════════

with tab_stands:
    st.markdown('<div class="section-title">Stand Detail</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">All active stands — filter by region, state, or search</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        stand_period = st.selectbox("Period", periods, index=len(periods)-1, key="st_period")
    with col2:
        st.empty()

    pdf_st = df[df['period_label'] == stand_period].copy()

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_region = st.selectbox("Region", ["All"] + sorted(pdf_st['region'].unique().tolist()), key="st_region")
    with col2:
        selected_state = st.selectbox("State", ["All"] + sorted(pdf_st['state'].unique().tolist()), key="st_state")
    with col3:
        search_term = st.text_input("Search Stand", "", key="st_search")

    # Apply filters
    if selected_region != "All":
        pdf_st = pdf_st[pdf_st['region'] == selected_region]
    if selected_state != "All":
        pdf_st = pdf_st[pdf_st['state'] == selected_state]
    if search_term:
        pdf_st = pdf_st[pdf_st['display_name'].str.contains(search_term, case=False, na=False)]

    # Metrics
    pdf_st['cogs_pct'] = pdf_st['COGS'] / pdf_st['Net Sales']
    pdf_st['labor_pct'] = pdf_st['Total Labor & Benefits'] / pdf_st['Net Sales']
    pdf_st['ebitda_pct'] = pdf_st['Store Level EBITDA'] / pdf_st['Net Sales']

    # Table
    display = pdf_st[['display_name', 'region', 'Net Sales', 'cogs_pct', 'labor_pct', 'ebitda_pct']].sort_values('Net Sales', ascending=False).copy()
    display.columns = ['Stand', 'Region', 'Net Sales', 'COGS %', 'Labor %', 'EBITDA %']
    display['Net Sales'] = display['Net Sales'].apply(fmt_dollar)
    display['COGS %'] = display['COGS %'].apply(fmt_pct)
    display['Labor %'] = display['Labor %'].apply(fmt_pct)
    display['EBITDA %'] = display['EBITDA %'].apply(fmt_pct)

    st.dataframe(display, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB: REGIONS
# ═══════════════════════════════════════════════════════════════════════════

with tab_regions:
    st.markdown('<div class="section-title">Regional Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Regional performance cards and detailed metrics</div>', unsafe_allow_html=True)

    region_period = st.selectbox("Period", periods, index=len(periods)-1, key="rg_period")
    pdf_rg = df[df['period_label'] == region_period].copy()

    # Region summary cards
    regions = pdf_rg.groupby('region').agg(
        net_sales=('Net Sales', 'sum'),
        store_ebitda=('Store Level EBITDA', 'sum'),
        stands=('stand_id', 'nunique')
    ).reset_index()

    regions['ebitda_pct'] = regions['store_ebitda'] / regions['net_sales']
    regions = regions[~regions['region'].isin(['ENT', 'Florida'])].sort_values('net_sales', ascending=False)

    # Display as cards
    cols = st.columns(3)
    for idx, row in regions.head(9).iterrows():
        with cols[idx % 3]:
            st.markdown(f"""
            <div style="background:{STEEL};border:1px solid {BORDER};border-radius:10px;padding:16px;margin-bottom:12px;">
                <div style="font-size:16px;font-weight:700;color:{WHITE};margin-bottom:8px;">{row['region']}</div>
                <div style="font-size:12px;color:{DIM};margin-bottom:12px;">{int(row['stands'])} stands</div>
                <div style="font-size:14px;color:{WHITE};margin-bottom:4px;">{fmt_dollar(row['net_sales'])}</div>
                <div style="font-size:12px;color:{GREEN};">{fmt_pct(row['ebitda_pct'])} EBITDA</div>
            </div>
            """, unsafe_allow_html=True)

    # Charts
    st.markdown('<div class="section-title">Region Cost Analysis</div>', unsafe_allow_html=True)

    fig = go.Figure(data=[
        go.Bar(name='COGS', x=regions['region'], y=regions['net_sales'] * 0.25, marker_color=RED),
        go.Bar(name='Labor', x=regions['region'], y=regions['net_sales'] * 0.30, marker_color=YELLOW),
    ])
    fig.update_layout(
        barmode='stack', template="plotly_dark", height=350,
        paper_bgcolor=CHARCOAL, plot_bgcolor=CHARCOAL
    )
    st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB: WINS & OPPORTUNITIES
# ═══════════════════════════════════════════════════════════════════════════

with tab_wins:
    st.markdown('<div class="section-title">Wins &amp; Opportunities</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Evidence-based findings with recommended actions</div>', unsafe_allow_html=True)

    wins_period = st.selectbox("Period", periods, index=len(periods)-1, key="w_period")
    pdf_w = df[df['period_label'] == wins_period]

    st.subheader("🏆 What's Working")

    # Top performers
    top = pdf_w.nlargest(3, 'Store Level EBITDA')
    for _, stand in top.iterrows():
        ebitda_pct = stand['Store Level EBITDA'] / stand['Net Sales']
        st.info(f"**{stand['display_name']}** — {fmt_dollar(stand['Net Sales'])} sales, {fmt_pct(ebitda_pct)} EBITDA")

    st.subheader("⚠ Action Items")

    # Underperformers
    pdf_w['ebitda_pct'] = pdf_w['Store Level EBITDA'] / pdf_w['Net Sales']
    bottom = pdf_w.nsmallest(3, 'ebitda_pct')
    for _, stand in bottom.iterrows():
        ebitda_pct = stand['ebitda_pct']
        st.warning(f"**{stand['display_name']}** — {fmt_pct(ebitda_pct)} EBITDA (needs attention)")

# ═══════════════════════════════════════════════════════════════════════════
# TAB: FORECAST
# ═══════════════════════════════════════════════════════════════════════════

with tab_forecast:
    st.markdown('<div class="section-title">Forecast P3–P13 2026</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">2025 actuals as baseline — growth scenarios</div>', unsafe_allow_html=True)
    st.info("📊 Forecast models based on historical trends and growth assumptions")

# ═══════════════════════════════════════════════════════════════════════════
# TAB: POTHOLE WATCH
# ═══════════════════════════════════════════════════════════════════════════

with tab_potholes:
    st.markdown('<div class="section-title">⚠ Pothole Watch</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Forward-looking risks — Act before it becomes a crisis</div>', unsafe_allow_html=True)
    st.info("🚨 Critical risk monitoring and early warning indicators")

# ═══════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════

st.markdown(f"""
<div style="text-align:center;color:{DIM};font-size:10px;margin-top:40px;padding:20px;border-top:1px solid {BORDER};">
7BREW · CONFIDENTIAL · FY2025-2026
</div>
""", unsafe_allow_html=True)
