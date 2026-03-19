"""
7CREW ENTERPRISES — P&L Performance Dashboard
Streamlit App  |  github.com/your-org/7brew-dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
import glob
import tempfile
from pathlib import Path

from brew_extract import build_dataset

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="7CREW | P&L Dashboard",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Brand palette ─────────────────────────────────────────────────────────────
RED       = "#C8102E"
RED_DARK  = "#8B0000"
BLACK     = "#1A1A1A"
CHARCOAL  = "#2D2D2D"
WHITE     = "#FFFFFF"
GOOD_BG   = "#E8F5E9"; GOOD_TXT = "#1B5E20"
WARN_BG   = "#FFF8E1"; WARN_TXT = "#5D4037"
BAD_BG    = "#FFEBEE"; BAD_TXT  = "#B71C1C"
WATCH_BG  = "#E3F2FD"; WATCH_TXT= "#0D47A1"
Q4_COHORTS = {"P10'25", "P11'25", "P12'25", "P13'25", "P1'26"}

PLOTLY_COLORS = [RED, "#1565C0", "#2E7D32", "#F9A825",
                 "#6A1B9A", "#00838F", "#4E342E", "#37474F"]

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
/* Sidebar */
[data-testid="stSidebar"] {{
    background: {BLACK};
}}
[data-testid="stSidebar"] * {{ color: #E0E0E0 !important; }}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stMultiSelect label {{ color: #B0B0B0 !important; font-size:12px; }}

/* Main header */
.brew-header {{
    background: {BLACK};
    border-left: 5px solid {RED};
    padding: 14px 20px;
    border-radius: 6px;
    margin-bottom: 18px;
}}
.brew-header h1 {{
    color: {WHITE}; font-size: 22px; font-weight: 800;
    letter-spacing: 2px; margin: 0; text-transform: uppercase;
}}
.brew-header p {{ color: #A0A0A0; font-size: 12px; margin: 4px 0 0; }}

/* Section headers */
.brew-section {{
    background: {CHARCOAL};
    border-left: 4px solid {RED};
    padding: 8px 16px;
    border-radius: 4px;
    margin: 20px 0 10px;
    color: {WHITE};
    font-weight: 700;
    font-size: 13px;
    letter-spacing: 1px;
    text-transform: uppercase;
}}

/* KPI cards */
.kpi-card {{
    background: {BLACK};
    border-top: 3px solid {RED};
    border-radius: 8px;
    padding: 16px;
    text-align: center;
}}
.kpi-label {{
    color: #808080;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 6px;
}}
.kpi-value {{ font-size: 28px; font-weight: 800; margin: 0; line-height: 1; }}
.kpi-sub {{ color: #808080; font-size: 11px; margin-top: 4px; }}
.kpi-good  {{ color: {GOOD_TXT}; }}
.kpi-warn  {{ color: #F9A825; }}
.kpi-bad   {{ color: {BAD_TXT}; }}
.kpi-white {{ color: {WHITE}; }}
.kpi-red   {{ color: {RED}; }}

/* Q4 banner */
.q4-banner {{
    background: {WATCH_BG};
    border-left: 4px solid {WATCH_TXT};
    padding: 10px 16px;
    border-radius: 4px;
    color: {WATCH_TXT};
    font-size: 12px;
    margin-bottom: 16px;
}}

/* Hide Streamlit branding */
#MainMenu, footer {{ visibility: hidden; }}
</style>
""", unsafe_allow_html=True)

# ── Data loading ──────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent / "data"

@st.cache_data(show_spinner="Reading P&L files…")
def load_data(file_paths_key: str):
    """Load and cache the consolidated dataset."""
    return build_dataset(str(DATA_DIR))

def get_file_key():
    files = sorted(glob.glob(str(DATA_DIR / "7BREW Income Statement Side By Side PTD All*.xlsx")))
    return "|".join(f"{p}:{os.path.getmtime(p):.0f}" for p in files)

# ── Helpers ───────────────────────────────────────────────────────────────────

def safe_pct(num, den):
    try:
        v = num / den
        return v if np.isfinite(v) else None
    except Exception:
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

def traffic_color(value, target, higher_better=True, tol=0.03):
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return ""
    diff = (value - target) if higher_better else (target - value)
    if diff >= tol:    return f"background-color:{GOOD_BG};color:{GOOD_TXT}"
    if diff <= -tol:   return f"background-color:{BAD_BG};color:{BAD_TXT}"
    return f"background-color:{WARN_BG};color:{WARN_TXT}"

def kpi_card(label, value, sub="", cls="kpi-white"):
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value {cls}">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>"""

