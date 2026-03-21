from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st
import plotly.express as px

from part5.dashboard_features.airport_comparison_features import (
    NYC_AIRPORTS,
    MONTH_LABELS,
    MONTH_TO_NUM,
    get_destinations,
    get_comparison_kpis,
    get_cancellation_rate_df,
    get_top_routes_by_airport,
    get_weather_impact_by_airport_df,
    get_cancellation_conclusion_text,
    get_weather_conclusion_text,
    get_routes_conclusion_text,
    get_kpi_takeaway_text,
)

st.set_page_config(
    page_title="Airport Comparison",
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
            padding-bottom: 3rem;
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
            box-shadow: 0 4px 24px rgba(31, 42, 68, 0.12);
            margin-top: 0.4rem;
            margin-bottom: 1.9rem;
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
            margin-bottom: 1.1rem;
            line-height: 1.6;
        }}

        .airport-card {{
            background: #ffffff;
            border: 1px solid {CARD_BORDER};
            border-radius: 16px;
            padding: 1.15rem 1.2rem 1.05rem 1.2rem;
            box-shadow: 0 4px 20px rgba(91, 33, 182, 0.10);
            min-height: 215px;
            margin-bottom: 0.8rem;
        }}

        .airport-title {{
            font-size: 1.1rem;
            font-weight: 750;
            color: {PRIMARY};
            margin-bottom: 0.7rem;
        }}

        .airport-main {{
            font-size: 2.1rem;
            font-weight: 800;
            color: {PRIMARY};
            line-height: 1.05;
            margin-bottom: 0.8rem;
        }}

        .airport-lines {{
            font-size: 0.98rem;
            line-height: 1.7;
            color: #374151;
        }}

        .insight-box {{
            background: #ffffff;
            border-left: 4px solid {BLUE_DARK};
            padding: 0.95rem 1.05rem;
            border-radius: 10px;
            color: {PRIMARY};
            margin-top: 0.9rem;
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

# -------------------------------------------------------------------
# Cached data wrappers
# -------------------------------------------------------------------

@st.cache_data
def get_destinations_cached():
    return get_destinations()


@st.cache_data
def get_comparison_kpis_cached(months, day_sql, day_params, dest_filter):
    return get_comparison_kpis(list(months), day_sql, list(day_params), dest_filter)


@st.cache_data
def get_cancellation_rate_df_cached(months, day_sql, day_params, dest_filter):
    return get_cancellation_rate_df(list(months), day_sql, list(day_params), dest_filter)


@st.cache_data
def get_top_routes_by_airport_cached(months, day_sql, day_params, dest_filter, n=5):
    return get_top_routes_by_airport(list(months), day_sql, list(day_params), dest_filter, n=n)


@st.cache_data
def get_weather_impact_by_airport_df_cached(months, day_sql, day_params, dest_filter):
    return get_weather_impact_by_airport_df(list(months), day_sql, list(day_params), dest_filter)


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

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


def insight_box(text: str):
    st.markdown(f"<div class='insight-box'>{text}</div>", unsafe_allow_html=True)


def show_fig(fig, use_container_width=True):
    st.plotly_chart(fig, use_container_width=use_container_width, config=PLOT_CONFIG)


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


def render_airport_kpi_card(airport: str, row: pd.Series | None):
    if row is None:
        st.markdown(
            f"""
            <div class="airport-card">
                <div class="airport-title">{airport}</div>
                <div class="airport-lines" style="color:#6b7280;">No data for selected filters.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    total_flights = 0 if pd.isna(row["total_flights"]) else int(row["total_flights"])
    avg_dep_delay = 0.0 if pd.isna(row["avg_dep_delay"]) else float(row["avg_dep_delay"])
    avg_arr_delay = 0.0 if pd.isna(row["avg_arr_delay"]) else float(row["avg_arr_delay"])
    pct_15 = 0.0 if pd.isna(row["pct_dep_delay_15"]) else float(row["pct_dep_delay_15"])
    pct_30 = 0.0 if pd.isna(row["pct_dep_delay_30"]) else float(row["pct_dep_delay_30"])

    st.markdown(
        f"""
        <div class="airport-card">
            <div class="airport-title">{airport}</div>
            <div class="airport-main">{total_flights:,} flights</div>
            <div class="airport-lines">
                Avg dep delay: <b>{avg_dep_delay:.1f} min</b><br>
                Avg arr delay: <b>{avg_arr_delay:.1f} min</b><br>
                &gt; 15 min delayed: <b>{pct_15:.1f}%</b><br>
                &gt; 30 min delayed: <b>{pct_30:.1f}%</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_filter_context(dest_filter, months, use_specific_day, day_params):
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

    return f"Current view: JFK, LGA, and EWR compared for {dest_text}, filtered to {date_text}."


# -------------------------------------------------------------------
# Main page
# -------------------------------------------------------------------

def main():
    st.title("NYC Flights Dashboard")

    st.sidebar.header("Filters")

    destinations = get_destinations_cached()

    dest_choice = st.sidebar.selectbox(
        "Arrival airport",
        ["All destinations"] + destinations
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
            max_value=pd.to_datetime("2023-12-31")
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
            key="month_preset_airport_comparison",
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
                default=MONTH_LABELS
            )

        months = [MONTH_TO_NUM[m] for m in selected_months]
        if not months:
            st.warning("Select at least one month.")
            st.stop()

    months = tuple(months)
    day_params_tuple = tuple(day_params)
    filter_context = format_filter_context(dest_filter, months, use_specific_day, day_params_tuple)

    st.markdown(
        f"""
        <div class="intro-box">
            <div class="intro-title">Airport Comparison</div>
            <div class="intro-text">
                Use this page to compare <b>JFK</b>, <b>LGA</b>, and <b>EWR</b> on traffic volume,
                reliability, route mix, and weather sensitivity. The three airports are shown side by side
                so differences remain easy to interpret under the current filters.
            </div>
            <div class="filter-row">
                <div class="intro-note">{filter_context}</div>
                <div class="intro-note-secondary">Interactive filters: arrival airport, month, specific day</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------------------------------------------------
    # KPI comparison
    # ---------------------------------------------------

    section_open(
        "Comparison KPIs",
        "These cards provide a quick side-by-side overview of traffic volume and delay severity at the three NYC airports."
    )

    kpi_df = get_comparison_kpis_cached(months, day_sql, day_params_tuple, dest_filter)

    if kpi_df.empty:
        st.info("No flights found for the selected filters.")
        st.stop()

    c1, c2, c3 = st.columns(3, gap="large")
    for col, airport in zip([c1, c2, c3], NYC_AIRPORTS):
        row_df = kpi_df[kpi_df["origin"] == airport]
        row = None if row_df.empty else row_df.iloc[0]
        with col:
            render_airport_kpi_card(airport, row)

    insight_box(get_kpi_takeaway_text(kpi_df))
    section_close()

    # ---------------------------------------------------
    # Cancellation + weather
    # ---------------------------------------------------

    section_open(
        "Cancellations and Weather Impact",
        "The charts below compare cancellation patterns and show how wind conditions relate to average departure delays."
    )

    cancel_df = get_cancellation_rate_df_cached(months, day_sql, day_params_tuple, dest_filter)
    weather_df = get_weather_impact_by_airport_df_cached(months, day_sql, day_params_tuple, dest_filter)

    left, right = st.columns(2, gap="large")

    with left:
        if cancel_df.empty:
            st.info("No cancellation data available.")
        else:
            if use_specific_day:
                fig_cancel = px.bar(
                    cancel_df,
                    x="origin",
                    y="cancellation_rate",
                    title="Cancellation rate by airport",
                    labels={"origin": "Airport", "cancellation_rate": "Cancellation rate (%)"},
                    color="origin",
                    color_discrete_map={
                        "JFK": JFK_COLOR,
                        "LGA": LGA_COLOR,
                        "EWR": EWR_COLOR,
                    },
                )
                style_fig(fig_cancel, height=400, showlegend=False)
            else:
                fig_cancel = px.line(
                    cancel_df,
                    x="month_label",
                    y="cancellation_rate",
                    color="origin",
                    markers=True,
                    title="Cancellation rate by month",
                    labels={
                        "month_label": "Month",
                        "cancellation_rate": "Cancellation rate (%)",
                        "origin": "Airport",
                    },
                    color_discrete_map={
                        "JFK": JFK_COLOR,
                        "LGA": LGA_COLOR,
                        "EWR": EWR_COLOR,
                    },
                )
                style_fig(fig_cancel, height=400, showlegend=True)
                fig_cancel.update_layout(
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title="")
                )

            show_fig(fig_cancel)
            insight_box(get_cancellation_conclusion_text(cancel_df, use_specific_day))

    with right:
        if weather_df.empty:
            st.info("No weather data available for these filters.")
        else:
            fig_weather = px.bar(
                weather_df,
                x="origin",
                y="avg_dep_delay",
                color="wind_category",
                barmode="group",
                title="Average delay by wind category",
                labels={
                    "origin": "Airport",
                    "avg_dep_delay": "Avg departure delay (min)",
                    "wind_category": "Wind",
                },
                color_discrete_map={
                    "Calm": BLUE_LIGHT,
                    "Moderate": BLUE_MID,
                    "Strong": BLUE_DARK,
                },
                category_orders={"wind_category": ["Calm", "Moderate", "Strong"]},
            )
            style_fig(fig_weather, height=400, showlegend=True)
            fig_weather.update_layout(
                legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title="")
            )
            show_fig(fig_weather)
            insight_box(get_weather_conclusion_text(weather_df))

    section_close()

    # ---------------------------------------------------
    # Routes
    # ---------------------------------------------------

    section_open(
        "Top Routes by Airport",
        "This section highlights the busiest destination routes for each NYC airport in the current filtered view."
    )

    routes_df = get_top_routes_by_airport_cached(months, day_sql, day_params_tuple, dest_filter, n=5)

    if routes_df.empty:
        st.info("No route data available.")
    else:
        routes_df = routes_df.copy()
        routes_df["route"] = routes_df["origin"] + " → " + routes_df["dest"]

        fig_routes = px.bar(
            routes_df.sort_values("flights", ascending=True),
            x="flights",
            y="route",
            color="origin",
            orientation="h",
            title="Top routes across the three airports",
            labels={"flights": "Flights", "route": "Route", "origin": "Airport"},
            color_discrete_map={
                "JFK": JFK_COLOR,
                "LGA": EWR_COLOR,
                "EWR": LGA_COLOR,
            },
        )

        style_fig(fig_routes, height=650, showlegend=True)
        fig_routes.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title="")
        )
        show_fig(fig_routes)

        display_routes = routes_df[["origin", "route", "dest", "flights"]].rename(
            columns={
                "origin": "Airport",
                "route": "Route",
                "dest": "Destination",
                "flights": "Flights",
            }
        ).copy()
        display_routes["Flights"] = display_routes["Flights"].map(lambda x: f"{int(x):,}")

        st.dataframe(
            display_routes,
            use_container_width=True,
            hide_index=True
        )

        insight_box(get_routes_conclusion_text(routes_df))

    section_close()


if __name__ == "__main__":
    main()