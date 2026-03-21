from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from part3.db import query_df
from part5.dashboard_features.delay_analysis_features import (
    MONTH_LABELS,
    MONTH_TO_NUM,
    get_destinations,
    get_kpi_summary,
    get_delay_values,
    get_delay_histogram_df,
    get_carrier_delay_df,
    get_routes_delay_df,
    get_time_of_day_df,
    get_wind_category_df,
    get_wind_sign_summary_filtered,
    get_precipitation_df,
    get_weather_delay_correlation_filtered,
    get_visibility_df,
    get_distance_delay_df,
    get_manufacturer_delay_summary_filtered,
)

st.set_page_config(
    page_title="Delay Analysis",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------------------------------------------------
# Styling
# -------------------------------------------------------------------

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
RED = "#f43737"
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
            min-height: 190px;
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

        .warning-box {{
            background: #fff8e8;
            border-left: 4px solid #d4a72c;
            padding: 0.95rem 1.05rem;
            border-radius: 12px;
            color: #6b5b1e;
            margin-top: 0.9rem;
            margin-bottom: 0.6rem;
            line-height: 1.6;
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

        div[data-testid="stMetric"] {{
            background: transparent;
            border: none;
            box-shadow: none;
            padding: 0;
        }}

        div[data-testid="stSlider"] {{
            padding-top: 0.5rem;
            padding-bottom: 0.9rem;
        }}

        div[data-testid="stDataFrame"] {{
            border-radius: 12px;
            overflow: hidden;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------
# Cached data wrappers
# -------------------------------------------------------------------

@st.cache_data
def get_destinations_cached():
    return get_destinations()


@st.cache_data
def get_kpi_summary_cached(origins, months, dest_filter, day_sql, day_params):
    return get_kpi_summary(list(origins), list(months), dest_filter, day_sql, list(day_params))


@st.cache_data
def get_delay_values_cached(origins, months, dest_filter, day_sql, day_params):
    return get_delay_values(list(origins), list(months), dest_filter, day_sql, list(day_params))


@st.cache_data
def get_delay_histogram_df_cached(origins, months, dest_filter, day_sql, day_params, max_delay_cap):
    return get_delay_histogram_df(
        origins=list(origins),
        months=list(months),
        dest_filter=dest_filter,
        day_sql=day_sql,
        day_params=list(day_params),
        max_delay_cap=max_delay_cap,
    )


@st.cache_data
def get_carrier_delay_df_cached(origins, months, dest_filter, day_sql, day_params):
    return get_carrier_delay_df(list(origins), list(months), dest_filter, day_sql, list(day_params))


@st.cache_data
def get_routes_delay_df_cached(origins, months, dest_filter, day_sql, day_params):
    return get_routes_delay_df(list(origins), list(months), dest_filter, day_sql, list(day_params))


@st.cache_data
def get_time_of_day_df_cached(origins, months, dest_filter, day_sql, day_params):
    return get_time_of_day_df(list(origins), list(months), dest_filter, day_sql, list(day_params))


@st.cache_data
def get_wind_category_df_cached(origins, months, dest_filter, day_sql, day_params):
    return get_wind_category_df(list(origins), list(months), dest_filter, day_sql, list(day_params))


@st.cache_data
def get_wind_sign_summary_filtered_cached(origins, months, dest_filter, day_sql, day_params):
    return get_wind_sign_summary_filtered(list(origins), list(months), dest_filter, day_sql, list(day_params))


@st.cache_data
def get_precipitation_df_cached(origins, months, dest_filter, day_sql, day_params):
    return get_precipitation_df(list(origins), list(months), dest_filter, day_sql, list(day_params))


@st.cache_data
def get_weather_delay_correlation_filtered_cached(origins, months, dest_filter, day_sql, day_params):
    return get_weather_delay_correlation_filtered(list(origins), list(months), dest_filter, day_sql, list(day_params))


@st.cache_data
def get_visibility_df_cached(origins, months, dest_filter, day_sql, day_params):
    return get_visibility_df(list(origins), list(months), dest_filter, day_sql, list(day_params))


@st.cache_data
def get_distance_delay_df_cached(origins, months, dest_filter, day_sql, day_params):
    return get_distance_delay_df(list(origins), list(months), dest_filter, day_sql, list(day_params))


@st.cache_data
def get_manufacturer_delay_summary_filtered_cached(origins, months, dest_filter, day_sql, day_params, min_flights=500):
    return get_manufacturer_delay_summary_filtered(
        list(origins), list(months), dest_filter, day_sql, list(day_params), min_flights=min_flights
    )


@st.cache_data
def get_timezone_delay_df_cached(origins, months, dest_filter, day_sql, day_params):
    origin_ph = ",".join(["?"] * len(origins))
    month_ph = ",".join(["?"] * len(months))

    params = list(origins) + list(months)
    dest_sql = ""
    if dest_filter is not None:
        dest_sql = "AND dest = ?"
        params.append(dest_filter)

    params.extend(day_params)

    query = f"""
        SELECT
            (dest_tz_offset - origin_tz_offset) AS tz_diff,
            CASE
                WHEN (dest_tz_offset - origin_tz_offset) <= -3 THEN 'Westbound (3+ hr behind)'
                WHEN (dest_tz_offset - origin_tz_offset) = -2 THEN 'Westbound (2 hr behind)'
                WHEN (dest_tz_offset - origin_tz_offset) = -1 THEN 'Westbound (1 hr behind)'
                WHEN (dest_tz_offset - origin_tz_offset) = 0 THEN 'Same timezone'
                WHEN (dest_tz_offset - origin_tz_offset) = 1 THEN 'Eastbound (1 hr ahead)'
                WHEN (dest_tz_offset - origin_tz_offset) = 2 THEN 'Eastbound (2 hr ahead)'
                ELSE 'Eastbound (3+ hr ahead)'
            END AS tz_group,
            ROUND(AVG(dep_delay), 2) AS avg_dep_delay,
            ROUND(AVG(arr_delay), 2) AS avg_arr_delay,
            ROUND(AVG(air_time), 2) AS avg_air_time,
            COUNT(*) AS flights
        FROM flights
        WHERE origin IN ({origin_ph})
          AND month IN ({month_ph})
          {dest_sql}
          {day_sql}
          AND cancelled = 0
          AND dep_delay IS NOT NULL
          AND arr_delay IS NOT NULL
          AND air_time IS NOT NULL
          AND origin_tz_offset IS NOT NULL
          AND dest_tz_offset IS NOT NULL
        GROUP BY tz_diff, tz_group
        HAVING COUNT(*) >= 50
        ORDER BY tz_diff
    """
    return query_df(query, tuple(params))

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

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


def warning_box(text):
    st.markdown(f"<div class='warning-box'>{text}</div>", unsafe_allow_html=True)


def safe_int(value) -> int:
    return 0 if value is None or pd.isna(value) else int(value)


def safe_float(value, default=0.0) -> float:
    return default if value is None or pd.isna(value) else float(value)


def style_fig(fig, height=420, showlegend=False):
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(t=65, l=20, r=40, b=20),
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


def make_share_pie(
    df: pd.DataFrame,
    category_col: str,
    flights_col: str,
    title: str,
    color_map: dict[str, str],
    order: list[str] | None = None,
):
    plot_df = df.copy()

    if order is not None:
        plot_df[category_col] = pd.Categorical(plot_df[category_col], categories=order, ordered=True)
        plot_df = plot_df.sort_values(category_col)

    fig = px.pie(
        plot_df,
        names=category_col,
        values=flights_col,
        title=title,
        hole=0.52,
        color=category_col,
        color_discrete_map=color_map,
    )

    fig.update_traces(
        textposition="outside",
        textinfo="percent",
        sort=False,
        hovertemplate="%{label}<br>Share: %{percent}<br>Flights: %{value:,}<extra></extra>",
    )

    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(t=65, l=20, r=20, b=20),
        height=400,
        font=dict(color=PRIMARY, size=14),
        title_font=dict(size=16, color=PRIMARY),
        title_x=0.03,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.98,
            xanchor="left",
            x=1.02,
            title="",
        ),
    )
    return fig


def format_filter_context(
    origins: tuple[str, ...],
    dest_filter: str | None,
    months: tuple[int, ...],
    use_specific_day: bool,
    day_params: tuple[int, ...],
) -> str:
    origin_text = "all NYC departure airports" if len(origins) == 3 else origins[0]
    dest_text = "all destinations" if dest_filter is None else dest_filter

    if use_specific_day and len(day_params) == 3:
        date_text = f"{day_params[2]:02d}-{day_params[1]:02d}-{day_params[0]}"
    elif len(months) == 12:
        date_text = "the full year"
    else:
        month_names = [MONTH_LABELS[m - 1] for m in months]
        if len(month_names) <= 3:
            date_text = ", ".join(month_names)
        else:
            date_text = f"{len(month_names)} selected months"

    return f"Current view: {origin_text} → {dest_text}, filtered to {date_text}."


def cleaned_manufacturer_table(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    rename_map = {
        "manufacturer": "Manufacturer",
        "flights": "Flights",
        "avg_dep_delay": "Avg dep delay",
        "avg_arr_delay": "Avg arr delay",
        "cancel_pct": "Cancel %",
    }
    out = out.rename(columns=rename_map)
    if "Flights" in out.columns:
        out["Flights"] = out["Flights"].map(lambda x: f"{int(x):,}")
    for col in ["Avg dep delay", "Avg arr delay", "Cancel %"]:
        if col in out.columns:
            out[col] = out[col].map(lambda x: round(float(x), 2))
    return out


def describe_sample_size(n: int) -> str:
    if n < 30:
        return "very small"
    if n < 100:
        return "small"
    if n < 500:
        return "moderate"
    return "large"


def histogram_bins(n: int) -> int:
    if n < 30:
        return max(8, n)
    if n < 100:
        return 15
    if n < 300:
        return 25
    return 60

# -------------------------------------------------------------------
# Filters
# -------------------------------------------------------------------

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

st.sidebar.subheader("Date")
use_specific_day = st.sidebar.checkbox("Filter to a specific day", value=False)

day_sql = ""
day_params: list[int] = []

if use_specific_day:
    chosen_date = st.sidebar.date_input(
        "Select date",
        value=pd.to_datetime("2023-01-01"),
        min_value=pd.to_datetime("2023-01-01"),
        max_value=pd.to_datetime("2023-12-31"),
    )
    day_sql = "AND year = ? AND month = ? AND day = ?"
    day_params = [chosen_date.year, chosen_date.month, chosen_date.day]
    months = [chosen_date.month]
else:
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
        label_visibility="collapsed",
        key="month_preset",
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
            "Select months (any combination)",
            MONTH_LABELS,
            default=MONTH_LABELS,
        )

    months = [MONTH_TO_NUM[m] for m in selected_months]
    if not months:
        st.warning("Select at least one month.")
        st.stop()

months = tuple(months)
day_params_tuple = tuple(day_params)
filter_context = format_filter_context(origins, dest_filter, months, use_specific_day, day_params_tuple)

# -------------------------------------------------------------------
# Intro
# -------------------------------------------------------------------

st.markdown(
    f"""
    <div class="intro-box">
        <div class="intro-title"> Delay Analysis and Causes</div>
        <div class="intro-text">
            This page shows how often delays occur, how severe they are, and which operational
            and weather-related factors are associated with worse performance across NYC flights.
        </div>
        <div class="filter-row">
            <div class="intro-note">{filter_context}</div>
            <div class="intro-note-secondary">Interactive filters: departure airport, arrival airport, date</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------
# Delay Statistics
# -------------------------------------------------------------------

section_open(
    "Delay Statistics Overview",
    "These views summarize delay frequency, delay severity, and which airlines or routes are most affected under the current filters.",
)

kpi = get_kpi_summary_cached(origins, months, dest_filter, day_sql, day_params_tuple)
delays_df = get_delay_values_cached(origins, months, dest_filter, day_sql, day_params_tuple)

delayed_flights = safe_int(kpi["delayed_flights"])
avg_dep_delay = safe_float(kpi["avg_dep_delay"], 0.0)
pct_delayed_15 = safe_float(kpi["pct_delayed_15"], 0.0)
pct_delayed_30 = safe_float(kpi["pct_delayed_30"], 0.0)

median_delay = float(delays_df["dep_delay"].median()) if not delays_df.empty else None
p95_delay = float(delays_df["dep_delay"].quantile(0.95)) if not delays_df.empty else None

sample_n = len(delays_df)
sample_label = describe_sample_size(sample_n)

row1_col1, row1_col2, row1_col3 = st.columns(3, gap="large")
with row1_col1:
    kpi_card("Delayed flights", f"{delayed_flights:,}", "Flights with positive departure delay")
with row1_col2:
    kpi_card("Average departure delay", f"{avg_dep_delay:.1f}", "Minutes")
with row1_col3:
    kpi_card("Share delayed > 15 min", f"{pct_delayed_15:.1f}%", "Flights above 15 minutes")

row2_col1, row2_col2, row2_col3 = st.columns(3, gap="large")
with row2_col1:
    kpi_card("Share delayed > 30 min", f"{pct_delayed_30:.1f}%", "Flights above 30 minutes")
with row2_col2:
    kpi_card("Median departure delay", f"{median_delay:.1f}" if median_delay is not None else "n/a", "Minutes")
with row2_col3:
    kpi_card("95th percentile delay", f"{p95_delay:.1f}" if p95_delay is not None else "n/a", "Minutes")

if sample_n < 50:
    warning_box(
        f"The current filter selection produces a <b>{sample_label}</b> sample ({sample_n} observed delay values). "
        f"Results below should be interpreted carefully because small samples can shift strongly with small filter changes."
    )

st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

st.subheader("Departure Delay Distribution")
st.markdown("This chart shows the distribution of departure delays in the current filtered sample.")

max_delay_cap = st.slider("Maximum delay shown (minutes)", 60, 600, 240, step=30)

hist_df = get_delay_histogram_df_cached(
    origins=origins,
    months=months,
    dest_filter=dest_filter,
    day_sql=day_sql,
    day_params=day_params_tuple,
    max_delay_cap=max_delay_cap,
)

if hist_df.empty:
    st.info("No delay data available for the selected filters.")
else:
    nbins = histogram_bins(len(hist_df))
    fig_hist = px.histogram(
        hist_df,
        x="dep_delay",
        nbins=nbins,
        title=f"Distribution of departure delays (capped at {max_delay_cap} minutes)",
        labels={"dep_delay": "Departure delay (minutes)"},
        color_discrete_sequence=[BLUE_MAIN],
    )
    style_fig(fig_hist, height=450, showlegend=False)
    fig_hist.update_yaxes(title="Number of flights")
    show_fig(fig_hist)

    if len(hist_df) < 50:
        insight_box(
            f"This filtered view contains a <b>small number of observations</b>, so the histogram uses fewer bins to keep the pattern readable."
        )
    else:
        insight_box(
            f"Most flights in the current filtered view cluster in the lower delay ranges, while very long delays appear less often."
        )

st.markdown("<div style='height: 0.95rem;'></div>", unsafe_allow_html=True)

st.subheader("Average Departure Delay by Airline")
st.markdown("This comparison shows which airlines have the highest average departure delay in the current filtered sample.")

carrier_df = get_carrier_delay_df_cached(origins, months, dest_filter, day_sql, day_params_tuple)

if carrier_df.empty:
    st.info("No airline meets the minimum flight threshold for the selected filters.")
else:
    colE, colF = st.columns([1, 1], gap="large")
    with colE:
        display_carrier_df = carrier_df.rename(
            columns={
                "airline": "Airline",
                "flights": "Flights",
                "avg_dep_delay": "Avg dep delay",
                "avg_arr_delay": "Avg arr delay",
            }
        ).copy()
        display_carrier_df["Flights"] = display_carrier_df["Flights"].map(lambda x: f"{int(x):,}")
        st.dataframe(display_carrier_df, use_container_width=True, hide_index=True, height=420)

    with colF:
        fig_car = px.bar(
            carrier_df.sort_values("avg_dep_delay", ascending=True),
            x="avg_dep_delay",
            y="airline",
            orientation="h",
            title="Average departure delay by airline",
            labels={"avg_dep_delay": "Average departure delay (minutes)", "airline": ""},
            color_discrete_sequence=[BLUE_DARK],
        )
        style_fig(fig_car, height=420, showlegend=False)
        fig_car.update_layout(coloraxis_showscale=False)
        show_fig(fig_car)

    top_airline = carrier_df.iloc[0]
    insight_box(
        f"<b>{top_airline['airline']}</b> has the highest average departure delay in the current filtered view at <b>{top_airline['avg_dep_delay']:.1f} minutes</b>."
    )

st.markdown("<div style='height: 0.8rem;'></div>", unsafe_allow_html=True)

st.subheader("Average Departure Delay by Route")
st.markdown("This comparison highlights routes where departure delays are highest while keeping only routes with enough flights.")

routes_df = get_routes_delay_df_cached(origins, months, dest_filter, day_sql, day_params_tuple)

if routes_df.empty:
    st.info("No routes meet the minimum flight threshold for the selected filters.")
else:
    colG, colH = st.columns([1, 1], gap="large")
    with colG:
        display_routes_df = routes_df[["route", "number_of_flights", "avg_dep_delay"]].rename(
            columns={
                "route": "Route",
                "number_of_flights": "Flights",
                "avg_dep_delay": "Avg dep delay",
            }
        ).copy()
        display_routes_df["Flights"] = display_routes_df["Flights"].map(lambda x: f"{int(x):,}")
        st.dataframe(display_routes_df, use_container_width=True, hide_index=True, height=420)

    with colH:
        fig_routes = px.bar(
            routes_df.sort_values("avg_dep_delay", ascending=True),
            x="avg_dep_delay",
            y="route",
            orientation="h",
            title="Average departure delay by route",
            labels={"avg_dep_delay": "Average departure delay (minutes)", "route": ""},
            color_discrete_sequence=[BLUE_DARK],
        )
        style_fig(fig_routes, height=420, showlegend=False)
        fig_routes.update_layout(coloraxis_showscale=False)
        show_fig(fig_routes)

    top_route = routes_df.iloc[0]
    insight_box(
        f"<b>{top_route['route']}</b> has the highest average departure delay in the filtered sample at <b>{top_route['avg_dep_delay']:.1f} minutes</b>."
    )

section_close()

# -------------------------------------------------------------------
# Delay Causes
# -------------------------------------------------------------------

section_open(
    "Potential Causes of Delay",
    "The sections below explore possible explanations for delay patterns, including time of day, weather, route distance, timezone difference, and aircraft manufacturer.",
)

st.subheader("Departure Hour and Delay Build-Up")
st.markdown(
    "Later departures can face higher delays because disruption builds through the day. "
    "This chart compares average departure delay with flight volume by scheduled departure hour."
)

tod_df = get_time_of_day_df_cached(origins, months, dest_filter, day_sql, day_params_tuple)

if not tod_df.empty:
    fig_tod = make_subplots(specs=[[{"secondary_y": True}]])
    fig_tod.add_trace(
        go.Scatter(
            x=tod_df["dep_hour_label"],
            y=tod_df["avg_dep_delay"],
            mode="lines+markers",
            name="Average departure delay",
            line=dict(color=RED, width=3),
            marker=dict(size=7, color=RED),
        ),
        secondary_y=False,
    )
    fig_tod.add_trace(
        go.Bar(
            x=tod_df["dep_hour_label"],
            y=tod_df["flights"],
            name="Flights",
            opacity=0.28,
            marker_color=BLUE_LIGHT,
        ),
        secondary_y=True,
    )
    fig_tod.update_layout(
        title="Average departure delay and flight volume by scheduled departure hour",
        xaxis_title="Scheduled departure hour",
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(t=65, l=20, r=20, b=20),
        height=450,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        font=dict(color=PRIMARY, size=14),
        title_font=dict(size=16, color=PRIMARY),
        title_x=0.03,
    )
    fig_tod.update_yaxes(title_text="Average departure delay (minutes)", secondary_y=False, gridcolor="#edf2f7")
    fig_tod.update_yaxes(title_text="Number of flights", secondary_y=True, showgrid=False)
    show_fig(fig_tod)

    peak_row = tod_df.sort_values("avg_dep_delay", ascending=False).iloc[0]
    insight_box(
        f"The highest average departure delay in the current view appears around <b>{peak_row['dep_hour_label']}</b>, at about <b>{peak_row['avg_dep_delay']:.1f} minutes</b>."
    )
else:
    st.info("No time-of-day data available for the selected filters.")

st.markdown("<div style='height: 1.15rem;'></div>", unsafe_allow_html=True)

st.subheader("Wind Conditions")
st.markdown(
    "Wind conditions can affect flight operations and delay severity. "
    "The left chart shows average departure delay by wind category, while the right chart shows how common each wind category is."
)

try:
    wind_df = get_wind_category_df_cached(origins, months, dest_filter, day_sql, day_params_tuple)

    if wind_df.empty:
        st.info("No wind-category data available for the selected filters.")
    else:
        wind_order = [
            "Calm (<10 mph)",
            "Moderate (10-20 mph)",
            "Strong (20-30 mph)",
            "Severe (30+ mph)",
        ]
        wind_colors = {
            "Calm (<10 mph)": BLUE_LIGHT,
            "Moderate (10-20 mph)": BLUE_MID,
            "Strong (20-30 mph)": BLUE_MAIN,
            "Severe (30+ mph)": BLUE_DARK,
        }

        colW1, colW2 = st.columns(2, gap="large")

        with colW1:
            fig_wind_dep = px.bar(
                wind_df,
                x="wind_category",
                y="avg_dep_delay",
                title="Average departure delay by wind category",
                labels={"wind_category": "Wind category", "avg_dep_delay": "Average departure delay (minutes)"},
                color="wind_category",
                category_orders={"wind_category": wind_order},
                color_discrete_map=wind_colors,
            )
            style_fig(fig_wind_dep, height=400, showlegend=False)
            fig_wind_dep.update_xaxes(tickangle=-25)
            show_fig(fig_wind_dep)

        with colW2:
            fig_wind_share = make_share_pie(
                wind_df,
                category_col="wind_category",
                flights_col="flights",
                title="Flight share by wind category",
                color_map=wind_colors,
                order=wind_order,
            )
            show_fig(fig_wind_share)

        top_wind_delay = wind_df.sort_values("avg_dep_delay", ascending=False).iloc[0]
        top_wind_share = wind_df.assign(
            share_pct=100 * wind_df["flights"] / wind_df["flights"].sum()
        ).sort_values("share_pct", ascending=False).iloc[0]

        insight_box(
            f"<b>{top_wind_delay['wind_category']}</b> shows the highest average departure delay at <b>{top_wind_delay['avg_dep_delay']:.1f} minutes</b>, while <b>{top_wind_share['wind_category']}</b> is the most common wind condition."
        )

except Exception as e:
    st.info("Wind analysis unavailable — check that joined weather data includes wind speed.")
    st.caption(f"Details: {e}")

st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)

st.subheader("Headwind and Tailwind Effect on Airtime")
st.markdown(
    "This comparison estimates whether flights experienced headwinds or tailwinds based on route direction and wind direction."
)

try:
    wind_sign_df = get_wind_sign_summary_filtered_cached(origins, months, dest_filter, day_sql, day_params_tuple)

    if wind_sign_df.empty:
        st.info("No headwind/tailwind summary available.")
    else:
        col_ws1, col_ws2 = st.columns([1, 1.15], gap="large")

        with col_ws1:
            display_wind_sign = wind_sign_df.rename(
                columns={
                    "wind_relation": "Wind relation",
                    "flights": "Flights",
                    "mean_air_time": "Mean airtime",
                    "mean_distance": "Mean distance",
                    "mean_dot": "Mean wind effect",
                }
            ).copy()
            if "Flights" in display_wind_sign.columns:
                display_wind_sign["Flights"] = display_wind_sign["Flights"].map(lambda x: f"{int(x):,}")
            for col in ["Mean airtime", "Mean distance", "Mean wind effect"]:
                if col in display_wind_sign.columns:
                    display_wind_sign[col] = display_wind_sign[col].map(lambda x: round(float(x), 2))
            st.dataframe(display_wind_sign, use_container_width=True, hide_index=True, height=280)

        with col_ws2:
            fig_wind_sign = px.bar(
                wind_sign_df,
                x="wind_relation",
                y="mean_air_time",
                title="Average airtime by wind relation",
                labels={"wind_relation": "Wind relation", "mean_air_time": "Mean airtime (minutes)"},
                color="wind_relation",
                color_discrete_map={
                    "Headwind": "#ff9bb4",
                    "Neutral": "#a3afff",
                    "Tailwind": "#80c9fd",
                },
            )
            style_fig(fig_wind_sign, height=280, showlegend=False)
            show_fig(fig_wind_sign)

        highest_airtime = wind_sign_df.sort_values("mean_air_time", ascending=False).iloc[0]
        lowest_airtime = wind_sign_df.sort_values("mean_air_time", ascending=True).iloc[0]
        insight_box(
            f"<b>{highest_airtime['wind_relation']}</b> flights have the longest average airtime at <b>{highest_airtime['mean_air_time']:.1f} minutes</b>, while <b>{lowest_airtime['wind_relation']}</b> flights are shortest on average."
        )

except Exception as e:
    st.info("Headwind vs tailwind summary unavailable.")
    st.caption(f"Details: {e}")

st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)

st.subheader("Precipitation Conditions")
st.markdown(
    "Rain and heavier precipitation can slow airport operations. "
    "The left chart shows delay severity, while the right chart shows how common each precipitation category is."
)

try:
    precip_df = get_precipitation_df_cached(origins, months, dest_filter, day_sql, day_params_tuple)

    if precip_df.empty:
        st.info("No precipitation data available for the selected filters.")
    else:
        precip_order = [
            "None (0 in)",
            "Light (0–0.1 in/hr)",
            "Moderate (0.1–0.5 in/hr)",
            "Heavy (>0.5 in/hr)",
        ]
        precip_colors = {
            "None (0 in)": BLUE_LIGHT,
            "Light (0–0.1 in/hr)": BLUE_MID,
            "Moderate (0.1–0.5 in/hr)": BLUE_MAIN,
            "Heavy (>0.5 in/hr)": BLUE_DARK,
        }

        colP1, colP2 = st.columns(2, gap="large")

        with colP1:
            fig_precip = px.bar(
                precip_df,
                x="precip_category",
                y="avg_dep_delay",
                title="Average departure delay by precipitation category",
                labels={"precip_category": "Precipitation category", "avg_dep_delay": "Average departure delay (minutes)"},
                color="precip_category",
                category_orders={"precip_category": precip_order},
                color_discrete_map=precip_colors,
            )
            style_fig(fig_precip, height=400, showlegend=False)
            fig_precip.update_xaxes(tickangle=-25)
            show_fig(fig_precip)

        with colP2:
            fig_precip_share = make_share_pie(
                precip_df,
                category_col="precip_category",
                flights_col="flights",
                title="Flight share by precipitation category",
                color_map=precip_colors,
                order=precip_order,
            )
            show_fig(fig_precip_share)

        top_precip_delay = precip_df.sort_values("avg_dep_delay", ascending=False).iloc[0]
        top_precip_share = precip_df.assign(
            share_pct=100 * precip_df["flights"] / precip_df["flights"].sum()
        ).sort_values("share_pct", ascending=False).iloc[0]

        insight_box(
            f"<b>{top_precip_delay['precip_category']}</b> shows the highest average departure delay, while <b>{top_precip_share['precip_category']}</b> is the most common precipitation condition."
        )

except Exception as e:
    st.info("Precipitation analysis unavailable — check that joined weather data includes precipitation.")
    st.caption(f"Details: {e}")

st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)

st.subheader("Combined Wind and Precipitation Conditions")
st.markdown(
    "This heatmap highlights whether difficult wind and precipitation conditions reinforce each other."
)

weather_corr_df = get_weather_delay_correlation_filtered_cached(
    origins, months, dest_filter, day_sql, day_params_tuple
)

if weather_corr_df.empty:
    st.info("No combined weather correlation data available for the selected filters.")
else:
    fig_weather_corr = px.density_heatmap(
        weather_corr_df,
        x="wind_speed_bucket",
        y="precip_bucket",
        z="avg_dep_delay",
        histfunc="avg",
        title="Average departure delay by wind speed and precipitation",
        labels={
            "wind_speed_bucket": "Wind speed bucket (mph)",
            "precip_bucket": "Precipitation bucket",
            "avg_dep_delay": "Average departure delay (minutes)",
        },
        color_continuous_scale="RdYlGn_r",
    )
    style_fig(fig_weather_corr, height=450, showlegend=False)
    fig_weather_corr.update_layout(coloraxis_colorbar=dict(title="Avg delay (min)"))
    show_fig(fig_weather_corr)

    top_weather_cell = weather_corr_df.sort_values("avg_dep_delay", ascending=False).iloc[0]
    insight_box(
        f"The highest average departure delay appears for the combination of wind speed around <b>{top_weather_cell['wind_speed_bucket']}</b> mph and precipitation bucket <b>{top_weather_cell['precip_bucket']}</b>."
    )

st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)

st.subheader("Visibility Conditions")
st.markdown(
    "Lower visibility can make operations more difficult. "
    "These charts compare delay severity and flight share across visibility categories."
)

try:
    vis_df = get_visibility_df_cached(origins, months, dest_filter, day_sql, day_params_tuple)

    if vis_df.empty:
        st.info("No visibility data available for the selected filters.")
    else:
        vis_order = [
            "Poor (<2 mi)",
            "Low (2–5 mi)",
            "Moderate (5–8 mi)",
            "Good (>8 mi)",
        ]
        vis_colors = {
            "Poor (<2 mi)": BLUE_DARK,
            "Low (2–5 mi)": BLUE_MAIN,
            "Moderate (5–8 mi)": BLUE_MID,
            "Good (>8 mi)": BLUE_LIGHT,
        }

        colV1, colV2 = st.columns(2, gap="large")

        with colV1:
            fig_vis = px.bar(
                vis_df,
                x="vis_category",
                y="avg_dep_delay",
                title="Average departure delay by visibility category",
                labels={"vis_category": "Visibility category", "avg_dep_delay": "Average departure delay (minutes)"},
                color="vis_category",
                category_orders={"vis_category": vis_order},
                color_discrete_map=vis_colors,
            )
            style_fig(fig_vis, height=400, showlegend=False)
            fig_vis.update_xaxes(tickangle=-25)
            show_fig(fig_vis)

        with colV2:
            fig_vis_share = make_share_pie(
                vis_df,
                category_col="vis_category",
                flights_col="flights",
                title="Flight share by visibility category",
                color_map=vis_colors,
                order=vis_order,
            )
            show_fig(fig_vis_share)

        top_vis_delay = vis_df.sort_values("avg_dep_delay", ascending=False).iloc[0]
        top_vis_share = vis_df.assign(
            share_pct=100 * vis_df["flights"] / vis_df["flights"].sum()
        ).sort_values("share_pct", ascending=False).iloc[0]

        insight_box(
            f"<b>{top_vis_delay['vis_category']}</b> has the highest average departure delay, while <b>{top_vis_share['vis_category']}</b> is the most common visibility condition."
        )

except Exception as e:
    st.info("Visibility analysis unavailable — check that joined weather data includes visibility.")
    st.caption(f"Details: {e}")

st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)

st.subheader("Route Distance")
st.markdown(
    "Route distance may influence delays because short- and long-haul flights face different operational constraints."
)

dist_df = get_distance_delay_df_cached(origins, months, dest_filter, day_sql, day_params_tuple)

if dist_df.empty:
    st.info("No distance-based delay data available for the selected filters.")
else:
    colD1, colD2 = st.columns(2, gap="large")

    with colD1:
        fig_dist = px.bar(
            dist_df,
            x="distance_range",
            y="avg_dep_delay",
            title="Average departure delay by route distance band",
            labels={"distance_range": "Distance band", "avg_dep_delay": "Average departure delay (minutes)"},
            color_discrete_sequence=[BLUE_MAIN],
        )
        style_fig(fig_dist, height=400, showlegend=False)
        fig_dist.update_xaxes(tickangle=-25)
        show_fig(fig_dist)

    with colD2:
        fig_dist_n = px.bar(
            dist_df,
            x="distance_range",
            y="flights",
            title="Flight volume by route distance band",
            labels={"distance_range": "Distance band", "flights": "Number of flights"},
            color_discrete_sequence=[BLUE_LIGHT],
        )
        style_fig(fig_dist_n, height=400, showlegend=False)
        fig_dist_n.update_xaxes(tickangle=-25)
        show_fig(fig_dist_n)

    top_dist_delay = dist_df.sort_values("avg_dep_delay", ascending=False).iloc[0]
    top_dist_volume = dist_df.sort_values("flights", ascending=False).iloc[0]
    insight_box(
        f"The <b>{top_dist_delay['distance_range']}</b> distance band has the highest average departure delay, while <b>{top_dist_volume['distance_range']}</b> contains the highest flight volume."
    )

st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)

st.subheader("Timezone Difference Between Origin and Destination")
st.markdown(
    "Flights crossing time zones often represent longer trips and different scheduling patterns. "
    "These charts compare delay, airtime, and flight volume across timezone differences between origin and destination."
)

tz_df = get_timezone_delay_df_cached(origins, months, dest_filter, day_sql, day_params_tuple)

if tz_df.empty:
    st.info("No timezone-difference data is available for the selected filters.")
else:
    tz_order = [
        "Westbound (3+ hr behind)",
        "Westbound (2 hr behind)",
        "Westbound (1 hr behind)",
        "Same timezone",
        "Eastbound (1 hr ahead)",
        "Eastbound (2 hr ahead)",
        "Eastbound (3+ hr ahead)",
    ]

    tz_colors = {
        "Westbound (3+ hr behind)": BLUE_DARK,
        "Westbound (2 hr behind)": BLUE_MAIN,
        "Westbound (1 hr behind)": BLUE_MID,
        "Same timezone": BLUE_LIGHT,
        "Eastbound (1 hr ahead)": BLUE_MID,
        "Eastbound (2 hr ahead)": BLUE_MAIN,
        "Eastbound (3+ hr ahead)": BLUE_DARK,
    }

    tz_df["tz_group"] = pd.Categorical(tz_df["tz_group"], categories=tz_order, ordered=True)
    tz_df["tz_group"] = tz_df["tz_group"].cat.remove_unused_categories()
    tz_df = tz_df.sort_values("tz_group")

    colT1, colT2 = st.columns(2, gap="large")

    with colT1:
        fig_tz_delay = px.bar(
            tz_df,
            x="tz_group",
            y="avg_dep_delay",
            title="Average departure delay by timezone difference",
            labels={
                "tz_group": "Timezone difference",
                "avg_dep_delay": "Average departure delay (minutes)",
            },
            color="tz_group",
            color_discrete_map=tz_colors,
        )
        style_fig(fig_tz_delay, height=400, showlegend=False)
        fig_tz_delay.update_xaxes(tickangle=-25)
        show_fig(fig_tz_delay)

    with colT2:
        fig_tz_flights = px.bar(
            tz_df,
            x="tz_group",
            y="flights",
            title="Flight volume by timezone difference",
            labels={
                "tz_group": "Timezone difference",
                "flights": "Number of flights",
            },
            color="tz_group",
            color_discrete_map=tz_colors,
        )
        style_fig(fig_tz_flights, height=400, showlegend=False)
        fig_tz_flights.update_xaxes(tickangle=-25)
        show_fig(fig_tz_flights)

    display_tz = tz_df[["tz_group", "flights", "avg_dep_delay", "avg_arr_delay", "avg_air_time"]].rename(
        columns={
            "tz_group": "Timezone difference",
            "flights": "Flights",
            "avg_dep_delay": "Avg dep delay",
            "avg_arr_delay": "Avg arr delay",
            "avg_air_time": "Avg airtime",
        }
    ).copy()
    display_tz["Flights"] = display_tz["Flights"].map(lambda x: f"{int(x):,}")
    for col in ["Avg dep delay", "Avg arr delay", "Avg airtime"]:
        display_tz[col] = display_tz[col].map(lambda x: f"{float(x):.2f}")

    st.dataframe(display_tz, use_container_width=True, hide_index=True)

    top_tz_delay = tz_df.sort_values("avg_dep_delay", ascending=False).iloc[0]
    top_tz_volume = tz_df.sort_values("flights", ascending=False).iloc[0]

    insight_box(
        f"<b>{top_tz_delay['tz_group']}</b> flights show the highest average departure delay at "
        f"<b>{top_tz_delay['avg_dep_delay']:.1f} minutes</b>, while "
        f"<b>{top_tz_volume['tz_group']}</b> accounts for the highest flight volume in the current filtered sample."
    )

st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)

st.subheader("Aircraft Manufacturer")
st.markdown(
    "This comparison explores whether aircraft manufacturer groups show different delay patterns in the filtered sample."
)

manuf_df = get_manufacturer_delay_summary_filtered_cached(
    origins, months, dest_filter, day_sql, day_params_tuple, min_flights=500
)

if manuf_df.empty:
    st.info("No manufacturer data available for the selected filters.")
else:
    colM1, colM2 = st.columns([1, 1.2], gap="large")

    with colM1:
        st.dataframe(
            cleaned_manufacturer_table(manuf_df),
            use_container_width=True,
            hide_index=True,
            height=420,
        )

    with colM2:
        fig_manuf = px.bar(
            manuf_df.sort_values("avg_dep_delay", ascending=True),
            x="avg_dep_delay",
            y="manufacturer",
            orientation="h",
            title="Average departure delay by aircraft manufacturer",
            labels={"avg_dep_delay": "Average departure delay (minutes)", "manufacturer": ""},
            hover_data={"flights": True, "cancel_pct": True, "avg_arr_delay": True},
            color_discrete_sequence=[BLUE_DARK],
        )
        style_fig(fig_manuf, height=420, showlegend=False)
        fig_manuf.update_layout(coloraxis_showscale=False)
        show_fig(fig_manuf)

    top_manuf = manuf_df.iloc[0]
    insight_box(
        f"<b>{top_manuf['manufacturer']}</b> has the highest average departure delay among manufacturers meeting the minimum threshold, at <b>{top_manuf['avg_dep_delay']:.1f} minutes</b>."
    )

section_close()