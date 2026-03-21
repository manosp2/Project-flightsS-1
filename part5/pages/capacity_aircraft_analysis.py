from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import plotly.express as px

from part5.dashboard_features.aircraft_capacity_features import (
    MONTH_LABELS,
    MONTH_TO_NUM,
    get_destinations,
    get_capacity_kpis,
    get_airport_capacity_df,
    get_airline_capacity_df,
    get_route_capacity_df,
    get_monthly_capacity_df,
    get_capacity_conclusion_text,
)

st.set_page_config(
    page_title="Passenger Capacity & Fleet Utilization",
    layout="wide",
    initial_sidebar_state="expanded",
)

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

PLOT_CONFIG = {"displayModeBar": False, "responsive": True}

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
            margin-bottom: 1.7rem;
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
            box-shadow: 0 4px 24px rgba(31, 42, 68, 0.12);
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
            min-height: 165px;
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
    </style>
    """,
    unsafe_allow_html=True,
)

@st.cache_data
def get_destinations_cached():
    return get_destinations()

@st.cache_data
def get_capacity_kpis_cached(origins, months, dest_filter):
    return get_capacity_kpis(list(origins), list(months), dest_filter)

@st.cache_data
def get_airport_capacity_df_cached(months, dest_filter):
    return get_airport_capacity_df(list(months), dest_filter)

@st.cache_data
def get_airline_capacity_df_cached(origins, months, dest_filter, min_flights):
    return get_airline_capacity_df(list(origins), list(months), dest_filter, min_flights=min_flights)

@st.cache_data
def get_route_capacity_df_cached(origins, months, dest_filter, top_n):
    return get_route_capacity_df(list(origins), list(months), dest_filter, top_n=top_n)

@st.cache_data
def get_monthly_capacity_df_cached(origins, dest_filter):
    return get_monthly_capacity_df(list(origins), dest_filter)

def section_open(title, subtitle=""):
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

def kpi_card(label, value, footnote=""):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div>
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
            </div>
            <div class="kpi-footnote">{footnote}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def insight_box(text):
    st.markdown(f"<div class='insight-box'>{text}</div>", unsafe_allow_html=True)

def style_fig(fig, height=420, showlegend=False):
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(t=65, l=20, r=20, b=20),
        height=height,
        showlegend=showlegend,
        font=dict(color=PRIMARY, size=14),
        title_font=dict(size=16, color=PRIMARY),
        title_x=0.03,
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="#edf2f7", zeroline=False)
    return fig

def show_fig(fig, use_container_width=True):
    st.plotly_chart(fig, use_container_width=use_container_width, config=PLOT_CONFIG)

def format_filter_context(origins, dest_filter, months):
    origin_text = "all NYC departure airports" if len(origins) == 3 else origins[0]
    dest_text = "all destinations" if dest_filter is None else dest_filter

    if len(months) == 12:
        month_text = "the full year"
    else:
        month_names = [MONTH_LABELS[m - 1] for m in months]
        month_text = ", ".join(month_names) if len(month_names) <= 3 else f"{len(month_names)} selected months"

    return f"Current view: {origin_text} → {dest_text}, filtered to {month_text}."

st.title("NYC Flights Dashboard")

st.sidebar.header("Filters")

origin_choice = st.sidebar.selectbox(
    "Departure airport",
    ["All NYC", "JFK", "LGA", "EWR"],
    index=0,
)
origins = ("JFK", "LGA", "EWR") if origin_choice == "All NYC" else (origin_choice,)

destinations = get_destinations_cached()
dest_choice = st.sidebar.selectbox(
    "Arrival airport",
    ["All destinations"] + destinations,
)
dest_filter = None if dest_choice == "All destinations" else dest_choice

preset = st.sidebar.selectbox(
    "Month preset",
    [
        "All months",
        "Q1 (Jan–Mar)",
        "Q2 (Apr–Jun)",
        "Q3 (Jul–Sep)",
        "Q4 (Oct–Dec)",
        "Q1 + Q2 (Jan–Jun)",
        "Q3 + Q4 (Jul–Dec)",
        "Custom",
    ],
    index=0,
    key="month_preset_capacity",
)

if preset == "All months":
    selected_months = MONTH_LABELS
elif preset == "Q1 (Jan–Mar)":
    selected_months = ["Jan", "Feb", "Mar"]
elif preset == "Q2 (Apr–Jun)":
    selected_months = ["Apr", "May", "Jun"]
elif preset == "Q3 (Jul–Sep)":
    selected_months = ["Jul", "Aug", "Sep"]
elif preset == "Q4 (Oct–Dec)":
    selected_months = ["Oct", "Nov", "Dec"]
elif preset == "Q1 + Q2 (Jan–Jun)":
    selected_months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
elif preset == "Q3 + Q4 (Jul–Dec)":
    selected_months = ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
else:
    selected_months = st.sidebar.multiselect(
        "Select months",
        MONTH_LABELS,
        default=MONTH_LABELS,
    )

months = tuple(MONTH_TO_NUM[m] for m in selected_months)
if not months:
    st.warning("Select at least one month.")
    st.stop()

min_airline_flights = st.sidebar.slider(
    "Minimum flights per airline",
    min_value=25,
    max_value=500,
    value=100,
    step=25,
)

filter_context = format_filter_context(origins, dest_filter, months)

st.markdown(
    f"""
    <div class="intro-box">
        <div class="intro-title">Passenger Capacity & Fleet Utilization</div>
        <div class="intro-text">
            Aircraft seat capacity provides an estimate of how many passengers can move through NYC airports.
            This page compares passenger capacity across airports, airlines, and routes to highlight where larger aircraft
            operate and where the highest potential passenger throughput is concentrated.
        </div>
        <div class="filter-row">
            <div class="intro-note">{filter_context}</div>
            <div class="intro-note-secondary">Interactive filters: departure airport, arrival airport, month preset, minimum flights per airline</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

