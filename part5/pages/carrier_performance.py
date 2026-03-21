from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from part5.dashboard_features.carrier_performance_features import (
    get_all_carriers,
    get_carrier_overview_df,
    get_carrier_kpis,
    get_carrier_status_breakdown_df,
    get_carrier_avg_delay_df,
    get_carrier_monthly_trend_df,
    get_carrier_airport_share_df,
    get_carrier_delay_buckets_df,
)

st.set_page_config(
    page_title="Airline Carrier Performance",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Colour palette
# ─────────────────────────────────────────────

PRIMARY = "#0f172a"
BLUE_DARK = "#2167b6"
BLUE_MAIN = "#3aa2ed"
BLUE_MID = "#8bc2fa"
BLUE_LIGHT = "#b5d2fd"
BLUE_PALE = "#f5f8ff"
TEXT_MID = "#4b5563"
TEXT_LIGHT = "#6b7280"
BG = "#f5f5f5"
CARD_BORDER = "#e5e7eb"
JFK_COLOR = "#ffa856"
EWR_COLOR = "#83eaff"
LGA_COLOR = "#8799ff"

CARRIER_PALETTE = [
    "#7c3aed", "#1794ce", "#11922b", "#f59e0b",
    "#ef4444", "#b93535", "#ffed29", "#84cc16",
    "#f97316", "#ec4899", "#2bf7df", "#6366f1",
    "#c689ff", "#22d3ee",
]

carrier_color_map = {
    name: CARRIER_PALETTE[i % len(CARRIER_PALETTE)]
    for i, name in enumerate(get_all_carriers()["name"])
}

PLOT_CONFIG = {"displayModeBar": False, "responsive": True}

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown(
    f"""
    <style>
        .stApp {{
            background-color: {BG};
        }}

        .block-container {{
            padding-top: 2rem;
            padding-bottom: 3.2rem;
            max-width: 1320px;
        }}

        h1, h2, h3 {{
            color: {PRIMARY} !important;
        }}

        .intro-box {{
            background: #ffffff;
            padding: 1.45rem 1.7rem;
            border-radius: 16px;
            border: 1px solid {CARD_BORDER};
            box-shadow: 0 4px 18px rgba(91, 33, 182, 0.10);
            margin-bottom: 1.6rem;
        }}

        .intro-title {{
            font-size: 1.15rem;
            font-weight: 700;
            color: {PRIMARY};
            margin-bottom: 0.35rem;
        }}

        .intro-text {{
            font-size: 1rem;
            color: #374151;
            line-height: 1.7;
        }}

        .filter-row {{
            margin-top: 0.85rem;
            display: flex;
            gap: 0.6rem;
            flex-wrap: wrap;
        }}

        .intro-note {{
            display: inline-block;
            background: {BLUE_MAIN};
            color: #ffffff;
            padding: 0.42rem 0.78rem;
            border-radius: 999px;
            font-size: 0.88rem;
            font-weight: 600;
        }}

        .intro-note-secondary {{
            display: inline-block;
            background: #e5e7eb;
            color: #374151;
            padding: 0.42rem 0.78rem;
            border-radius: 999px;
            font-size: 0.88rem;
            font-weight: 600;
        }}

        .section-box {{
            background: #ffffff;
            border: 1px solid {CARD_BORDER};
            border-top: 4px solid {BLUE_MAIN};
            border-radius: 14px;
            padding: 1.4rem 1.4rem 1.15rem 1.4rem;
            box-shadow: 0 4px 24px rgba(91, 33, 182, 0.08);
            margin-top: 0.5rem;
            margin-bottom: 2.05rem;
        }}

        .section-title {{
            font-size: 1.48rem;
            font-weight: 750;
            color: {PRIMARY};
            margin-bottom: 0.25rem;
        }}

        .section-subtitle {{
            color: {TEXT_MID};
            font-size: 0.98rem;
            margin-bottom: 1.15rem;
            line-height: 1.6;
        }}

        .kpi-card {{
            background: #ffffff;
            border: 1px solid {CARD_BORDER};
            border-radius: 16px;
            padding: 1.2rem 1.25rem 1.05rem 1.25rem;
            box-shadow: 0 4px 20px rgba(91, 33, 182, 0.10);
            min-height: 160px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            margin-bottom: 1.15rem;
        }}

        .kpi-label {{
            font-size: 0.98rem;
            color: {TEXT_MID};
            margin-bottom: 0.7rem;
            line-height: 1.45;
            font-weight: 650;
        }}

        .kpi-value {{
            font-size: 2.8rem;
            font-weight: 800;
            color: {PRIMARY};
            line-height: 1.0;
            margin-bottom: 0.45rem;
            letter-spacing: -0.02em;
        }}

        .kpi-footnote {{
            font-size: 0.86rem;
            color: {TEXT_LIGHT};
            line-height: 1.45;
        }}

        .insight-box {{
            background: #ffffff;
            border-left: 4px solid {BLUE_DARK};
            padding: 0.95rem 1.05rem;
            border-radius: 10px;
            color: {PRIMARY};
            margin-top: 0.95rem;
            margin-bottom: 0.55rem;
            line-height: 1.65;
        }}

        section[data-testid="stSidebar"] {{
            background: #ffffff !important;
            border-right: 1px solid {CARD_BORDER};
        }}

        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {{
            color: #111827;
        }}

        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p {{
            color: #111827 !important;
            font-weight: 500;
        }}

        [data-testid="stSidebarNavLink"] p,
        [data-testid="stSidebarNavLink"] span,
        section[data-testid="stSidebar"] nav a p,
        section[data-testid="stSidebar"] nav a span {{
            color: #111827 !important;
            font-weight: 600;
        }}

        div[data-testid="stDataFrame"] {{
            border-radius: 12px;
            overflow: hidden;
        }}

        div[data-testid="stAlert"] p {{
            color: #111827 !important;
            font-weight: 500;
        }}

        section[data-testid="stSidebar"] [data-baseweb="tag"] {{
            background-color: #16a34a !important;
            border-color: #15803d !important;
        }}

        section[data-testid="stSidebar"] [data-baseweb="tag"] span {{
            color: #ffffff !important;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def style_fig(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        font=dict(color="#000000", size=13),
        title=dict(
            x=0.01,
            y=0.98,
            xanchor="left",
            yanchor="top"
        ),
        title_font=dict(size=15, color="#000000"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=10, t=120, b=20),
        legend=dict(
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor=CARD_BORDER,
            borderwidth=1,
        ),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#f3f4f6", linecolor="#e5e7eb")
    fig.update_yaxes(showgrid=True, gridcolor="#f3f4f6", linecolor="#e5e7eb")
    return fig


def kpi_card(label: str, value: str, footnote: str = "") -> str:
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-footnote">{footnote}</div>
    </div>
    """


def section_open(title: str, subtitle: str = ""):
    st.markdown(
        f"""
        <div class="section-box">
            <div class="section-title">{title}</div>
            {"<div class='section-subtitle'>" + subtitle + "</div>" if subtitle else ""}
        """,
        unsafe_allow_html=True,
    )

def section_close():
    st.markdown("</div>", unsafe_allow_html=True)

def format_filter_context(selected_carriers, origin):
    airport_text = "all airports" if origin == "All" else origin
    return (
        f"Current view: {len(selected_carriers)} airline"
        f"{'s' if len(selected_carriers) != 1 else ''} selected · {airport_text}"
    )


# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────

with st.sidebar:
    st.markdown("### Filters")

    all_carriers_df = get_all_carriers()
    carrier_options = all_carriers_df["name"].tolist()
    carrier_code_map = dict(zip(all_carriers_df["name"], all_carriers_df["carrier"]))

    selected_name = st.selectbox(
        "Airlines",
        options=["All airlines"] + carrier_options,
        index=0,
        help="Select one airline to compare, or choose All airlines.",
    )

    if selected_name == "All airlines":
        selected_carriers = all_carriers_df["carrier"].tolist()
    else:
        selected_carriers = [carrier_code_map[selected_name]]

    origin = st.selectbox(
        "Departure airport",
        options=["All", "EWR", "JFK", "LGA"],
        index=0,
    )

# ─────────────────────────────────────────────
# Guard — no airlines selected
# ─────────────────────────────────────────────

if not selected_carriers:
    st.warning("Please select at least one airline from the sidebar.")
    st.stop()

# ─────────────────────────────────────────────
# Page header
# ─────────────────────────────────────────────

st.markdown("<h1 style='margin-bottom:0.2rem;'>NYC Flights Dashboard</h1>", unsafe_allow_html=True)
st.markdown(
    f"""
    <div class="intro-box">
        <div class="intro-title">Airline Carrier Performance</div>
        <div class="intro-text">
            Compare all NYC-area carriers across on-time performance, average delays,
            cancellation rates, and monthly reliability. Use the sidebar to narrow down
            to specific airlines or a single departure airport.
        </div>
        <div class="filter-row">
            <div class="intro-note">{format_filter_context(selected_carriers, origin)}</div>
            <div class="intro-note-secondary">Interactive filters: airlines, departure airport</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# KPI row
# ─────────────────────────────────────────────

kpis = get_carrier_kpis(selected_carriers, origin)

total = int(kpis.get("total_flights", 0))
on_time = kpis.get("on_time_pct", 0) or 0
avg_dep = kpis.get("avg_dep_delay", 0) or 0
canc = kpis.get("cancellation_pct", 0) or 0

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(kpi_card("Total Flights", f"{total:,}", "across selected airlines & airport"), unsafe_allow_html=True)
with k2:
    st.markdown(kpi_card("On-Time Rate", f"{on_time:.1f}%", "departure delay ≤ 15 min"), unsafe_allow_html=True)
with k3:
    st.markdown(kpi_card("Avg Departure Delay", f"{avg_dep:.0f} min", "when delayed (dep delay > 0)"), unsafe_allow_html=True)
with k4:
    st.markdown(kpi_card("Cancellation Rate", f"{canc:.2f}%", "% of flights cancelled"), unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Section 1 — Scorecard table
# ─────────────────────────────────────────────

section_open(
    "Carrier Scorecard",
    "Ranked overview of every selected airline — total flights, on-time rate, average delays, and cancellation rate."
)

overview_df = get_carrier_overview_df()
overview_df = overview_df[overview_df["carrier"].isin(selected_carriers)]

scorecard = overview_df[[
    "airline", "carrier", "total_flights", "on_time_pct",
    "avg_dep_delay", "avg_arr_delay", "cancellation_pct"
]].copy()
scorecard = scorecard.sort_values("on_time_pct", ascending=False).reset_index(drop=True)
scorecard.index += 1
scorecard.columns = [
    "Airline", "Code", "Total Flights", "On-Time %",
    "Avg Dep Delay (min)", "Avg Arr Delay (min)", "Cancellation %"
]

st.dataframe(
    scorecard.style
        .background_gradient(subset=["On-Time %"], cmap="RdYlGn", vmin=50, vmax=90)
        .background_gradient(subset=["Cancellation %"], cmap="RdYlGn_r", vmin=0, vmax=5)
        .format({
            "Total Flights": "{:,}",
            "On-Time %": "{:.1f}%",
            "Avg Dep Delay (min)": "{:.1f}",
            "Avg Arr Delay (min)": "{:.1f}",
            "Cancellation %": "{:.2f}%",
        }),
    use_container_width=True,
    height=min(60 + len(scorecard) * 38, 520),
)

best_ontime = scorecard.iloc[0]["Airline"]
worst_cancel = scorecard.sort_values("Cancellation %", ascending=False).iloc[0]["Airline"]

st.markdown(
    f"""<div class="insight-box">
        <strong>{best_ontime}</strong> ranks #1 for on-time departures among selected carriers.
        &nbsp;|&nbsp; <strong>{worst_cancel}</strong> has the highest cancellation rate.
    </div>""",
    unsafe_allow_html=True,
)
section_close()

# ─────────────────────────────────────────────
# Section 2 — Flight status breakdown
# ─────────────────────────────────────────────

section_open(
    "Flight Status Breakdown",
    "Each bar shows how a carrier's flights split across four outcomes: on-time, slightly late (1–15 min), delayed (>15 min), and cancelled.")

status_df = get_carrier_status_breakdown_df(selected_carriers, origin)

if not status_df.empty:
    fig_status = go.Figure()

    statuses = [
        ("on_time_pct", "On-Time (≤ 0 min)", BLUE_LIGHT),
        ("slightly_late_pct", "Slightly Late (1–15 min)", BLUE_MID),
        ("delayed_pct", "Delayed (> 15 min)", BLUE_DARK),
        ("cancelled_pct", "Cancelled", TEXT_MID),
    ]

    for col, label, colour in statuses:
        fig_status.add_trace(go.Bar(
            name=label,
            x=status_df["airline"],
            y=status_df[col],
            marker_color=colour,
            text=status_df[col].map(lambda v: f"{v:.1f}%"),
            textposition="inside",
            insidetextanchor="middle",
        ))

    fig_status.update_layout(
        title="Flight Status Distribution by Airline",
        barmode="stack",
        xaxis_title="Airline",
        yaxis_title="% of Flights",
        yaxis=dict(range=[0, 100], ticksuffix="%"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=420,
    )
    st.plotly_chart(style_fig(fig_status), use_container_width=True, config=PLOT_CONFIG)

    top_ontime = status_df.sort_values("on_time_pct", ascending=False).iloc[0]
    st.markdown(
        f"""<div class="insight-box">
             <strong>{top_ontime['airline']}</strong> has the best on-time rate at
            <strong>{top_ontime['on_time_pct']:.1f}%</strong> of flights departing on time or early.
        </div>""",
        unsafe_allow_html=True,
    )
section_close()
st.divider()

# ─────────────────────────────────────────────
# Section 3 — Average departure vs arrival delay
# ─────────────────────────────────────────────

section_open("Average Delay by Carrier",
             "When flights are delayed, how long do passengers actually wait? Compares average departure and arrival delay per airline.")

delay_df = get_carrier_avg_delay_df(selected_carriers, origin)

if not delay_df.empty:
    fig_delay = go.Figure()
    fig_delay.add_trace(go.Bar(
        name="Avg Dep Delay",
        x=delay_df["airline"],
        y=delay_df["avg_dep_delay"],
        marker_color=BLUE_MAIN,
        text=delay_df["avg_dep_delay"].map(lambda v: f"{v:.0f}m" if pd.notna(v) else "N/A"),
        textposition="outside",
    ))
    fig_delay.add_trace(go.Bar(
        name="Avg Arr Delay",
        x=delay_df["airline"],
        y=delay_df["avg_arr_delay"],
        marker_color=BLUE_MID,
        text=delay_df["avg_arr_delay"].map(lambda v: f"{v:.0f}m" if pd.notna(v) else "N/A"),
        textposition="outside",
    ))
    fig_delay.update_layout(
        title="Average Departure vs Arrival Delay by Airline",
        barmode="group",
        xaxis_title="Airline",
        yaxis_title="Average Delay (minutes)",
        yaxis=dict(range=[0, delay_df[["avg_dep_delay", "avg_arr_delay"]].max().max() * 1.25]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=420,
    )
    st.plotly_chart(style_fig(fig_delay), use_container_width=True, config=PLOT_CONFIG)

    worst_dep = delay_df.dropna(subset=["avg_dep_delay"]).sort_values("avg_dep_delay", ascending=False).iloc[0]
    best_dep = delay_df.dropna(subset=["avg_dep_delay"]).sort_values("avg_dep_delay").iloc[0]
    st.markdown(
        f"""<div class="insight-box">
             <strong>{worst_dep['airline']}</strong> has the longest average departure delay
            (<strong>{worst_dep['avg_dep_delay']:.0f} min</strong>), while
            <strong>{best_dep['airline']}</strong> recovers quickest
            (<strong>{best_dep['avg_dep_delay']:.0f} min</strong>).
        </div>""",
        unsafe_allow_html=True,
    )
section_close()


# ─────────────────────────────────────────────
# Section 4 — Monthly on-time trend
# ─────────────────────────────────────────────

section_open("Monthly On-Time Rate",
            "How each carrier's reliability shifts across the year — spot seasonal dips, summer slowdowns, and winter disruptions.")

trend_df = get_carrier_monthly_trend_df(selected_carriers, origin)

MONTH_ORDER = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

if not trend_df.empty:
    trend_df["month_label"] = pd.Categorical(trend_df["month_label"], categories=MONTH_ORDER, ordered=True)
    trend_df = trend_df.sort_values(["carrier", "month_label"])

    fig_trend = px.line(
        trend_df,
        x="month_label",
        y="on_time_pct",
        color="airline",
        markers=True,
        title="Monthly On-Time Rate by Airline",
        labels={"month_label": "Month", "on_time_pct": "On-Time Rate (%)", "airline": "Airline"},
        color_discrete_map=carrier_color_map,
        category_orders={"month_label": MONTH_ORDER},
    )
    fig_trend.update_traces(line_width=2.2, marker_size=6)
    fig_trend.update_layout(
        yaxis=dict(ticksuffix="%"),
        xaxis_title="Month",
        yaxis_title="On-Time Rate (%)",
        legend=dict(orientation="h", yanchor="bottom", y=0.99, xanchor="center", x=0.5),
        height=480,
    )
    st.plotly_chart(style_fig(fig_trend), use_container_width=True, config=PLOT_CONFIG)

    monthly_avg = trend_df.groupby("month_label")["on_time_pct"].mean().reindex(MONTH_ORDER)
    worst_month = monthly_avg.idxmin()
    best_month = monthly_avg.idxmax()
    st.info(
        f" On-time performance drops most sharply in **{worst_month}** across the selected carriers "
        f"— likely due to weather or peak travel demand. Best overall reliability: **{best_month}**."
    )

section_close()


# ─────────────────────────────────────────────
# Section 5 — Delay bucket distribution
# ─────────────────────────────────────────────

section_open("Delay Severity Heatmap",
             "How delay lengths are distributed across carriers — from on-time/early through short, medium, and long delays (60+ min). Darker = more flights.")

bucket_df = get_carrier_delay_buckets_df(selected_carriers, origin)

if not bucket_df.empty:
    bucket_cols = {
        "on_time_or_early": "Early / On-Time",
        "delay_1_15": "1–15 min",
        "delay_16_30": "16–30 min",
        "delay_31_60": "31–60 min",
        "delay_over_60": "60+ min",
    }

    bucket_df["total"] = bucket_df[list(bucket_cols.keys())].sum(axis=1)
    for col, label in bucket_cols.items():
        bucket_df[label] = (bucket_df[col] / bucket_df["total"] * 100).round(1)
    heat_matrix = bucket_df.set_index("airline")[list(bucket_cols.values())]

    fig_heat = go.Figure(data=go.Heatmap(
        z=heat_matrix.values,
        x=heat_matrix.columns.tolist(),
        y=heat_matrix.index.tolist(),
        colorscale=[
            [0.0, "#6cc45d"],
            [0.3, "#ffeb79"],
            [0.6, "#ff934c"],
            [1.0, "#E82A2A"],
        ],
        text=[[f"{v:.1f}%" for v in row] for row in heat_matrix.values],
        texttemplate="%{text}",
        textfont=dict(size=12, color="white"),
        hoverongaps=False,
        colorbar=dict(title="% of Flights", ticksuffix="%"),
    ))
    fig_heat.update_layout(
        title="Delay Severity Distribution Across Airlines",
        xaxis_title="Delay Bucket",
        yaxis_title="Airline",
        yaxis=dict(autorange="reversed"),
        margin=dict(l=10, r=10, t=40, b=40),
        font=dict(color="#000000", size=13),
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=max(300, len(heat_matrix) * 46 + 80),
    )
    st.plotly_chart(fig_heat, use_container_width=True, config=PLOT_CONFIG)

    most_severe = bucket_df.set_index("airline")["60+ min"].idxmax()
    st.info(
        f" **{most_severe}** has the highest share of very long delays (60+ min) among selected carriers "
        "— passengers on this airline face the longest waits when things go wrong."
    )

section_close()


# ─────────────────────────────────────────────
# Section 6 — Airport dominance
# ─────────────────────────────────────────────

section_open("Airport Dominance",
             "Which airlines dominate EWR, JFK, and LGA? Each bar shows the share of flights operated from each NYC airport by carrier.")

airport_df = get_carrier_airport_share_df(selected_carriers)

if not airport_df.empty:
    fig_airport = px.bar(
        airport_df,
        x="origin",
        y="total_flights",
        color="airline",
        barmode="group",
        labels={"origin": "Airport", "total_flights": "Total Flights", "airline": "Airline"},
        color_discrete_map=carrier_color_map,
        text="total_flights",
    )
    fig_airport.update_traces(texttemplate="%{text:,}", textposition="outside", cliponaxis=False)
    fig_airport.update_layout(
        title="Airline Flight Volume by NYC Airport",
        xaxis_title="NYC Airport",
        yaxis_title="Total Flights",
        yaxis=dict(range=[0, airport_df["total_flights"].max() * 1.2]),
        legend=dict(orientation="h", yanchor="bottom", y=0.99, xanchor="center", x=0.5),
        height=520,
    )
    st.plotly_chart(style_fig(fig_airport), use_container_width=True, config=PLOT_CONFIG)

    insights = []
    for apt in ["EWR", "JFK", "LGA"]:
        apt_data = airport_df[airport_df["origin"] == apt]
        if not apt_data.empty:
            top = apt_data.sort_values("total_flights", ascending=False).iloc[0]
            insights.append(
                f"**{apt}**: **{top['airline']}** is the dominant carrier with **{int(top['total_flights']):,}** flights."
            )
    if insights:
        st.info("  \n".join(insights))

section_close()