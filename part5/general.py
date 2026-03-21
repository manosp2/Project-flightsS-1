import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
import plotly.express as px

from part3.db import query_df
from part3.flights_analysis import plot_destinations_for_day
from part3.flights_statistics import flight_stats_for_day

st.set_page_config(
    page_title="NYC Flights Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

NYC_AIRPORTS = ["JFK", "LGA", "EWR"]
MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTH_TO_NUM = {m: i + 1 for i, m in enumerate(MONTH_LABELS)}

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

        section[data-testid="stSidebar"] {{
            background: #ffffff;
            border-right: 1px solid {CARD_BORDER};
        }}

        section[data-testid="stSidebar"] > div {{
            padding-top: 1rem;
        }}

        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {{
            color: #111827 !important;
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

        .sidebar-brand {{
            background: rgba(124, 58, 237, 0.25);
            border: 1px solid {BLUE_MID};
            border-radius: 16px;
            padding: 0.9rem 1rem;
            margin-bottom: 1rem;
        }}

        .sidebar-brand-title {{
            font-size: 1.05rem;
            font-weight: 800;
            color: #f1f5f9;
            margin-bottom: 0.2rem;
        }}

        .sidebar-brand-text {{
            font-size: 0.9rem;
            color: #c7d2fe;
            line-height: 1.45;
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

        .kpi-card {{
            background: #ffffff;
            border: 1px solid {CARD_BORDER};
            border-radius: 16px;
            padding: 1.15rem 1.2rem 1.05rem 1.2rem;
            box-shadow: 0 4px 20px rgba(91, 33, 182, 0.10);
            min-height: 185px;
            margin-bottom: 0.85rem;
        }}

        .kpi-label {{
            font-size: 0.95rem;
            color: {TEXT_MID};
            margin-bottom: 0.55rem;
            line-height: 1.45;
            font-weight: 650;
        }}

        .kpi-value {{
            font-size: 2.4rem;
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

        .airport-mini-card {{
            background: #ffffff;
            border: 1px solid {CARD_BORDER};
            border-radius: 16px;
            padding: 1rem 1rem 0.95rem 1rem;
            box-shadow: 0 4px 20px rgba(91, 33, 182, 0.10);
            min-height: 155px;
        }}

        .airport-mini-title {{
            font-size: 1rem;
            font-weight: 750;
            color: {PRIMARY};
            margin-bottom: 0.45rem;
        }}

        .airport-mini-main {{
            font-size: 1.55rem;
            font-weight: 800;
            color: {PRIMARY};
            margin-bottom: 0.5rem;
        }}

        .airport-pill {{
            display: inline-block;
            padding: 0.35rem 0.75rem;
            border-radius: 999px;
            color: white;
            font-size: 0.86rem;
            font-weight: 700;
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

        div[data-testid="stDataFrame"] {{
            border-radius: 12px;
            overflow: hidden;
        }}

        div[data-testid="stAlert"] p,
        div[data-testid="stAlert"] li,
        div[data-testid="stAlert"] div:not([class]) {{
            color: #111827 !important;
            font-weight: 500;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------
# Helpers
# ---------------------------------------------------

def build_ph(values: list) -> str:
    return ",".join(["?"] * len(values))


def month_name(m: int) -> str:
    return MONTH_LABELS[m - 1] if 1 <= m <= 12 else str(m)


def build_day_sql_for_alias(day_sql: str, alias: str) -> str:
    return (
        day_sql.replace("AND year", f"AND {alias}.year")
               .replace("AND month", f"AND {alias}.month")
               .replace("AND day", f"AND {alias}.day")
    )


def style_fig(fig, height=420, showlegend=False):
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(t=65, l=20, r=20, b=20),
        height=height,
        showlegend=showlegend,
        font=dict(color="#000000", size=14),
        title_font=dict(size=16, color="#000000"),
        title_x=0.03,
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="#edf2f7", zeroline=False)
    return fig


def show_fig(fig, use_container_width=True):
    st.plotly_chart(fig, use_container_width=use_container_width, config=PLOT_CONFIG)


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


def kpi_card(label: str, value: str, footnote: str = ""):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-footnote">{footnote}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_airport_mini_card(airport: str, flights: int | None, avg_delay: float | None, color: str):
    if flights is None:
        st.markdown(
            f"""
            <div class="airport-mini-card">
                <div class="airport-mini-title">{airport}</div>
                <div style="color:#6b7280;">No data for current filters.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    delay_text = "n/a" if avg_delay is None or pd.isna(avg_delay) else f"{avg_delay:.1f} min avg dep delay"
    st.markdown(
        f"""
        <div class="airport-mini-card">
            <div class="airport-mini-title">{airport}</div>
            <div class="airport-mini-main">{flights:,} flights</div>
            <span class="airport-pill" style="background-color:{color};">{delay_text}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_filter_context(origins: list[str], dest_filter: str | None, months: list[int], use_specific_day: bool, day_params: list[int]) -> str:
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


# ---------------------------------------------------
# Filter options
# ---------------------------------------------------

@st.cache_data
def get_destinations():
    df = query_df(
        """
        SELECT DISTINCT dest
        FROM flights
        WHERE dest IS NOT NULL
        ORDER BY dest
        """
    )
    return df["dest"].dropna().tolist()


# ---------------------------------------------------
# Overview queries
# ---------------------------------------------------

@st.cache_data
def get_overview_metrics(origins: list[str], months: list[int], dest: str | None, day_sql: str, day_params: list) -> dict:
    o_ph = build_ph(origins)
    m_ph = build_ph(months)

    dest_sql = ""
    params = [*origins, *months]
    params.extend(day_params)

    if dest is not None:
        dest_sql = "AND dest = ?"
        params.append(dest)

    df = query_df(
        f"""
        SELECT
            COUNT(*) AS total_flights,
            COUNT(DISTINCT dest) AS unique_destinations,
            COUNT(DISTINCT carrier) AS unique_airlines,
            AVG(CASE WHEN dep_delay IS NOT NULL THEN dep_delay END) AS avg_dep_delay,
            AVG(CASE WHEN arr_delay IS NOT NULL THEN arr_delay END) AS avg_arr_delay
        FROM flights
        WHERE origin IN ({o_ph})
          AND month IN ({m_ph})
          {day_sql}
          {dest_sql};
        """,
        params=tuple(params)
    )
    return df.iloc[0].to_dict()


@st.cache_data
def get_busiest_route(origins: list[str], months: list[int], dest: str | None, day_sql: str, day_params: list):
    o_ph = build_ph(origins)
    m_ph = build_ph(months)

    dest_sql = ""
    params = [*origins, *months]
    params.extend(day_params)

    if dest is not None:
        dest_sql = "AND dest = ?"
        params.append(dest)

    df = query_df(
        f"""
        SELECT
            origin,
            dest,
            COUNT(*) AS flights
        FROM flights
        WHERE origin IN ({o_ph})
          AND month IN ({m_ph})
          {day_sql}
          {dest_sql}
        GROUP BY origin, dest
        ORDER BY flights DESC
        LIMIT 1;
        """,
        params=tuple(params)
    )

    if df.empty:
        return "N/A", 0

    row = df.iloc[0]
    return f"{row['origin']} → {row['dest']}", int(row["flights"])


@st.cache_data
def get_airport_kpis(origins: list[str], months: list[int], dest: str | None, day_sql: str, day_params: list) -> pd.DataFrame:
    o_ph = build_ph(origins)
    m_ph = build_ph(months)

    dest_sql = ""
    params = [*origins, *months]
    params.extend(day_params)

    if dest is not None:
        dest_sql = "AND dest = ?"
        params.append(dest)

    return query_df(
        f"""
        SELECT
            origin,
            COUNT(*) AS total_flights,
            AVG(CASE WHEN dep_delay IS NOT NULL THEN dep_delay END) AS avg_dep_delay
        FROM flights
        WHERE origin IN ({o_ph})
          AND month IN ({m_ph})
          {day_sql}
          {dest_sql}
        GROUP BY origin
        ORDER BY origin;
        """,
        params=tuple(params)
    )


@st.cache_data
def fig_top_destinations_filtered(origins: list[str], months: list[int], day_sql: str, day_params: list, n: int = 10):
    o_ph = build_ph(origins)
    m_ph = build_ph(months)

    params = [*origins, *months]
    params.extend(day_params)

    df = query_df(
        f"""
        SELECT
            dest,
            COUNT(*) AS flight_count
        FROM flights
        WHERE origin IN ({o_ph})
          AND month IN ({m_ph})
          {day_sql}
        GROUP BY dest
        ORDER BY flight_count DESC
        LIMIT ?;
        """,
        params=tuple([*params, n])
    )

    fig = px.bar(
        df,
        x="dest",
        y="flight_count",
        title=f"Top {n} destinations",
        labels={"dest": "Destination", "flight_count": "Flights"},
        color_discrete_sequence=[BLUE_MAIN],
    )
    fig.update_xaxes(tickangle=45)
    return style_fig(fig, height=420, showlegend=False)


@st.cache_data
def fig_delay_by_month(origins: list[str], months: list[int], dest: str | None, day_sql: str, day_params: list):
    o_ph = build_ph(origins)
    m_ph = build_ph(months)

    dest_sql = ""
    params = [*origins, *months]
    params.extend(day_params)

    if dest is not None:
        dest_sql = "AND dest = ?"
        params.append(dest)

    df = query_df(
        f"""
        SELECT
            month,
            ROUND(AVG(CASE WHEN dep_delay IS NOT NULL THEN dep_delay END), 2) AS avg_dep_delay
        FROM flights
        WHERE origin IN ({o_ph})
          AND month IN ({m_ph})
          {day_sql}
          {dest_sql}
        GROUP BY month
        ORDER BY month;
        """,
        params=tuple(params)
    )

    month_map = {i + 1: MONTH_LABELS[i] for i in range(12)}
    df["month_label"] = df["month"].map(month_map)

    fig = px.bar(
        df,
        x="month_label",
        y="avg_dep_delay",
        title="Average departure delay by month",
        labels={"month_label": "Month", "avg_dep_delay": "Avg departure delay (min)"},
        color_discrete_sequence=[BLUE_DARK],
    )
    return style_fig(fig, height=420, showlegend=False)


@st.cache_data
def get_selected_day_stats(origin: str, chosen_date):
    return flight_stats_for_day(origin, int(chosen_date.month), int(chosen_date.day))


@st.cache_data
def fig_destinations_for_selected_day(origin: str, chosen_date):
    fig = plot_destinations_for_day(
        origin,
        int(chosen_date.month),
        int(chosen_date.day),
        limit=50
    )
    fig.update_layout(height=750, margin=dict(l=20, r=20, t=60, b=20))
    return fig


@st.cache_data
def get_plane_types_route_filtered(origin: str, dest: str, months: list[int], day_sql: str, day_params: list) -> pd.DataFrame:
    m_ph = build_ph(months)
    day_sql_f = build_day_sql_for_alias(day_sql, "f")

    df = query_df(
        f"""
        SELECT
            COALESCE(NULLIF(TRIM(p.type), ''), 'Unknown') AS plane_type,
            COUNT(*) AS count
        FROM flights f
        LEFT JOIN planes p
            ON p.tailnum = f.tailnum
        WHERE f.origin = ?
          AND f.dest = ?
          AND f.month IN ({m_ph})
          {day_sql_f}
        GROUP BY plane_type
        ORDER BY count DESC
        """,
        params=tuple([origin, dest, *months, *day_params])
    )
    return df


# ---------------------------------------------------
# Main
# ---------------------------------------------------

def main():
    st.title("NYC Flights Dashboard")

    # ----------------------------
    # Sidebar filters
    # ----------------------------
    st.sidebar.header("Filters")

    origin_choice = st.sidebar.selectbox(
        "Departure airport",
        ["All NYC", "JFK", "LGA", "EWR"],
        index=0
    )

    origins = NYC_AIRPORTS if origin_choice == "All NYC" else [origin_choice]

    destinations = get_destinations()
    dest_choice = st.sidebar.selectbox(
        "Arrival airport",
        ["All destinations"] + destinations
    )
    dest_filter = None if dest_choice == "All destinations" else dest_choice

    st.sidebar.subheader("Date")
    use_specific_day = st.sidebar.checkbox("Filter to a specific day", value=False)

    day_sql = ""
    day_params: list = []

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
                default=MONTH_LABELS
            )

        months = [MONTH_TO_NUM[m] for m in selected_months]
        if not months:
            st.warning("Select at least one month.")
            st.stop()

    context_text = format_filter_context(origins, dest_filter, months, use_specific_day, day_params)

    st.markdown(
        f"""
        <div class="intro-box">
            <div class="intro-title">General Overview</div>
            <div class="intro-text">
                This page gives a broad overview of NYC flight activity, including traffic volume,
                destination patterns, delays, selected routes, aircraft usage, and daily route maps.
                It is designed as the starting point for exploring the dashboard.
            </div>
            <div class="filter-row">
                <div class="intro-note">{context_text}</div>
                <div class="intro-note-secondary">Interactive filters: departure airport, arrival airport, month, specific day</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ----------------------------
    # Flight overview
    # ----------------------------
    section_open(
        "Flight Overview",
        "These KPIs summarize the selected slice of the dataset and highlight the overall scale and delay profile."
    )

    m = get_overview_metrics(origins, months, dest_filter, day_sql, day_params)
    route, busiest_route_flights = get_busiest_route(origins, months, dest_filter, day_sql, day_params)

    c1, c2, c3 = st.columns(3, gap="large")
    c4, c5, c6 = st.columns(3, gap="large")

    with c1:
        kpi_card("Total flights", f"{int(m['total_flights']):,}", "Flights in the current filtered view")
    with c2:
        kpi_card("Unique destinations", f"{int(m['unique_destinations']):,}", "Distinct destination airports reached")
    with c3:
        kpi_card("Unique airlines", f"{int(m['unique_airlines']):,}", "Carriers present in the filtered sample")
    with c4:
        kpi_card(
            "Avg departure delay",
            f"{m['avg_dep_delay']:.1f}" if m["avg_dep_delay"] is not None else "n/a",
            "Minutes"
        )
    with c5:
        kpi_card(
            "Avg arrival delay",
            f"{m['avg_arr_delay']:.1f}" if m["avg_arr_delay"] is not None else "n/a",
            "Minutes"
        )
    with c6:
        kpi_card("Busiest route", route, f"{busiest_route_flights:,} flights" if busiest_route_flights else "No route data")

    insight_box(
        f"The busiest route in the current view is <b>{route}</b>. This summary helps identify whether the selected slice is broad and representative or narrow and route-specific."
    )

    section_close()

    # ----------------------------
    # Flights by origin airport
    # ----------------------------
    section_open(
        "Flights by Origin Airport",
        "This section compares the selected NYC departure airports by traffic volume and average departure delay."
    )

    airport_df = get_airport_kpis(origins, months, dest_filter, day_sql, day_params).set_index("origin")

    a1, a2, a3 = st.columns(3, gap="large")
    delays = airport_df["avg_dep_delay"].to_dict() if not airport_df.empty else {}
    palette = [BLUE_LIGHT, BLUE_MAIN, BLUE_DARK]
    sorted_airports = sorted(delays, key=lambda k: (delays[k] is None, delays[k]))
    color_map = {ap: palette[min(i, len(palette) - 1)] for i, ap in enumerate(sorted_airports)}

    for col, ap in zip([a1, a2, a3], NYC_AIRPORTS):
        if ap not in airport_df.index:
            with col:
                render_airport_mini_card(ap, None, None, "#cccccc")
            continue

        flights_ap = int(airport_df.loc[ap, "total_flights"])
        val = airport_df.loc[ap, "avg_dep_delay"]
        color = color_map.get(ap, BLUE_MAIN)

        with col:
            render_airport_mini_card(ap, flights_ap, val, color)

    if not airport_df.empty:
        top_volume_airport = airport_df.sort_values("total_flights", ascending=False).index[0]
        top_delay_airport = airport_df.sort_values("avg_dep_delay", ascending=False).index[0]
        insight_box(
            f"<b>{top_volume_airport}</b> handles the most traffic in the current filters, while <b>{top_delay_airport}</b> has the highest average departure delay."
        )

    section_close()

    # ----------------------------
    # Flight patterns
    # ----------------------------
    section_open(
        "Flight Patterns",
        "These charts show destination popularity and average departure delay by month. For the top destinations chart, the arrival-airport filter is intentionally not applied."
    )

    left, right = st.columns(2, gap="large")

    with left:
        fig = fig_top_destinations_filtered(origins, months, day_sql, day_params)
        show_fig(fig)

    with right:
        fig = fig_delay_by_month(origins, months, dest_filter, day_sql, day_params)
        show_fig(fig)

    section_close()

    # ----------------------------
    # Selected route summary
    # ----------------------------
    section_open(
        "Selected Route Summary",
        "This section shows route-specific statistics and aircraft types when one departure airport and one arrival airport are selected."
    )

    if len(origins) == 1 and dest_filter is not None:
        selected_origin = origins[0]
        m_ph = build_ph(months)

        route_kpi = query_df(
            f"""
            SELECT
                COUNT(*) AS total_flights,
                ROUND(AVG(dep_delay), 2) AS avg_dep_delay,
                ROUND(AVG(arr_delay), 2) AS avg_arr_delay,
                COUNT(DISTINCT carrier) AS airlines
            FROM flights
            WHERE origin = ?
              AND dest = ?
              AND month IN ({m_ph})
              {day_sql}
            """,
            params=tuple([selected_origin, dest_filter, *months, *day_params])
        ).iloc[0]

        route_cols = st.columns(4, gap="large")
        route_cols[0].metric("Route", f"{selected_origin} → {dest_filter}")
        route_cols[1].metric("Flights", f"{int(route_kpi['total_flights']):,}")
        route_cols[2].metric(
            "Avg dep delay (min)",
            f"{route_kpi['avg_dep_delay']:.1f}" if route_kpi["avg_dep_delay"] is not None else "n/a"
        )
        route_cols[3].metric(
            "Avg arr delay (min)",
            f"{route_kpi['avg_arr_delay']:.1f}" if route_kpi["avg_arr_delay"] is not None else "n/a"
        )

        st.markdown("#### Plane types for selected route")

        plane_df = get_plane_types_route_filtered(selected_origin, dest_filter, months, day_sql, day_params)

        if plane_df.empty:
            st.info("No plane type information found for this route.")
        else:
            c1, c2 = st.columns([1, 1.2], gap="large")

            with c1:
                display_plane_df = plane_df.rename(columns={"plane_type": "Plane type", "count": "Flights"}).copy()
                display_plane_df["Flights"] = display_plane_df["Flights"].map(lambda x: f"{int(x):,}")
                st.dataframe(display_plane_df, use_container_width=True, hide_index=True)

            with c2:
                fig_plane = px.bar(
                    plane_df.head(10).sort_values("count", ascending=True),
                    x="count",
                    y="plane_type",
                    orientation="h",
                    title=f"Plane types used on {selected_origin} → {dest_filter}",
                    labels={"count": "Flights", "plane_type": "Plane type"},
                    color_discrete_sequence=[BLUE_MAIN],
                )
                style_fig(fig_plane, height=420, showlegend=False)
                show_fig(fig_plane)

            top_plane = plane_df.iloc[0]
            insight_box(
                f"The most common aircraft type on <b>{selected_origin} → {dest_filter}</b> is <b>{top_plane['plane_type']}</b>, with <b>{int(top_plane['count']):,}</b> flights."
            )

    else:
        st.info("Select one departure airport and one arrival airport to see route-specific plane types.")

    section_close()

    # ----------------------------
    # Daily statistics and route map
    # ----------------------------
    section_open(
        "Daily Statistics and Route Map",
        "When a specific day is selected, this section shows daily KPIs and a destination route map."
    )

    if use_specific_day:
        if len(origins) == 1:
            selected_origin = origins[0]

            try:
                day_stats = get_selected_day_stats(selected_origin, chosen_date)

                d1, d2, d3, d4 = st.columns(4, gap="large")
                d1.metric("Flights that day", f"{day_stats['total_flights']:,}")
                d2.metric("Unique destinations", f"{day_stats['unique_destinations']:,}")
                d3.metric("Most visited destination", day_stats["most_visited_dest"] or "n/a")
                d4.metric("Flights to top destination", f"{day_stats['most_visited_count']:,}")

                fig_map = fig_destinations_for_selected_day(selected_origin, chosen_date)
                show_fig(fig_map)

                insight_box(
                    f"On {chosen_date.strftime('%d-%m-%Y')}, <b>{selected_origin}</b> reached <b>{day_stats['unique_destinations']:,}</b> destinations. "
                    f"The map helps show how concentrated or spread the day’s traffic was."
                )

            except Exception as e:
                st.info("Could not generate daily route statistics/map for the selected date.")
                st.caption(f"Details: {e}")
        else:
            st.info("Select a single departure airport and a specific day to show the daily route map.")
    else:
        st.info("Turn on 'Filter to a specific day' in the sidebar to see daily statistics and the route map.")

    section_close()


if __name__ == "__main__":
    main()