def section(title):
    st.markdown(f'<div class="brew-section">{title}</div>', unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────

def sidebar_controls(df):
    with st.sidebar:
        logo_path = Path(__file__).parent / "assets" / "logo.png"
        if logo_path.exists():
            st.image(str(logo_path), width=180)
        else:
            st.markdown(f"## <span style='color:{RED}'>7CREW</span> ENTERPRISES", unsafe_allow_html=True)

        st.divider()

        # File uploader
        with st.expander("📂 Add New Period Files", expanded=True):
            st.caption("Drop a new P&L xlsx here to add it to the dataset. "
                       "Files are saved to the data/ folder.")
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

        periods = sorted(df['period_label'].unique(),
                         key=lambda p: df[df['period_label']==p]['sort_key'].iloc[0])
        selected_period = st.selectbox("📅 Current Period", periods,
                                       index=len(periods)-1)

        regions = ["All"] + sorted(df['region'].unique().tolist())
        selected_region = st.selectbox("🗺️ Region", regions)

        cohorts = ["All"] + sorted(
            df['cohort'].unique().tolist(),
            key=lambda c: (0 if c=="Legacy (Pre-Data)" else 1, c))
        selected_cohort = st.multiselect("📦 Cohort", cohorts[1:],
                                         placeholder="All cohorts")

        st.divider()
        st.caption(f"**{df['stand_id'].nunique()}** stands  |  "
                   f"**{df['period_label'].nunique()}** periods")
        st.caption(f"Last updated: {pd.Timestamp.now().strftime('%m/%d/%Y')}")

    return selected_period, selected_region, selected_cohort, periods

def apply_filters(df, period, region, cohorts):
    ldf = df[df['period_label'] == period].copy()
    if region != "All":
        ldf = ldf[ldf['region'] == region]
    if cohorts:
        ldf = ldf[ldf['cohort'].isin(cohorts)]
    ldf['ebitda_pct'] = ldf['Store Level EBITDA'] / ldf['Net Sales'].replace(0, np.nan)
    ldf['cogs_pct']   = ldf['COGS'] / ldf['Net Sales'].replace(0, np.nan)
    ldf['labor_pct']  = ldf['Total Labor & Benefits'] / ldf['Net Sales'].replace(0, np.nan)
    return ldf

# ── Tab: CEO Summary ──────────────────────────────────────────────────────────

def tab_ceo(df, ldf, periods, selected_period):
    first_period = periods[0]
    fdf = df[df['period_label'] == first_period]
    mature = ldf[~ldf['is_ramp']]

    total_stands = ldf['stand_id'].nunique()
    total_ns     = ldf['Net Sales'].sum()
    first_ns     = fdf['Net Sales'].sum()
    growth       = safe_pct(total_ns - first_ns, first_ns)
    net_ebitda   = safe_pct(ldf['Store Level EBITDA'].sum(), total_ns)
    net_cogs     = safe_pct(ldf['COGS'].sum(), total_ns)
    net_labor    = safe_pct(ldf['Total Labor & Benefits'].sum(), total_ns)
    auv          = mature['Net Sales'].mean() if not mature.empty else 0

    # Network averages across all periods (used as benchmarks throughout)
    all_ns          = df['Net Sales'].sum()
    avg_ebitda_all  = safe_pct(df['Store Level EBITDA'].sum(), all_ns)
    avg_cogs_all    = safe_pct(df['COGS'].sum(), all_ns)
    avg_labor_all   = safe_pct(df['Total Labor & Benefits'].sum(), all_ns)

    # KPI row
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    cards = [
        (c1, "Total Stands",   str(total_stands),  f"vs {fdf['stand_id'].nunique()} in {first_period}", "kpi-white"),
        (c2, "Network Sales",  fmt_dollar(total_ns, mm=True), f"Avg Mature Unit {fmt_dollar(auv)}", "kpi-red"),
        (c3, "Store EBITDA %", fmt_pct(net_ebitda), f"Network Avg {fmt_pct(avg_ebitda_all)}",
         "kpi-good" if (net_ebitda or 0) >= (avg_ebitda_all or 0) else "kpi-bad"),
        (c4, "COGS %",         fmt_pct(net_cogs),  f"Network Avg {fmt_pct(avg_cogs_all)}",
         "kpi-good" if (net_cogs or 1) <= (avg_cogs_all or 1) else "kpi-bad"),
        (c5, "Labor %",        fmt_pct(net_labor), f"Network Avg {fmt_pct(avg_labor_all)}",
         "kpi-good" if (net_labor or 1) <= (avg_labor_all or 1) else "kpi-bad"),
        (c6, "Ramp Phase",     f"{int(ldf['is_ramp'].sum())} stands", "< 4 periods open", "kpi-warn"),
    ]
    for col, label, val, sub, cls in cards:
        col.markdown(kpi_card(label, val, sub, cls), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Period trend chart ──────────────────────────────────────────────────
    section("Period-Over-Period Network Performance")

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
                        line=dict(color="#1565C0", width=2),
                        yaxis="y2")
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor=CHARCOAL, plot_bgcolor=CHARCOAL,
            yaxis=dict(title="Net Sales ($)", gridcolor="#404040"),
            yaxis2=dict(title="Store EBITDA ($)", overlaying="y", side="right",
                        gridcolor="#404040"),
            legend=dict(x=0, y=1.1, orientation="h"),
            margin=dict(l=0,r=0,t=20,b=0), height=280,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_table:
        tbl = trend[['period_label','stands','net_sales','ebitda_pct']].copy()
        tbl.columns = ["Period","Stands","Net Sales","EBITDA %"]
        tbl["Net Sales"] = tbl["Net Sales"].apply(lambda x: fmt_dollar(x))
        tbl["EBITDA %"]  = tbl["EBITDA %"].apply(fmt_pct)
        st.dataframe(tbl, use_container_width=True, hide_index=True, height=280)

    # ── EBITDA % trend line ─────────────────────────────────────────────────
    col_l, col_r = st.columns(2)

    with col_l:
        section("EBITDA % by Period")
        fig2 = go.Figure()
        fig2.add_scatter(x=trend['period_label'], y=trend['ebitda_pct'],
                         mode="lines+markers",
                         line=dict(color=RED, width=3),
                         marker=dict(size=8))
        fig2.add_hline(y=avg_ebitda_all or 0, line_dash="dash",
                       line_color=GOOD_TXT, annotation_text=f"Network Avg {fmt_pct(avg_ebitda_all)}")
        fig2.update_layout(
            template="plotly_dark",
            paper_bgcolor=CHARCOAL, plot_bgcolor=CHARCOAL,
            yaxis=dict(tickformat=".0%", gridcolor="#404040"),
            margin=dict(l=0,r=0,t=10,b=0), height=220,
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col_r:
        section("Stand Count Growth")
        fig3 = go.Figure()
        fig3.add_bar(x=trend['period_label'], y=trend['stands'],
                     marker_color=CHARCOAL, marker_line_color=RED,
                     marker_line_width=1.5)
        fig3.update_layout(
            template="plotly_dark",
            paper_bgcolor=CHARCOAL, plot_bgcolor=CHARCOAL,
            yaxis=dict(gridcolor="#404040"),
            margin=dict(l=0,r=0,t=10,b=0), height=220,
        )
        st.plotly_chart(fig3, use_container_width=True)

    # ── Top / Bottom 10 ─────────────────────────────────────────────────────
    section(f"Top 10 vs Bottom 10 Mature Stores — EBITDA % ({selected_period})")
    mature2 = ldf[~ldf['is_ramp']].copy()
    mature2['ep'] = mature2['Store Level EBITDA'] / mature2['Net Sales'].replace(0, np.nan)

    col_top, col_bot = st.columns(2)
    for col, label, n_func, bg in [
        (col_top, "🏆 Top 10", lambda d: d.nlargest(10,'ep'), GOOD_BG),
        (col_bot, "⚠️ Bottom 10", lambda d: d.nsmallest(10,'ep'), BAD_BG),
    ]:
        with col:
            st.markdown(f"**{label}**")
            sub = n_func(mature2)[['display_name','Net Sales','ep','cogs_pct','labor_pct']].copy()
            sub.columns = ["Stand","Net Sales","EBITDA %","COGS %","Labor %"]
            sub["Net Sales"] = sub["Net Sales"].apply(fmt_dollar)
            for c in ["EBITDA %","COGS %","Labor %"]:
                sub[c] = sub[c].apply(fmt_pct)
            st.dataframe(sub, hide_index=True, use_container_width=True)


# ── Tab: COO Scorecard ────────────────────────────────────────────────────────

def tab_coo(df, ldf, periods, selected_period):
    section(f"Operations Scorecard — {selected_period}  "
            "| 🟢 EBITDA ≥15%  🟡 10–14%  🔴 <10%  |  ⚡ Ramp  🔵 Q4 Watch")

    prev_period = None
    sorted_periods = sorted(df['period_label'].unique(),
                            key=lambda p: df[df['period_label']==p]['sort_key'].iloc[0])
    idx = sorted_periods.index(selected_period)
    if idx > 0:
        prev_period = sorted_periods[idx - 1]
    pns = (df[df['period_label']==prev_period]
           .set_index('stand_id')['Net Sales'].to_dict() if prev_period else {})

    ldf2 = ldf.copy()
    ldf2['ebitda_pct'] = ldf2['Store Level EBITDA'] / ldf2['Net Sales'].replace(0, np.nan)
    ldf2['cogs_pct']   = ldf2['COGS'] / ldf2['Net Sales'].replace(0, np.nan)
    ldf2['labor_pct']  = ldf2['Total Labor & Benefits'] / ldf2['Net Sales'].replace(0, np.nan)
    ldf2['prev_ns']    = ldf2['stand_id'].map(pns)
    ldf2['delta_ns']   = ldf2['Net Sales'] - ldf2['prev_ns'].fillna(ldf2['Net Sales'])
    ldf2['is_q4']      = ldf2['cohort'].isin(Q4_COHORTS)
    ldf2['status']     = ldf2.apply(
        lambda r: "⚡ Ramp" if r['is_ramp'] else ("🔵 Q4 Watch" if r['is_q4'] else "Mature"), axis=1)

    display_cols = ['display_name','region','cohort','periods_open','status',
                    'Net Sales','delta_ns','cogs_pct','labor_pct','ebitda_pct',
                    'Store Level EBITDA']
    rename_map = {'display_name':'Stand','region':'Region','cohort':'Cohort',
                  'periods_open':'Periods Open','status':'Status',
                  'Net Sales':'Net Sales','delta_ns':'Δ vs Prior',
                  'cogs_pct':'COGS %','labor_pct':'Labor %',
                  'ebitda_pct':'EBITDA %','Store Level EBITDA':'EBITDA $'}

    tbl = ldf2.sort_values(['region','cohort','ebitda_pct'],
                           ascending=[True,True,False])[display_cols].rename(columns=rename_map)

    # Format columns
    for money_col in ['Net Sales','Δ vs Prior','EBITDA $']:
        tbl[money_col] = tbl[money_col].apply(fmt_dollar)
    for pct_col in ['COGS %','Labor %','EBITDA %']:
        tbl[pct_col] = tbl[pct_col].apply(fmt_pct)
    tbl['Periods Open'] = tbl['Periods Open'].astype(int)

    # Region filter toggle
    regions = ["All"] + sorted(ldf2['region'].unique())
    sel_r = st.radio("Region", regions, horizontal=True)
    if sel_r != "All":
        tbl = tbl[tbl['Region'] == sel_r]

    st.dataframe(tbl, hide_index=True, use_container_width=True, height=500)

    # ── COGS & Labor distribution ────────────────────────────────────────────
    # Compute network averages for reference lines
    _ns = ldf2['Net Sales'].replace(0, np.nan)
    avg_cogs   = (ldf2['COGS'] / _ns).mean()
    avg_labor  = (ldf2['Total Labor & Benefits'] / _ns).mean()
    avg_ebitda = (ldf2['Store Level EBITDA'] / _ns).mean()

    section("Metric Distribution")
    c1, c2, c3 = st.columns(3)
    for col, col_name, target, hb, title in [
        (c1, 'cogs_pct',  avg_cogs,   False, "COGS % Distribution"),
        (c2, 'labor_pct', avg_labor,  False, "Labor % Distribution"),
        (c3, 'ebitda_pct',avg_ebitda, True,  "EBITDA % Distribution"),
    ]:
        with col:
            vals = ldf2[col_name].dropna()
            fig = go.Figure()
            fig.add_histogram(x=vals, nbinsx=20, marker_color=RED,
                              marker_line_color=BLACK, marker_line_width=1)
            fig.add_vline(x=target, line_dash="dash", line_color=GOOD_TXT,
                          annotation_text=f"Avg {target:.1%}" if target else "")
            fig.update_layout(
                title=title, template="plotly_dark",
                paper_bgcolor=CHARCOAL, plot_bgcolor=CHARCOAL,
                xaxis=dict(tickformat=".0%"), margin=dict(l=0,r=0,t=30,b=0),
                height=220, showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)


# ── Tab: Q4 Class Watch ───────────────────────────────────────────────────────

def tab_q4(df, ldf, periods, selected_period):
    st.markdown(
        '<div class="q4-banner">⚠️  These stands open in Fall/Winter when foot traffic, '
        'hiring, and weather headwinds create naturally slower ramp curves. '
        'Performance is benchmarked against Q4 class averages, not the full network.'
        '</div>', unsafe_allow_html=True)

    q4_df   = df[df['cohort'].isin(Q4_COHORTS)].copy()
    q4_ldf  = ldf[ldf['cohort'].isin(Q4_COHORTS)].copy()
    q4_ldf['ep'] = q4_ldf['Store Level EBITDA'] / q4_ldf['Net Sales'].replace(0, np.nan)

    if q4_ldf.empty:
        st.info("No Q4 class stands match the current filters.")
        return

    # ── Q4 KPIs vs network ─────────────────────────────────────────────────
    net_ns    = ldf['Net Sales'].mean()
    q4_ns     = q4_ldf['Net Sales'].mean()
    net_ep    = safe_pct(ldf['Store Level EBITDA'].sum(), ldf['Net Sales'].sum())
    q4_ep     = safe_pct(q4_ldf['Store Level EBITDA'].sum(), q4_ldf['Net Sales'].sum())
    q4_count  = q4_ldf['stand_id'].nunique()
    q4_ramp   = int(q4_ldf['is_ramp'].sum())

    c1, c2, c3, c4, c5 = st.columns(5)
    cards = [
        (c1, "Q4 Stands",        str(q4_count),         f"{q4_ramp} still ramping",       "kpi-white"),
        (c2, "Q4 Avg Unit Sales", fmt_dollar(q4_ns),    f"Network avg {fmt_dollar(net_ns)}",
         "kpi-good" if q4_ns >= net_ns*0.8 else "kpi-warn"),
        (c3, "Q4 EBITDA %",      fmt_pct(q4_ep),        f"Network avg {fmt_pct(net_ep)}",
         "kpi-good" if (q4_ep or 0)>=0.10 else "kpi-warn"),
        (c4, "On Target",
         str(len(q4_ldf[q4_ldf['ep'] >= 0.10])),
         "EBITDA ≥ 10% (Q4 benchmark)", "kpi-good"),
        (c5, "Needs Attention",
         str(len(q4_ldf[q4_ldf['ep'] < 0.05])),
         "EBITDA < 5%", "kpi-bad"),
    ]
    for col, label, val, sub, cls in cards:
        col.markdown(kpi_card(label, val, sub, cls), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Ramp curve: Q4 vs benchmarks ────────────────────────────────────────
    section("Q4 Class Ramp Curve vs Benchmarks")

    legacy_df = df[df['cohort'] == 'Legacy (Pre-Data)']
    mid_df    = df[df['cohort'].isin({"P5'25","P6'25","P7'25","P8'25","P9'25"})]

    max_age = min(int(q4_df['periods_open'].max()), 14)
    ages = list(range(1, max_age + 1))

    fig = go.Figure()
    for label, subset, color, dash in [
        ("Q4 Class",          q4_df,     RED,       "solid"),
        ("Legacy Benchmark",  legacy_df, GOOD_TXT,  "dash"),
        ("Mid-Year '25",      mid_df,    "#1565C0",  "dot"),
    ]:
        y_vals = []
        for age in ages:
            adf = subset[subset['periods_open'] == age]
            y_vals.append(adf['Net Sales'].mean() if not adf.empty else None)
        fig.add_scatter(x=[f"P+{a}" for a in ages], y=y_vals,
                        name=label, mode="lines+markers",
                        line=dict(color=color, width=2.5, dash=dash),
                        marker=dict(size=7))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=CHARCOAL, plot_bgcolor=CHARCOAL,
        yaxis=dict(title="Avg Net Sales ($)", tickformat="$,.0f", gridcolor="#404040"),
        xaxis=dict(title="Periods Since Opening"),
        legend=dict(x=0, y=1.1, orientation="h"),
        margin=dict(l=0,r=0,t=20,b=0), height=300,
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Per-stand scorecard ──────────────────────────────────────────────────
    section(f"Q4 Stand Scorecard — {selected_period}  (benchmarked against Q4 class avg)")

    sorted_periods = sorted(df['period_label'].unique(),
                            key=lambda p: df[df['period_label']==p]['sort_key'].iloc[0])
    idx = sorted_periods.index(selected_period)
    prev2 = sorted_periods[idx-1] if idx > 0 else None
    prev3 = sorted_periods[idx-2] if idx > 1 else None

    pns_curr  = df[df['period_label']==selected_period].set_index('stand_id')['Net Sales'].to_dict()
    pns_prev  = df[df['period_label']==prev2].set_index('stand_id')['Net Sales'].to_dict() if prev2 else {}
    pns_pprev = df[df['period_label']==prev3].set_index('stand_id')['Net Sales'].to_dict() if prev3 else {}

    q4_avg_ns = q4_ldf['Net Sales'].mean()
    q4_avg_ep = q4_ldf['ep'].mean()

    rows = []
    for _, r in q4_ldf.sort_values(['cohort','ep'], ascending=[True, False]).iterrows():
        sid = r['stand_id']
        t_c = pns_curr.get(sid, 0)
        t_p = pns_prev.get(sid, 0)
        t_pp= pns_pprev.get(sid, 0)
        if t_c>0 and t_p>0 and t_pp>0:
            traj = ("↑↑ Accel" if t_c>t_p>t_pp else
                    "↑ Improving" if t_c>t_p else
                    "↓↓ Declining" if t_c<t_p<t_pp else
                    "↓ Softening" if t_c<t_p else "→ Stable")
        else:
            traj = "↑ New" if t_c>0 else "Opening"

        ep_v = r['ep']
        rows.append({
            "Stand":        r['display_name'],
            "Cohort":       r['cohort'],
            "Periods Open": int(r['periods_open']),
            "Net Sales":    fmt_dollar(r['Net Sales']),
            "vs Q4 Avg":    fmt_dollar((r['Net Sales'] - q4_avg_ns) if q4_avg_ns else None),
            "COGS %":       fmt_pct(r.get('cogs_pct')),
            "Labor %":      fmt_pct(r.get('labor_pct')),
            "EBITDA %":     fmt_pct(ep_v),
            "vs Q4 Avg ":   fmt_pct((ep_v - q4_avg_ep) if (ep_v is not None and q4_avg_ep) else None),
            "Trajectory":   traj,
            "Status":       ("✓ On Target" if (ep_v or 0)>=0.10 else
                             "⚠ Watching"  if (ep_v or 0)>=0.05 else "✗ Needs Help"),
        })

    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    # ── Individual stand trend charts ────────────────────────────────────────
    section("Individual Q4 Stand Trajectories")
    st.caption("Net Sales over all active periods for each Q4 class stand.")

    q4_stand_list = (q4_df.drop_duplicates('stand_id')
                     .sort_values(['cohort','display_name'])['display_name'].tolist())
    selected_stands = st.multiselect(
        "Select stands to chart", q4_stand_list,
        default=q4_stand_list[:min(6, len(q4_stand_list))])

    if selected_stands:
        fig2 = go.Figure()
        for i, stand in enumerate(selected_stands):
            sdf = (q4_df[q4_df['display_name']==stand]
                   .sort_values('sort_key'))
            fig2.add_scatter(
                x=[f"P+{p}" for p in sdf['periods_open']],
                y=sdf['Net Sales'],
                name=stand, mode="lines+markers",
                line=dict(color=PLOTLY_COLORS[i % len(PLOTLY_COLORS)], width=2),
                marker=dict(size=6),
            )
        fig2.update_layout(
            template="plotly_dark",
            paper_bgcolor=CHARCOAL, plot_bgcolor=CHARCOAL,
            yaxis=dict(title="Net Sales ($)", tickformat="$,.0f", gridcolor="#404040"),
            xaxis=dict(title="Periods Since Opening"),
            legend=dict(x=0, y=1.15, orientation="h"),
            margin=dict(l=0,r=0,t=20,b=0), height=320,
        )
        st.plotly_chart(fig2, use_container_width=True)


# ── Tab: EBITDA Trend ─────────────────────────────────────────────────────────

def tab_ebitda(df, periods):
    # Network average EBITDA % across all data (used as benchmark)
    _net_avg_ep = safe_pct(df['Store Level EBITDA'].sum(), df['Net Sales'].sum())
    _q4_avg_ep  = safe_pct(
        df[df['cohort'].isin(Q4_COHORTS)]['Store Level EBITDA'].sum(),
        df[df['cohort'].isin(Q4_COHORTS)]['Net Sales'].sum()
    )

    section("Store EBITDA % by Stand Across All Periods")
    st.caption(f"🟢 ≥ Network Avg {fmt_pct(_net_avg_ep)}  |  🟡 Within 5%  |  🔴 Below  |  🔵 Q4 Watch (Q4 class avg {fmt_pct(_q4_avg_ep)})")

    sorted_periods = sorted(periods,
                            key=lambda p: df[df['period_label']==p]['sort_key'].iloc[0])

    stands = (df.drop_duplicates('stand_id')[['stand_id','display_name','region','cohort']]
              .join(df.groupby('stand_id')['Net Sales'].sum().rename('_ns'), on='stand_id')
              .sort_values(['region','_ns'], ascending=[True, False]))

    # Build pivot
    rows = []
    for _, sr in stands.iterrows():
        sdf = df[df['stand_id']==sr['stand_id']]
        row = {"Stand": sr['display_name'], "Region": sr['region'], "Cohort": sr['cohort']}
        ep_vals = []
        for period in sorted_periods:
            prow = sdf[sdf['period_label']==period]
            if not prow.empty and prow['Net Sales'].iloc[0] > 0:
                ep = prow['Store Level EBITDA'].iloc[0] / prow['Net Sales'].iloc[0]
                row[period] = ep
                ep_vals.append(ep)
            else:
                row[period] = None
        row["Avg"] = np.mean(ep_vals) if ep_vals else None
        rows.append(row)

    tbl = pd.DataFrame(rows)

    # Colour-format period columns
    def color_cell(val, is_q4=False):
        if pd.isna(val) or val is None:
            return "background-color:#2D2D2D;color:#666"
        thr = _q4_avg_ep if is_q4 else _net_avg_ep
        thr = thr or 0.10
        if val >= thr:          return f"background-color:{GOOD_BG};color:{GOOD_TXT}"
        if val >= thr - 0.05:   return f"background-color:{WARN_BG};color:{WARN_TXT}"
        return f"background-color:{BAD_BG};color:{BAD_TXT}"

    def fmt_val(v):
        return fmt_pct(v) if v is not None and not (isinstance(v, float) and np.isnan(v)) else ""

    # Format display copy
    display = tbl.copy()
    for col in sorted_periods + ["Avg"]:
        display[col] = display[col].apply(fmt_val)

    region_filter = st.radio("Filter by region", ["All","ENT","Florida"], horizontal=True)
    if region_filter != "All":
        display = display[display['Region']==region_filter]

    st.dataframe(display, hide_index=True, use_container_width=True, height=600)


# ── Tab: Cohort Analysis ──────────────────────────────────────────────────────

def tab_cohort(df, periods):
    sorted_periods = sorted(periods,
                            key=lambda p: df[df['period_label']==p]['sort_key'].iloc[0])
    all_cohorts = ['Legacy (Pre-Data)'] + sorted(
        [c for c in df['cohort'].unique() if c != 'Legacy (Pre-Data)'])

    max_age = min(int(df['periods_open'].max()), 14)
    ages = list(range(1, max_age+1))

    section("Ramp Curve — Average Net Sales by Cohort Age")
    fig = go.Figure()
    for i, cohort in enumerate(all_cohorts):
        cdf = df[df['cohort']==cohort]
        is_q4 = cohort in Q4_COHORTS
        y_vals = [cdf[cdf['periods_open']==age]['Net Sales'].mean() for age in ages]
        fig.add_scatter(
            x=[f"P+{a}" for a in ages], y=y_vals,
            name=cohort, mode="lines+markers",
            line=dict(
                color=(RED if cohort=='Legacy (Pre-Data)' else
                       WATCH_TXT if is_q4 else PLOTLY_COLORS[i%len(PLOTLY_COLORS)]),
                width=3 if cohort=='Legacy (Pre-Data)' else 1.5,
                dash="solid" if cohort=='Legacy (Pre-Data)' else ("dot" if is_q4 else "solid"),
            ),
            marker=dict(size=6 if cohort=='Legacy (Pre-Data)' else 4),
        )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=CHARCOAL, plot_bgcolor=CHARCOAL,
        yaxis=dict(title="Avg Net Sales ($)", tickformat="$,.0f", gridcolor="#404040"),
        xaxis=dict(title="Periods Since Opening"),
        legend=dict(x=1.01, y=1, bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=0, r=180, t=10, b=0), height=380,
    )
    st.plotly_chart(fig, use_container_width=True)

    section("EBITDA % Ramp Curve by Cohort")
    fig2 = go.Figure()
    for i, cohort in enumerate(all_cohorts):
        cdf = df[df['cohort']==cohort].copy()
        cdf['_ep'] = cdf['Store Level EBITDA'] / cdf['Net Sales'].replace(0, np.nan)
        is_q4 = cohort in Q4_COHORTS
        y_vals = [cdf[cdf['periods_open']==age]['_ep'].mean() for age in ages]
        fig2.add_scatter(
            x=[f"P+{a}" for a in ages], y=y_vals,
            name=cohort, mode="lines+markers",
            line=dict(
                color=(RED if cohort=='Legacy (Pre-Data)' else
                       WATCH_TXT if is_q4 else PLOTLY_COLORS[i%len(PLOTLY_COLORS)]),
                width=3 if cohort=='Legacy (Pre-Data)' else 1.5,
                dash="solid" if cohort=='Legacy (Pre-Data)' else ("dot" if is_q4 else "solid"),
            ),
            marker=dict(size=6 if cohort=='Legacy (Pre-Data)' else 4),
        )

    fig2.add_hline(y=_net_avg_ep or 0, line_dash="dash", line_color=GOOD_TXT,
                   annotation_text=f"Network Avg {fmt_pct(_net_avg_ep)} (Mature)")
    fig2.add_hline(y=_q4_avg_ep or 0, line_dash="dot",  line_color=WATCH_TXT,
                   annotation_text=f"Q4 Class Avg {fmt_pct(_q4_avg_ep)}")
    fig2.update_layout(
        template="plotly_dark",
        paper_bgcolor=CHARCOAL, plot_bgcolor=CHARCOAL,
        yaxis=dict(title="Avg EBITDA %", tickformat=".0%", gridcolor="#404040"),
        xaxis=dict(title="Periods Since Opening"),
        legend=dict(x=1.01, y=1, bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=0, r=180, t=10, b=0), height=340,
    )
    st.plotly_chart(fig2, use_container_width=True)

    # Table
    section("Cohort Summary Table")
    last_period = sorted_periods[-1]
    ldf = df[df['period_label']==last_period]
    rows = []
    for cohort in all_cohorts:
        cdf = ldf[ldf['cohort']==cohort]
        if cdf.empty: continue
        ep_vals = cdf['Store Level EBITDA'] / cdf['Net Sales'].replace(0, np.nan)
        rows.append({
            "Cohort": cohort,
            "Stands": cdf['stand_id'].nunique(),
            "Avg Net Sales": fmt_dollar(cdf['Net Sales'].mean()),
            "Avg EBITDA %": fmt_pct(ep_vals.mean()),
            "Avg COGS %": fmt_pct((cdf['COGS']/cdf['Net Sales'].replace(0,np.nan)).mean()),
            "Avg Labor %": fmt_pct((cdf['Total Labor & Benefits']/cdf['Net Sales'].replace(0,np.nan)).mean()),
            "Ramp Stands": int(cdf['is_ramp'].sum()),
            "Q4 Watch": "🔵 Yes" if cohort in Q4_COHORTS else "",
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


# ── Tab: Revenue Trend ────────────────────────────────────────────────────────

def tab_revenue(df, periods):
    sorted_periods = sorted(periods,
                            key=lambda p: df[df['period_label']==p]['sort_key'].iloc[0])
    section("Net Sales by Stand × Period")

    stands = (df.drop_duplicates('stand_id')[['stand_id','display_name','region','cohort']]
              .join(df.groupby('stand_id')['Net Sales'].sum().rename('_ns'), on='stand_id')
              .sort_values(['region','_ns'], ascending=[True, False]))

    rows = []
    for _, sr in stands.iterrows():
        sdf = df[df['stand_id']==sr['stand_id']]
        ns_map = sdf.set_index('period_label')['Net Sales'].to_dict()
        row = {"Stand": sr['display_name'], "Region": sr['region'], "Cohort": sr['cohort']}
        for p in sorted_periods:
            row[p] = ns_map.get(p)
        row["Total"] = sum(v for v in ns_map.values())
        row["Periods"] = len(ns_map)
        rows.append(row)

    tbl = pd.DataFrame(rows)

    region_filter = st.radio("Filter by region", ["All","ENT","Florida"], horizontal=True, key="rev_region")
    if region_filter != "All":
        tbl = tbl[tbl['Region']==region_filter]

    # Format money columns
    for col in sorted_periods + ["Total"]:
        tbl[col] = tbl[col].apply(lambda x: fmt_dollar(x) if x else "")

    st.dataframe(tbl, hide_index=True, use_container_width=True, height=600)

    section("Top 10 Stands by Total Revenue (All Periods)")
    top = (df.groupby(['stand_id','display_name','region','cohort'])['Net Sales']
             .sum().reset_index()
             .nlargest(10,'Net Sales')
             .rename(columns={'display_name':'Stand','region':'Region',
                               'cohort':'Cohort','Net Sales':'Total Net Sales'}))
    top['Total Net Sales'] = top['Total Net Sales'].apply(fmt_dollar)
    top.drop(columns='stand_id', inplace=True)
    st.dataframe(top, hide_index=True, use_container_width=True)


# ── Tab: Stand Directory ──────────────────────────────────────────────────────

def tab_directory(df, periods):
    sorted_periods = sorted(periods,
                            key=lambda p: df[df['period_label']==p]['sort_key'].iloc[0])
    last_period = sorted_periods[-1]
    ldf = df[df['period_label']==last_period].set_index('stand_id')
    per_cnt = df.groupby('stand_id')['period_label'].nunique().to_dict()

    rows = []
    stand_info = df.sort_values('sort_key').drop_duplicates('stand_id')
    for _, r in stand_info.sort_values(['region','cohort','display_name']).iterrows():
        sid = r['stand_id']
        is_q4 = r['cohort'] in Q4_COHORTS
        is_ramp = ldf.loc[sid,'is_ramp'] if sid in ldf.index else False
        last_ns  = ldf.loc[sid,'Net Sales'] if sid in ldf.index else None
        last_ebt = ldf.loc[sid,'Store Level EBITDA'] if sid in ldf.index else None
        ep = safe_pct(last_ebt, last_ns) if last_ns else None

        rows.append({
            "Stand ID": sid,
            "Stand": r['display_name'],
            "City": r['city'],
            "State": r['state'],
            "Region": r['region'],
            "Cohort": r['cohort'],
            "First Period": r['period_label'],
            "Periods Active": per_cnt.get(sid, 0),
            "Latest Sales": fmt_dollar(last_ns),
            "Latest EBITDA %": fmt_pct(ep),
            "Status": ("⚡ Ramp" if is_ramp else "🔵 Q4 Watch" if is_q4 else "Mature"),
        })

    tbl = pd.DataFrame(rows)

    c1, c2, c3 = st.columns(3)
    r_filter = c1.selectbox("Region", ["All","ENT","Florida"])
    c_filter = c2.selectbox("Cohort", ["All"] + sorted(df['cohort'].unique()))
    s_filter = c3.selectbox("Status", ["All","Mature","⚡ Ramp","🔵 Q4 Watch"])

    if r_filter != "All": tbl = tbl[tbl["Region"]==r_filter]
    if c_filter != "All": tbl = tbl[tbl["Cohort"]==c_filter]
    if s_filter != "All": tbl = tbl[tbl["Status"]==s_filter]

    st.dataframe(tbl, hide_index=True, use_container_width=True)
    st.caption(f"Showing {len(tbl)} of {len(rows)} stands")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Check data folder
    files = sorted(glob.glob(str(DATA_DIR / "7BREW Income Statement Side By Side PTD All*.xlsx")))

    if not files:
        # Render sidebar with uploader even when no data exists
        with st.sidebar:
            logo_path = Path(__file__).parent / "assets" / "logo.png"
            if logo_path.exists():
                st.image(str(logo_path), width=180)
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
        f'Viewing: {selected_period}  |  '
        f'{ldf["stand_id"].nunique()} stands in current view</p>'
        f'</div>', unsafe_allow_html=True)

    # Tabs
    tabs = st.tabs([
        "📊 CEO Summary",
        "⚙️ COO Scorecard",
        "🔍 Q4 Class Watch",
        "📈 EBITDA Trend",
        "🏗️ Cohort Analysis",
        "💰 Revenue Trend",
        "📋 Stand Directory",
    ])

    with tabs[0]: tab_ceo(df, ldf, periods, selected_period)
    with tabs[1]: tab_coo(df, ldf, periods, selected_period)
    with tabs[2]: tab_q4(df, ldf, periods, selected_period)
    with tabs[3]: tab_ebitda(df, periods)
    with tabs[4]: tab_cohort(df, periods)
    with tabs[5]: tab_revenue(df, periods)
    with tabs[6]: tab_directory(df, periods)


if __name__ == "__main__":
    main()
