from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st
import plotly.express as px

from part5.dashboard_features.plane_models_features import (
    human_num,
    get_destinations,
    load_plane_data,
    get_kpis,
    get_top_manufacturers,
    get_engine_box_df,
    get_engine_summary,
    get_scatter_sample,
    get_model_capability_df,
    build_model_capability_figure,
    get_carrier_manufacturer_table,
    build_corr_figure,
    get_corr_conclusion,
)

st.set_page_config(page_title="Plane Models Analysis", layout="wide")

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
    </style>
    """,
    unsafe_allow_html=True,
)

@st.cache_data
def get_destinations_cached():
    return get_destinations()


@st.cache_data
def load_plane_data_cached(dest_filter):
    return load_plane_data(dest_filter)


@st.cache_data
def get_top_manufacturers_cached(df, n=10):
    return get_top_manufacturers(df, n=n)


@st.cache_data
def get_engine_box_df_cached(df):
    return get_engine_box_df(df)


@st.cache_data
def get_engine_summary_cached(df):
    return get_engine_summary(df)


@st.cache_data
def get_scatter_sample_cached(df, n=1200):
    return get_scatter_sample(df, n=n)


@st.cache_data
def get_model_capability_df_cached(df):
    return get_model_capability_df(df)


@st.cache_data
def get_carrier_manufacturer_table_cached(dest_filter):
    return get_carrier_manufacturer_table(dest_filter)


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
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-footnote">{footnote}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def insight_box(text):
    st.markdown(f"<div class='insight-box'>{text}</div>", unsafe_allow_html=True)


def main():
    st.title("NYC Flights Dashboard")

    destinations = get_destinations_cached()

    st.sidebar.header("Filters")
    dest = st.sidebar.selectbox("Arrival airport", ["All destinations"] + destinations)
    dest_filter = None if dest == "All destinations" else dest

    current_view = "all destinations" if dest_filter is None else dest_filter

    st.markdown(
        f"""
        <div class="intro-box">
            <div class="intro-title"> Plane Models Analysis</div>
            <div class="intro-text">
                Explore how aircraft manufacturers, engine types, and aircraft characteristics
                relate to flight distance and air time across NYC flights.
            </div>
            <div class="filter-row">
                <span class="intro-note">Current view: {current_view}</span>
                <span class="intro-note-secondary">Interactive filters: Arrival airport, Manufacturer</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df = load_plane_data_cached(dest_filter)

    if df.empty:
        st.warning("No data available for the selected destination.")
        st.stop()

    manufacturer_options = sorted(df["manufacturer"].dropna().unique().tolist())

    selected_manufacturer = st.sidebar.selectbox(
        "Manufacturer",
        ["All manufacturers"] + manufacturer_options,
    )

    if selected_manufacturer != "All manufacturers":
        df = df[df["manufacturer"] == selected_manufacturer].copy()
        if df.empty:
            st.warning("No data available for the selected manufacturer filter.")
            st.stop()

    # ---------------------------------------------------
    # KPIs
    # ---------------------------------------------------
    kpis = get_kpis(df)

    section_open(
        "Plane Models KPIs",
        "A quick overview of fleet variety, manufacturer presence, and average flight characteristics within the current filter.",
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Unique plane models", f"{kpis['unique_models']}", "Distinct aircraft models observed")
    with c2:
        kpi_card("Manufacturers", f"{kpis['manufacturers']}", "Manufacturers represented in the data")
    with c3:
        kpi_card("Avg flight distance", f"{kpis['avg_distance']:.1f} mi", "Average route distance")
    with c4:
        kpi_card("Avg air time", f"{kpis['avg_air_time']:.1f} min", "Average time spent airborne")

    section_close()

    # ---------------------------------------------------
    # Manufacturer + engine analysis
    # ---------------------------------------------------
    section_open(
        "Manufacturer and Engine Analysis",
        "Compare which aircraft manufacturers dominate the selected routes and how engine types relate to travel distance.",
    )

    left, right = st.columns(2)

    with left:
        st.subheader("Aircraft Manufacturer Analysis")

        manu_df = get_top_manufacturers_cached(df, n=10)

        fig_manu = px.bar(
            manu_df.sort_values("flights"),
            x="flights",
            y="manufacturer",
            orientation="h",
            title="Top manufacturers by number of flights",
            text="flights",
            color_discrete_sequence=[BLUE_MAIN],
        )
        fig_manu.update_traces(texttemplate="%{text:,}", textposition="outside")
        fig_manu.update_layout(
            height=500,
            xaxis_title="Flights",
            yaxis_title="Manufacturer",
            margin=dict(t=70, l=20, r=30, b=20),
            coloraxis_showscale=False,
            plot_bgcolor="white",
            paper_bgcolor="white",
        )

        st.plotly_chart(fig_manu, use_container_width=True)

        if not manu_df.empty:
            top = manu_df.iloc[0]
            insight_box(
                f"Within the selected filters, <b>{top['manufacturer']}</b> appears most often, with "
                f"<b>{human_num(top['flights'])} flights</b>."
            )

    with right:
        st.subheader("Aircraft Engine Type Analysis")

        box_df = get_engine_box_df_cached(df)

        if box_df.empty:
            st.info("No Turbo-fan or Turbo-jet data available for this selection.")
        else:
            fig_engine = px.box(
                box_df,
                x="engine_type",
                y="distance",
                color="engine_type",
                points="outliers",
                category_orders={"engine_type": ["Turbo-fan", "Turbo-jet"]},
                title="Flight distance by engine type",
                color_discrete_sequence=["#ff893a", "#5ab621"],
            )

            fig_engine.update_layout(
                showlegend=False,
                height=500,
                xaxis_title="Engine type",
                yaxis_title="Flight distance (miles)",
                margin=dict(t=70, l=20, r=20, b=20),
                plot_bgcolor="white",
                paper_bgcolor="white",
            )

            st.plotly_chart(fig_engine, use_container_width=True)

            engine_summary = get_engine_summary_cached(df)
            if not engine_summary.empty:
                top_engine = engine_summary.iloc[0]
                insight_box(
                    f"The most common engine type is <b>{top_engine['engine_type']}</b>, "
                    f"with an average flight distance of <b>{top_engine['avg_distance']:.0f} miles</b>."
                )

    section_close()

    # ---------------------------------------------------
    # Comparison charts
    # ---------------------------------------------------
    section_open(
        "Plane and Flight Comparisons",
        "These charts compare flight distance and air time across engine type, engine count, and aircraft size using clearer business-style comparison visuals.",
    )

    compare_df = df.copy()

    engine_air_df = (
        compare_df.dropna(subset=["engine_type", "air_time"])
        .groupby("engine_type", as_index=False)
        .agg(
            avg_air_time=("air_time", "mean"),
            flights=("air_time", "size"),
        )
        .sort_values("avg_air_time", ascending=False)
    )

    engine_dist_df = (
        compare_df.dropna(subset=["engine_type", "distance"])
        .groupby("engine_type", as_index=False)
        .agg(
            avg_distance=("distance", "mean"),
            flights=("distance", "size"),
        )
        .sort_values("avg_distance", ascending=False)
    )

    engines_box_df = compare_df.dropna(subset=["engines", "distance"]).copy()
    if not engines_box_df.empty:
        engines_box_df["engines"] = engines_box_df["engines"].astype(int).astype(str)

    seats_box_df = compare_df.dropna(subset=["seats", "distance"]).copy()
    if not seats_box_df.empty:
        seats_box_df["seat_group"] = pd.cut(
            seats_box_df["seats"],
            bins=[0, 100, 200, 300, 500],
            labels=["Small (1–100)", "Medium (101–200)", "Large (201–300)", "Very Large (301+)"],
            include_lowest=True,
        )

    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)

    with c1:
        st.subheader("Average Air Time by Engine Type")
        if engine_air_df.empty:
            st.info("No engine-type airtime data available.")
        else:
            fig_engine_air = px.bar(
                engine_air_df,
                x="engine_type",
                y="avg_air_time",
                text="avg_air_time",
                title="Average flight duration by engine type",
                labels={
                    "engine_type": "Engine type",
                    "avg_air_time": "Average air time (minutes)",
                },
                color="engine_type",
                color_discrete_map={
                    "Turbo-fan": "#ff893a",
                    "Turbo-jet": "#5ab621",
                    "Propeller": "#76edb5",
                    "Unknown": "#62656a",
                },
            )
            fig_engine_air.update_traces(texttemplate="%{text:.1f}", textposition="outside")
            fig_engine_air.update_layout(
                showlegend=False,
                plot_bgcolor="white",
                paper_bgcolor="white",
                margin=dict(t=70, l=20, r=20, b=20),
                height=420,
                xaxis_title="Engine type",
                yaxis_title="Average air time (minutes)",
            )
            st.plotly_chart(fig_engine_air, use_container_width=True)

    with c2:
        st.subheader("Average Flight Distance by Engine Type")
        if engine_dist_df.empty:
            st.info("No engine-type distance data available.")
        else:
            fig_engine_dist = px.bar(
                engine_dist_df,
                x="engine_type",
                y="avg_distance",
                text="avg_distance",
                title="Average flight distance by engine type",
                labels={
                    "engine_type": "Engine type",
                    "avg_distance": "Average flight distance (miles)",
                },
                color="engine_type",
                color_discrete_map={
                    "Turbo-fan": "#ff893a",
                    "Turbo-jet": "#5ab621",
                    "Propeller": "#76edb5",
                    "Unknown": "#62656a",
                },
            )
            fig_engine_dist.update_traces(texttemplate="%{text:.0f}", textposition="outside")
            fig_engine_dist.update_layout(
                showlegend=False,
                plot_bgcolor="white",
                paper_bgcolor="white",
                margin=dict(t=70, l=20, r=20, b=20),
                height=420,
                xaxis_title="Engine type",
                yaxis_title="Average flight distance (miles)",
            )
            st.plotly_chart(fig_engine_dist, use_container_width=True)

    with c3:
        st.subheader("Flight Distance by Number of Engines")
        if engines_box_df.empty:
            st.info("No engine-count data available.")
        else:
            fig_engines_box = px.box(
                engines_box_df,
                x="engines",
                y="distance",
                title="Flight distance by number of engines",
                labels={
                    "engines": "Number of engines",
                    "distance": "Flight distance (miles)",
                },
                color_discrete_sequence=[BLUE_MAIN],
                points=False,
            )
            fig_engines_box.update_layout(
                showlegend=False,
                plot_bgcolor="white",
                paper_bgcolor="white",
                margin=dict(t=70, l=20, r=20, b=20),
                height=420,
                xaxis_title="Number of engines",
                yaxis_title="Flight distance (miles)",
            )
            st.plotly_chart(fig_engines_box, use_container_width=True)

    with c4:
        st.subheader("Flight Distance by Aircraft Size")
        if seats_box_df.empty:
            st.info("No seats data available.")
        else:
            fig_seats_box = px.box(
                seats_box_df,
                x="seat_group",
                y="distance",
                title="Flight distance by aircraft size group",
                labels={
                    "seat_group": "Aircraft size group",
                    "distance": "Flight distance (miles)",
                },
                category_orders={
                    "seat_group": ["Small (1–100)", "Medium (101–200)", "Large (201–300)", "Very Large (301+)"]
                },
                color_discrete_sequence=[BLUE_MAIN],
                points=False,
            )
            fig_seats_box.update_layout(
                showlegend=False,
                plot_bgcolor="white",
                paper_bgcolor="white",
                margin=dict(t=70, l=20, r=20, b=20),
                height=420,
                xaxis_title="Aircraft size group",
                yaxis_title="Flight distance (miles)",
            )
            st.plotly_chart(fig_seats_box, use_container_width=True)

    if not engine_air_df.empty and not engine_dist_df.empty:
        top_air = engine_air_df.iloc[0]
        top_dist = engine_dist_df.iloc[0]
        insight_box(
            f"<b>{top_air['engine_type']}</b> aircraft have the longest average air time "
            f"({top_air['avg_air_time']:.1f} min), while <b>{top_dist['engine_type']}</b> aircraft "
            f"cover the longest average distance ({top_dist['avg_distance']:.0f} miles)."
        )

    section_close()

    # ---------------------------------------------------
    # Model capability map
    # ---------------------------------------------------
    section_open(
        "Plane Models: Max Distance vs Max Air Time",
        "This chart highlights how far and how long different aircraft models are observed to fly.",
    )

    model_df = get_model_capability_df_cached(df)
    fig_model = build_model_capability_figure(model_df)
    fig_model.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(t=70, l=20, r=20, b=20),
        height=560,
    )

    st.plotly_chart(fig_model, use_container_width=True)

    if not model_df.empty:
        max_distance_row = model_df.sort_values("max_distance", ascending=False).iloc[0]
        max_air_time_row = model_df.sort_values("max_air_time", ascending=False).iloc[0]

        insight_box(
            f"<b>{max_air_time_row['model']}</b> reaches the highest observed air time, while "
            f"<b>{max_distance_row['model']}</b> reaches the largest observed distance."
        )

    section_close()

    # ---------------------------------------------------
    # Correlation + carrier table
    # ---------------------------------------------------
    section_open(
        "Correlation and Fleet Mix",
        "Summarize how aircraft and flight variables move together, and which manufacturers appear in each carrier’s fleet mix.",
    )

    left2, right2 = st.columns([1.05, 1])

    with left2:
        st.subheader("Correlation Matrix for Plane and Flight Variables")

        fig_corr, corr = build_corr_figure(df)
        fig_corr.update_traces(
            colorscale=[
                [0.0, "#6cc45d"],
                [0.3, "#ffeb79"],
                [0.6, "#ff934c"],
                [1.0, "#E82A2A"],
            ],
        )
        fig_corr.update_layout(
            title="Aircraft and Flight Metric Correlation",
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(t=70, l=20, r=20, b=20),
            height=520,
        )
        st.plotly_chart(fig_corr, use_container_width=True)

        insight_box(get_corr_conclusion(corr))

    with right2:
        st.subheader("Plane manufacturer per carrier")

        carrier_df = get_carrier_manufacturer_table_cached(dest_filter)

        st.dataframe(
            carrier_df,
            use_container_width=True,
            hide_index=True,
            height=520,
        )

        insight_box(
            "This table gives a quick overview of which manufacturers appear in each airline’s fleet mix within the current filters."
        )

    section_close()


if __name__ == "__main__":
    main()