section_open(
    "Capacity Overview",
    "These metrics summarize the estimated passenger capacity represented in the current filtered sample."
)

kpis = get_capacity_kpis_cached(origins, months, dest_filter)

if kpis["flights"] == 0:
    st.info("No aircraft capacity data is available for the selected filters.")
    st.stop()

c1, c2, c3, c4 = st.columns(4, gap="large")
with c1:
    kpi_card("Flights matched to aircraft", f"{kpis['flights']:,}", "Flights linked to plane records")
with c2:
    kpi_card("Average seats", f"{kpis['avg_seats']:.1f}", "Average aircraft size")
with c3:
    kpi_card("Estimated seat capacity", f"{kpis['est_passenger_capacity']:,}", "Seats used as passenger proxy")
with c4:
    kpi_card("Airlines / destinations", f"{kpis['airlines']} / {kpis['destinations']}", "Coverage in current view")

insight_box(get_capacity_conclusion_text(kpis))
section_close()

section_open(
    "Total Seat Capacity by NYC Airport",
    "This chart estimates how much passenger capacity is handled by each NYC airport."
)

airport_df = get_airport_capacity_df_cached(months, dest_filter)

if airport_df.empty:
    st.info("No airport capacity data is available for the selected filters.")
else:
    fig_airport = px.bar(
        airport_df,
        x="origin",
        y="est_passenger_capacity",
        color="origin",
        title="Total seat capacity handled by each NYC airport",
        labels={"origin": "Airport", "est_passenger_capacity": "Estimated passenger capacity"},
        color_discrete_map={"JFK": JFK_COLOR, "LGA": LGA_COLOR, "EWR": EWR_COLOR},
        text="est_passenger_capacity",
    )
    fig_airport.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    style_fig(fig_airport, height=420, showlegend=False)
    show_fig(fig_airport)

    top_airport = airport_df.iloc[0]
    insight_box(
        f"<b>{top_airport['origin']}</b> handles the largest estimated seat capacity in the selected view, "
        f"with about <b>{int(top_airport['est_passenger_capacity']):,}</b> seats. This suggests higher potential passenger throughput than the other NYC airports."
    )

section_close()

section_open(
    "Average Aircraft Size by Airline",
    "This section compares how airlines differ in average aircraft size and total capacity moved through the selected network."
)

airline_df = get_airline_capacity_df_cached(origins, months, dest_filter, min_airline_flights)

if airline_df.empty:
    st.info("No airline capacity data is available for the selected filters.")
