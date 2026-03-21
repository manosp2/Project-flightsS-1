import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st
import plotly.express as px

from part3.db import query_df
from part5.dashboard_features.weather_analysis_features import (
    get_filter_options,
    MONTH_LABELS,
    MONTH_TO_NUM,
    get_wind_effect_df,
    get_weather_delay_df,
    build_density_figure,
    build_box_figure,
    build_scatter_figure,
    wind_stats_table,
    build_corr_heatmap,
    build_bad_weather_boxplot,
    get_wind_conclusion_stats,
    get_bad_weather_stats,
)

st.set_page_config(page_title="Weather Analysis", layout="wide")

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

st.markdown(
    f"""
    <style>
        .stApp {{
            background-color: {BG};
        }}

        .block-container {{
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1300px;
        }}

        h1, h2, h3 {{
            color: #000000 !important;
        }}

        .intro-box {{
            background: #ffffff;
            padding: 1.4rem 1.6rem;
            border-radius: 16px;
            border: 1px solid {CARD_BORDER};
            box-shadow: 0 4px 18px rgba(91, 33, 182, 0.10);
            margin-bottom: 1.2rem;
        }}

        .intro-title {{
            font-size: 1.15rem;
            font-weight: 700;
            color: #1f2a44;
            margin-bottom: 0.35rem;
        }}

        .intro-text {{
            font-size: 1rem;
            color: #374151;
            line-height: 1.65;
        }}

        .filter-row {{
            margin-top: 0.8rem;
            display: flex;
            gap: 0.6rem;
            flex-wrap: wrap;
        }}

        .intro-note {{
            display: inline-block;
            background: {BLUE_MAIN};
            color: #ffffff;
            padding: 0.4rem 0.75rem;
            border-radius: 999px;
            font-size: 0.88rem;
            font-weight: 600;
        }}

        .intro-note-secondary {{
            display: inline-block;
            background: #e5e7eb;
            color: #374151;
            padding: 0.4rem 0.75rem;
            border-radius: 999px;
            font-size: 0.88rem;
            font-weight: 600;
        }}

        .section-box {{
            background: #ffffff;
            border: 1px solid {CARD_BORDER};
            border-top: 4px solid {BLUE_MAIN};
            border-radius: 14px;
            padding: 1.2rem 1.2rem 0.9rem 1.2rem;
            box-shadow: 0 4px 24px rgba(91, 33, 182, 0.10);
            margin-bottom: 1.4rem;
        }}

        .section-title {{
            font-size: 1.45rem;
            font-weight: 700;
            color: #1f2a44;
            margin-bottom: 0.25rem;
        }}

        .section-subtitle {{
            color: #667085;
            font-size: 0.96rem;
            margin-bottom: 0.9rem;
            line-height: 1.55;
        }}

        .insight-box {{
            background: #ffffff;
            border-left: 4px solid #5b21b6;
            padding: 0.9rem 1rem;
            border-radius: 10px;
            color: {PRIMARY};
            margin-top: 0.8rem;
            margin-bottom: 0.3rem;
            line-height: 1.6;
        }}

        section[data-testid="stSidebar"] {{
            background: #ffffff;
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

        div[data-testid="stRadio"] > div {{
            gap: 0.6rem;
        }}

                div[data-testid="stDataFrame"] {{
            background: #ffffff;
            border: 1px solid {CARD_BORDER};
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 18px rgba(91, 33, 182, 0.08);
        }}

    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def get_filter_options_cached():
    return get_filter_options()


@st.cache_data
def get_wind_effect_df_cached(origins, months, dest_filter, day_sql, day_params):
    return get_wind_effect_df(origins, months, dest_filter, day_sql, day_params)


@st.cache_data
def get_weather_delay_df_cached(origins, months, dest_filter, day_sql, day_params):
    return get_weather_delay_df(origins, months, dest_filter, day_sql, day_params)


@st.cache_data
def get_daily_weather_summary(origins, months, dest_filter, day_sql, day_params):
    origin_ph = ",".join(["?"] * len(origins))
    month_ph = ",".join(["?"] * len(months))

    params = list(origins) + list(months)
    dest_sql = ""

    if dest_filter is not None:
        dest_sql = "AND f.dest = ?"
        params.append(dest_filter)

    params.extend(day_params)

    query = f"""
        SELECT
            f.year,
            f.month,
            f.day,
            ROUND(AVG(f.dep_delay), 2) AS avg_dep_delay,
            ROUND(AVG(f.arr_delay), 2) AS avg_arr_delay,
            ROUND(AVG(w.wind_speed), 2) AS avg_wind_speed,
            ROUND(AVG(w.precip), 2) AS avg_precip,
            ROUND(AVG(w.visib), 2) AS avg_visibility,
            COUNT(*) AS flights
        FROM flights f
        JOIN weather w
            ON f.origin = w.origin
           AND f.year = w.year
           AND f.month = w.month
           AND f.day = w.day
           AND CAST(f.hour AS INTEGER) = CAST(w.hour AS INTEGER)
        WHERE f.origin IN ({origin_ph})
          AND f.month IN ({month_ph})
          {dest_sql}
          {day_sql}
        GROUP BY f.year, f.month, f.day
        ORDER BY f.year, f.month, f.day
    """
    return query_df(query, tuple(params))


@st.cache_data
def get_visibility_delay_df(origins, months, dest_filter, day_sql, day_params):
    origin_ph = ",".join(["?"] * len(origins))
    month_ph = ",".join(["?"] * len(months))

    params = list(origins) + list(months)
    dest_sql = ""

    if dest_filter is not None:
        dest_sql = "AND f.dest = ?"
        params.append(dest_filter)

    params.extend(day_params)

    query = f"""
        SELECT
            w.visib AS visibility,
            f.arr_delay
        FROM flights f
        JOIN weather w
            ON f.origin = w.origin
           AND f.year = w.year
           AND f.month = w.month
           AND f.day = w.day
           AND CAST(f.hour AS INTEGER) = CAST(w.hour AS INTEGER)
        WHERE f.origin IN ({origin_ph})
          AND f.month IN ({month_ph})
          {dest_sql}
          {day_sql}
          AND w.visib IS NOT NULL
          AND f.arr_delay IS NOT NULL
    """
    return query_df(query, tuple(params))


@st.cache_data
def get_windspeed_delay_df(origins, months, dest_filter, day_sql, day_params):
    origin_ph = ",".join(["?"] * len(origins))
    month_ph = ",".join(["?"] * len(months))

    params = list(origins) + list(months)
    dest_sql = ""

    if dest_filter is not None:
        dest_sql = "AND f.dest = ?"
        params.append(dest_filter)

    params.extend(day_params)

    query = f"""
        SELECT
            w.wind_speed,
            f.dep_delay
        FROM flights f
        JOIN weather w
            ON f.origin = w.origin
           AND f.year = w.year
           AND f.month = w.month
           AND f.day = w.day
           AND CAST(f.hour AS INTEGER) = CAST(w.hour AS INTEGER)
        WHERE f.origin IN ({origin_ph})
          AND f.month IN ({month_ph})
          {dest_sql}
          {day_sql}
          AND w.wind_speed IS NOT NULL
          AND f.dep_delay IS NOT NULL
    """
    return query_df(query, tuple(params))


@st.cache_data
def get_selected_day_weather_impact(origins, dest_filter, chosen_date):
    origin_ph = ",".join(["?"] * len(origins))

    params = list(origins)
    dest_sql = ""

    if dest_filter is not None:
        dest_sql = "AND f.dest = ?"
        params.append(dest_filter)

    params.extend([chosen_date.year, chosen_date.month, chosen_date.day])

    query = f"""
        SELECT
            CAST(f.hour AS INTEGER) AS hour,
            ROUND(AVG(f.dep_delay), 2) AS avg_dep_delay,
            ROUND(AVG(w.wind_speed), 2) AS avg_wind_speed,
            ROUND(AVG(w.precip), 2) AS avg_precip,
            ROUND(AVG(w.visib), 2) AS avg_visibility,
            COUNT(*) AS flights
        FROM flights f
        JOIN weather w
            ON f.origin = w.origin
           AND f.year = w.year
           AND f.month = w.month
           AND f.day = w.day
           AND CAST(f.hour AS INTEGER) = CAST(w.hour AS INTEGER)
        WHERE f.origin IN ({origin_ph})
          {dest_sql}
          AND f.year = ?
          AND f.month = ?
          AND f.day = ?
        GROUP BY CAST(f.hour AS INTEGER)
        ORDER BY hour
    """
    return query_df(query, tuple(params))


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


def insight_box(text):
    st.markdown(f"<div class='insight-box'>{text}</div>", unsafe_allow_html=True)


def format_filter_context(origins, dest_filter, months, chosen_date):
    origin_text = "all NYC departure airports" if len(origins) == 3 else origins[0]
    dest_text = "all destinations" if dest_filter is None else dest_filter

    if chosen_date is not None:
        date_text = f"{chosen_date.day:02d}-{chosen_date.month:02d}-{chosen_date.year}"
    elif len(months) == 12:
        date_text = "the full year"
    else:
        month_names = [MONTH_LABELS[m - 1] for m in months]
        date_text = ", ".join(month_names) if len(month_names) <= 3 else f"{len(month_names)} selected months"

    return f"Current view: {origin_text} → {dest_text}, filtered to {date_text}."


def build_filters():
    st.sidebar.header("Filters")

    origin_choice = st.sidebar.selectbox(
        "Departure airport",
        ["All NYC", "JFK", "LGA", "EWR"],
        index=0
    )
    origins = ["JFK", "LGA", "EWR"] if origin_choice == "All NYC" else [origin_choice]

    destinations = get_filter_options_cached()
    dest_choice = st.sidebar.selectbox(
        "Arrival airport",
        ["All destinations"] + destinations
    )
    dest_filter = None if dest_choice == "All destinations" else dest_choice

    st.sidebar.subheader("Date")
    use_specific_day = st.sidebar.checkbox("Filter to a specific day", value=False)

    chosen_date = None
    day_sql = ""
    day_params = []

    if use_specific_day:
        chosen_date = st.sidebar.date_input(
            "Select date",
            value=pd.to_datetime("2023-01-01"),
            min_value=pd.to_datetime("2023-01-01"),
            max_value=pd.to_datetime("2023-12-31"),
        )
        day_sql = "AND f.year = ? AND f.month = ? AND f.day = ?"
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
                "Select months",
                MONTH_LABELS,
                default=MONTH_LABELS
            )

        months = [MONTH_TO_NUM[m] for m in selected_months]
        if not months:
            st.warning("Select at least one month.")
            st.stop()

    return tuple(origins), dest_filter, tuple(months), day_sql, tuple(day_params), chosen_date

def style_plot(fig, height=500):
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(t=70, l=20, r=20, b=20),
        height=height,
        font=dict(color=PRIMARY, size=14),
        title_font=dict(size=16, color=PRIMARY),
        title_x=0.03,
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="#edf2f7", zeroline=False)
    return fig


def main():
    origins, dest_filter, months, day_sql, day_params, chosen_date = build_filters()
    filter_context = format_filter_context(origins, dest_filter, months, chosen_date)

    st.title("NYC Flights Dashboard")

    st.markdown(
        f"""
        <div class="intro-box">
            <div class="intro-title"> Weather Analysis</div>
            <div class="intro-text">
                Explore how wind and weather conditions relate to airtime, delays, and broader
                flight performance patterns across NYC flights.
            </div>
            <div class="filter-row">
                <div class="intro-note">{filter_context}</div>
                <div class="intro-note-secondary">Interactive filters: departure airport, arrival airport, months, specific day</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    section_open(
        "Wind Effect and Air Time",
        "Compare how headwinds and tailwinds relate to normalized air time using different visual views.",
    )

    with st.spinner("Loading wind effect analysis..."):
        wind_df = get_wind_effect_df_cached(
            origins,
            months,
            dest_filter,
            day_sql,
            day_params,
        )

    if wind_df.empty:
        st.info("No wind-effect data available for the selected filters.")
        st.stop()

    viz_choice = st.radio(
        "Select visualization",
        ["Density Plot", "Box Plot", "Scatter Plot"],
        index=0,
        horizontal=True,
    )

    if viz_choice == "Density Plot":
        fig = build_density_figure(wind_df)
        st.plotly_chart(style_plot(fig, 500), use_container_width=True)

    elif viz_choice == "Box Plot":
        fig = build_box_figure(wind_df)
        st.plotly_chart(style_plot(fig, 500), use_container_width=True)

    else:
        fig = build_scatter_figure(wind_df)
        st.plotly_chart(style_plot(fig, 500), use_container_width=True)
        st.caption("The scatter plot focuses on stronger wind-effect cases so the headwind vs tailwind pattern is easier to see.")

    wind_stats = get_wind_conclusion_stats(wind_df)

    insight_box(
        f"Headwind flights average <b>{wind_stats['head_mean']:.1f}</b> minutes per 100 miles, "
        f"while tailwind flights average <b>{wind_stats['tail_mean']:.1f}</b>. "
        f"That is a difference of about <b>{wind_stats['pct_diff']:.1f}%</b>. "
        f"The correlation between wind effect and normalized airtime is <b>{wind_stats['overall_corr']:.2f}</b>."
    )

    section_close()

    section_open(
        "Air Time Statistics by Wind Condition",
        "Summary statistics for headwind and tailwind flights in the current filtered view.",
    )

    stats_df = wind_stats_table(wind_df)

    st.dataframe(
        stats_df,
        use_container_width=True,
        hide_index=True,
    )

    section_close()

    section_open(
        "Weather Severity and Delays",
        "Examine how weather variables and broader bad-weather conditions relate to departure and arrival delays.",
    )

    weather_df = get_weather_delay_df_cached(
        origins,
        months,
        dest_filter,
        day_sql,
        day_params,
    )

    if weather_df.empty:
        st.info("No weather-delay data available for the selected filters.")
    else:
        fig_corr = build_corr_heatmap(weather_df)
        fig_corr.update_layout(title="Correlation between weather variables and delays")
        st.plotly_chart(style_plot(fig_corr, 500), use_container_width=True)

        bad_weather_stats = get_bad_weather_stats(weather_df)

        insight_box(
            f"Departure and arrival delays move together fairly strongly "
            f"(<b>corr = {bad_weather_stats['dep_arr_corr']:.2f}</b>), while most individual weather variables show weaker direct relationships with delays."
        )

        fig_box = build_bad_weather_boxplot(weather_df)
        fig_box.update_layout(title="Arrival delay in normal vs bad weather conditions")
        st.plotly_chart(style_plot(fig_box, 500), use_container_width=True)

        insight_box(
            f"The median arrival delay shifts from <b>{bad_weather_stats['median_normal']:.1f} min</b> "
            f"in normal conditions to <b>{bad_weather_stats['median_bad']:.1f} min</b> in bad-weather conditions. "
            f"The overall correlation between bad weather and arrival delay is <b>{bad_weather_stats['corr_bad']:.2f}</b>."
        )

        st.markdown(
            """
            <div class="insight-box">
                A negative arrival delay means the flight arrived earlier than scheduled.
            </div>
            """,
            unsafe_allow_html=True,
        )

    section_close()

    section_open(
        "Daily Weather Patterns",
        "Explore daily delay and weather trends, then compare delay levels across visibility and wind groups.",
    )

    daily_df = get_daily_weather_summary(origins, months, dest_filter, day_sql, day_params)

    if not daily_df.empty:
        daily_df["date"] = pd.to_datetime(
            dict(
                year=daily_df["year"],
                month=daily_df["month"],
                day=daily_df["day"]
            )
        )

        daily_df = daily_df.sort_values("date")

        numeric_cols = [
            "avg_dep_delay",
            "avg_arr_delay",
            "avg_wind_speed",
            "avg_precip",
            "avg_visibility",
            "flights",
        ]
        for col in numeric_cols:
            daily_df[col] = pd.to_numeric(daily_df[col], errors="coerce")

        # 14-day smoothing
        daily_df["dep_trend"] = daily_df["avg_dep_delay"].rolling(14, min_periods=1).mean()
        daily_df["arr_trend"] = daily_df["avg_arr_delay"].rolling(14, min_periods=1).mean()
        daily_df["wind_trend"] = daily_df["avg_wind_speed"].rolling(14, min_periods=1).mean()
        daily_df["precip_trend"] = daily_df["avg_precip"].rolling(14, min_periods=1).mean()
        daily_df["visibility_trend"] = daily_df["avg_visibility"].rolling(14, min_periods=1).mean()

        c1, c2 = st.columns(2)

        with c1:
            fig_daily_delay = px.line(
                daily_df,
                x="date",
                y=["avg_dep_delay", "avg_arr_delay"],
                title="Daily delay trend",
                labels={
                    "date": "Date",
                    "value": "Delay (minutes)",
                    "variable": "",
                },
                color_discrete_map={
                    "avg_dep_delay": BLUE_DARK,
                    "avg_arr_delay": BLUE_MAIN,
                },
            )

            fig_daily_delay.data[0].name = "Average departure delay"
            fig_daily_delay.data[1].name = "Average arrival delay"
            fig_daily_delay.data[0].line.width = 1.5
            fig_daily_delay.data[1].line.width = 1.5

            fig_daily_delay.add_scatter(
                x=daily_df["date"],
                y=daily_df["dep_trend"],
                mode="lines",
                name="Departure delay trend",
                line=dict(color=BLUE_DARK, width=4),
            )
            fig_daily_delay.add_scatter(
                x=daily_df["date"],
                y=daily_df["arr_trend"],
                mode="lines",
                name="Arrival delay trend",
                line=dict(color=BLUE_MAIN, width=4, dash="dot"),
            )

            st.plotly_chart(style_plot(fig_daily_delay, 450), use_container_width=True)

        with c2:
            fig_daily_weather = px.line(
                daily_df,
                x="date",
                y=["avg_wind_speed", "avg_precip", "avg_visibility"],
                title="Daily weather trend",
                labels={
                    "date": "Date",
                    "value": "Value",
                    "variable": "",
                },
                color_discrete_map={
                    "avg_wind_speed": BLUE_DARK,
                    "avg_precip": BLUE_MAIN,
                    "avg_visibility": BLUE_LIGHT,
                },
            )

            fig_daily_weather.data[0].name = "Average wind speed"
            fig_daily_weather.data[1].name = "Average precipitation"
            fig_daily_weather.data[2].name = "Average visibility"
            fig_daily_weather.data[0].line.width = 1.5
            fig_daily_weather.data[1].line.width = 1.5
            fig_daily_weather.data[2].line.width = 1.5

            fig_daily_weather.add_scatter(
                x=daily_df["date"],
                y=daily_df["wind_trend"],
                mode="lines",
                name="Wind speed trend",
                line=dict(color=BLUE_DARK, width=4),
            )
            fig_daily_weather.add_scatter(
                x=daily_df["date"],
                y=daily_df["precip_trend"],
                mode="lines",
                name="Precipitation trend",
                line=dict(color=BLUE_MAIN, width=4, dash="dot"),
            )
            fig_daily_weather.add_scatter(
                x=daily_df["date"],
                y=daily_df["visibility_trend"],
                mode="lines",
                name="Visibility trend",
                line=dict(color=BLUE_LIGHT, width=4, dash="dash"),
            )

            st.plotly_chart(style_plot(fig_daily_weather, 450), use_container_width=True)

        worst_days = daily_df.sort_values("avg_arr_delay", ascending=False).head(10)[
            ["date", "avg_dep_delay", "avg_arr_delay", "avg_wind_speed", "avg_precip", "avg_visibility", "flights"]
        ].copy()

        worst_days["date"] = worst_days["date"].dt.date

        st.subheader("Highest-delay days in the current filtered view")
        st.dataframe(worst_days, use_container_width=True, hide_index=True)

        if not worst_days.empty:
            top_day = worst_days.iloc[0]
            insight_box(
                f"The highest-delay day in the current filtered view was <b>{top_day['date']}</b>, "
                f"with average arrival delay of <b>{top_day['avg_arr_delay']:.1f} min</b>."
            )
    else:
        st.info("No daily weather summary data available for the selected filters.")

    vis_df = get_visibility_delay_df(origins, months, dest_filter, day_sql, day_params)
    if not vis_df.empty:
        vis_df = vis_df.copy()

        vis_df["visibility_group"] = pd.cut(
            vis_df["visibility"],
            bins=[-0.01, 2, 5, 8, 100],
            labels=["Poor (<2 mi)", "Low (2–5 mi)", "Moderate (5–8 mi)", "Good (>8 mi)"]
        )

        vis_df = vis_df.dropna(subset=["visibility_group", "arr_delay"])

        fig_vis = px.box(
            vis_df,
            x="visibility_group",
            y="arr_delay",
            color="visibility_group",
            title="Arrival delay vs visibility category",
            labels={
                "visibility_group": "Visibility category",
                "arr_delay": "Arrival delay (minutes)"
            },
            category_orders={
                "visibility_group": ["Poor (<2 mi)", "Low (2–5 mi)", "Moderate (5–8 mi)", "Good (>8 mi)"]
            },
            color_discrete_map={
                "Poor (<2 mi)": BLUE_DARK,
                "Low (2–5 mi)": BLUE_MAIN,
                "Moderate (5–8 mi)": BLUE_MID,
                "Good (>8 mi)": BLUE_LIGHT,
            },
            points=False
        )

        fig_vis.update_layout(showlegend=False)
        st.plotly_chart(style_plot(fig_vis, 500), use_container_width=True)

    ws_df = get_windspeed_delay_df(origins, months, dest_filter, day_sql, day_params)
    if not ws_df.empty:
        ws_df = ws_df.copy()

        ws_df["wind_group"] = pd.cut(
            ws_df["wind_speed"],
            bins=[-0.01, 10, 20, 30, 100],
            labels=["Calm (<10 mph)", "Moderate (10–20 mph)", "Strong (20–30 mph)", "Severe (30+ mph)"]
        )

        ws_df = ws_df.dropna(subset=["wind_group", "dep_delay"])

        fig_ws = px.box(
            ws_df,
            x="wind_group",
            y="dep_delay",
            color="wind_group",
            title="Departure delay vs wind speed category",
            labels={
                "wind_group": "Wind speed category",
                "dep_delay": "Departure delay (minutes)"
            },
            category_orders={
                "wind_group": ["Calm (<10 mph)", "Moderate (10–20 mph)", "Strong (20–30 mph)", "Severe (30+ mph)"]
            },
            color_discrete_map={
                "Calm (<10 mph)": BLUE_LIGHT,
                "Moderate (10–20 mph)": BLUE_MID,
                "Strong (20–30 mph)": BLUE_MAIN,
                "Severe (30+ mph)": BLUE_DARK,
            },
            points=False
        )

        fig_ws.update_layout(showlegend=False)
        st.plotly_chart(style_plot(fig_ws, 500), use_container_width=True)

    if chosen_date is not None:
        st.subheader(f"Selected Day Weather Insight: {chosen_date}")

        day_df = get_selected_day_weather_impact(origins, dest_filter, chosen_date)

        if not day_df.empty:
            numeric_cols = [
                "hour",
                "avg_dep_delay",
                "avg_wind_speed",
                "avg_precip",
                "avg_visibility",
                "flights",
            ]
            for col in numeric_cols:
                day_df[col] = pd.to_numeric(day_df[col], errors="coerce")

            fig_day = px.scatter(
                day_df,
                x="hour",
                y="avg_dep_delay",
                size="flights",
                color="avg_wind_speed",
                hover_data=["avg_precip", "avg_visibility"],
                title="Hourly departure delay, flight volume, and wind speed on the selected day",
                labels={
                    "hour": "Hour of day",
                    "avg_dep_delay": "Average departure delay (min)",
                    "avg_wind_speed": "Average wind speed",
                    "flights": "Flights",
                    "avg_precip": "Average precipitation",
                    "avg_visibility": "Average visibility",
                },
            )
            st.plotly_chart(style_plot(fig_day, 500), use_container_width=True)

            peak_row = day_df.sort_values("avg_dep_delay", ascending=False).iloc[0]
            insight_box(
                f"On <b>{chosen_date}</b>, the highest average departure delay occurred around "
                f"<b>{int(peak_row['hour']):02d}:00</b>, at about <b>{peak_row['avg_dep_delay']:.1f} minutes</b>."
            )
        else:
            st.info("No selected-day weather data available for this date and filter combination.")

    insight_box(
        "Weather conditions like wind and visibility can affect delays slightly, but they are not the main cause of delays. The strongest driver of arrival delays is late departure."
    )

    section_close()


if __name__ == "__main__":
    main()