else:
    left, right = st.columns([1.05, 1], gap="large")

    with left:
        display_airline = airline_df.rename(
            columns={
                "airline": "Airline",
                "flights": "Flights",
                "avg_seats": "Avg seats",
                "est_passenger_capacity": "Estimated seat capacity",
            }
        ).copy()
        display_airline["Flights"] = display_airline["Flights"].map(lambda x: f"{int(x):,}")
        display_airline["Avg seats"] = display_airline["Avg seats"].map(lambda x: f"{float(x):.1f}")
        display_airline["Estimated seat capacity"] = display_airline["Estimated seat capacity"].map(lambda x: f"{int(x):,}")
        st.dataframe(display_airline, use_container_width=True, hide_index=True, height=420)

    with right:
        fig_airline = px.bar(
            airline_df.sort_values("avg_seats", ascending=True),
            x="avg_seats",
            y="airline",
            orientation="h",
            title="Average aircraft size by airline",
            labels={"avg_seats": "Average seats", "airline": ""},
            color_discrete_sequence=[BLUE_DARK],
        )
        style_fig(fig_airline, height=420, showlegend=False)
        fig_airline.update_layout(coloraxis_showscale=False)
        show_fig(fig_airline)

    top_airline = airline_df.sort_values("avg_seats", ascending=False).iloc[0]
    insight_box(
        f"<b>{top_airline['airline']}</b> operates the largest aircraft on average in the selected sample, "
        f"with about <b>{top_airline['avg_seats']:.1f}</b> seats per flight. Larger aircraft can create higher passenger throughput and different gate and terminal demand."
    )

section_close()

section_open(
    "Routes Carrying the Most Passenger Capacity",
    "These routes contribute the most total seat capacity and highlight the main passenger corridors in the selected network."
)

routes_df = get_route_capacity_df_cached(origins, months, dest_filter, top_n=10)

if routes_df.empty:
    st.info("No route capacity data is available for the selected filters.")
else:
    left, right = st.columns([1.05, 1], gap="large")

    with left:
        display_routes = routes_df[["route", "flights", "avg_seats", "est_passenger_capacity"]].rename(
            columns={
                "route": "Route",
                "flights": "Flights",
                "avg_seats": "Avg seats",
                "est_passenger_capacity": "Estimated seat capacity",
            }
        ).copy()
        display_routes["Flights"] = display_routes["Flights"].map(lambda x: f"{int(x):,}")
        display_routes["Avg seats"] = display_routes["Avg seats"].map(lambda x: f"{float(x):.1f}")
        display_routes["Estimated seat capacity"] = display_routes["Estimated seat capacity"].map(lambda x: f"{int(x):,}")
        st.dataframe(display_routes, use_container_width=True, hide_index=True, height=430)

    with right:
        fig_routes = px.bar(
            routes_df.sort_values("est_passenger_capacity", ascending=True),
            x="est_passenger_capacity",
            y="route",
            orientation="h",
            title="Top 10 routes by seat capacity",
            labels={"est_passenger_capacity": "Estimated passenger capacity", "route": ""},
            color_discrete_sequence=[BLUE_MAIN],
        )
        style_fig(fig_routes, height=430, showlegend=False)
        fig_routes.update_layout(coloraxis_showscale=False)
        show_fig(fig_routes)

    top_route = routes_df.iloc[0]
    insight_box(
        f"The route <b>{top_route['route']}</b> carries the highest estimated passenger capacity in the selected view, "
        f"with about <b>{int(top_route['est_passenger_capacity']):,}</b> seats. This suggests that a small number of routes account for a large share of potential passenger throughput."
    )

section_close()

section_open(
    "Monthly Passenger Capacity Trend",
    "This trend shows how estimated seat capacity changes across the year for the current filtered network."
)

monthly_df = get_monthly_capacity_df_cached(origins, dest_filter)

if monthly_df.empty:
    st.info("No monthly capacity data is available for the selected filters.")
else:
    fig_month = px.line(
        monthly_df,
        x="month_label",
        y="est_passenger_capacity",
        markers=True,
        title="Estimated passenger capacity by month",
        labels={"month_label": "Month", "est_passenger_capacity": "Estimated passenger capacity"},
        category_orders={"month_label": MONTH_LABELS},
    )
    fig_month.update_traces(line=dict(color="red"))
    style_fig(fig_month, height=420, showlegend=False)
    show_fig(fig_month)

    top_month = monthly_df.sort_values("est_passenger_capacity", ascending=False).iloc[0]
    insight_box(
        f"<b>{top_month['month_label']}</b> has the highest estimated seat capacity in the current view, "
        f"with about <b>{int(top_month['est_passenger_capacity']):,}</b> seats."
    )

section_close()