import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from part3.db import query_df


# ---------------------------------------------------
# Small helpers
# ---------------------------------------------------

def divider():
    return """
    <hr style='margin-top:1.4rem;margin-bottom:1.4rem;border-top:1px solid rgba(120,120,120,0.25);'>
    """


def human_num(n):
    try:
        return f"{int(n):,}"
    except Exception:
        return str(n)


def clean_engine_type(val):
    if pd.isna(val):
        return "Unknown"

    v = str(val).lower().strip()

    if "fan" in v:
        return "Turbo-fan"
    if "jet" in v:
        return "Turbo-jet"
    if "recip" in v or "prop" in v:
        return "Propeller"

    return "Unknown"


# ---------------------------------------------------
# Data loading
# ---------------------------------------------------

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


def load_plane_data(dest=None):
    dest_sql = ""
    params = []

    if dest is not None:
        dest_sql = "AND f.dest = ?"
        params.append(dest)

    df = query_df(
        f"""
        SELECT
            f.distance,
            f.air_time,
            f.dep_delay,
            f.arr_delay,
            p.manufacturer,
            p.model,
            p.engines,
            p.seats,
            p.year AS plane_year,
            p.engine
        FROM flights f
        LEFT JOIN planes p
            ON f.tailnum = p.tailnum
        WHERE f.distance IS NOT NULL
          AND f.air_time IS NOT NULL
          AND p.model IS NOT NULL
          {dest_sql}
        """,
        params=tuple(params)
    )

    if df.empty:
        return df

    df["manufacturer"] = df["manufacturer"].fillna("Unknown").astype(str).str.strip()
    df["model"] = df["model"].fillna("Unknown").astype(str).str.strip()
    df["engine_type"] = df["engine"].apply(clean_engine_type)

    numeric_cols = [
        "distance", "air_time", "engines", "seats",
        "plane_year", "dep_delay", "arr_delay"
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["distance", "air_time"]).copy()
    df["speed"] = df["distance"] / df["air_time"] * 60

    return df


# ---------------------------------------------------
# KPI / summary helpers
# ---------------------------------------------------

def get_kpis(df: pd.DataFrame):
    return {
        "unique_models": int(df["model"].nunique()),
        "manufacturers": int(df["manufacturer"].nunique()),
        "avg_distance": float(df["distance"].mean()),
        "avg_air_time": float(df["air_time"].mean()),
    }


def get_top_manufacturers(df: pd.DataFrame, n: int = 10):
    return (
        df.groupby("manufacturer", as_index=False)
        .size()
        .rename(columns={"size": "flights"})
        .sort_values("flights", ascending=False)
        .head(n)
    )


def get_engine_box_df(df: pd.DataFrame):
    return df[df["engine_type"].isin(["Turbo-fan", "Turbo-jet"])].copy()


def get_engine_summary(df: pd.DataFrame):
    box_df = get_engine_box_df(df)
    if box_df.empty:
        return pd.DataFrame()

    return (
        box_df.groupby("engine_type", as_index=False)
        .agg(
            flights=("distance", "size"),
            avg_distance=("distance", "mean")
        )
        .sort_values("flights", ascending=False)
    )


# ---------------------------------------------------
# Scatter helpers
# ---------------------------------------------------

def get_scatter_sample(df_in: pd.DataFrame, n: int = 1200):
    if df_in.empty:
        return df_in.copy()

    n = min(len(df_in), n)
    return df_in.sample(n=n, random_state=42).copy()


# def get_color_map(values):
#     palette = (
#         px.colors.qualitative.Set2
#         + px.colors.qualitative.Safe
#         + px.colors.qualitative.Pastel
#         + px.colors.qualitative.Bold
#     )
#     uniq = sorted(pd.Series(values).dropna().unique().tolist())
#     return {v: palette[i % len(palette)] for i, v in enumerate(uniq)}


# def build_legend_figure(manufacturers, color_map):
#     fig = go.Figure()

#     for manu_name in manufacturers:
#         fig.add_trace(
#             go.Scatter(
#                 x=[None],
#                 y=[None],
#                 mode="markers",
#                 marker=dict(size=11, color=color_map[manu_name]),
#                 name=manu_name,
#                 showlegend=True,
#             )
#         )

    fig.update_layout(
        height=95,
        margin=dict(t=0, b=0, l=0, r=0),
        legend=dict(
            title="Manufacturer",
            orientation="h",
            y=1,
            yanchor="top",
            x=0,
            xanchor="left",
            font=dict(size=11),
            itemsizing="constant",
            tracegroupgap=8,
        ),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig


def build_scatter_figures(sample: pd.DataFrame):
    common = dict(
        opacity=0.55,
        color_discrete_sequence=["#3aa2ed"],
        hover_data={
            "manufacturer": True,
            "model": True,
            "plane_year": ":.0f",
            "air_time": ":.1f",
            "distance": ":.1f",
            "engines": True,
            "seats": True,
        },
    )

    fig_year_air = px.scatter(
        sample.dropna(subset=["plane_year", "air_time"]),
        x="plane_year",
        y="air_time",
        title="Year vs Flight Duration",
        **common
    )
    fig_year_air.update_layout(
        height=420,
        showlegend=False,
        xaxis_title="Plane Manufacturing Year",
        yaxis_title="Flight Duration (min)",
        margin=dict(t=70, l=20, r=20, b=20),
    )
    fig_year_air.update_traces(marker=dict(size=8))

    fig_year_dist = px.scatter(
        sample.dropna(subset=["plane_year", "distance"]),
        x="plane_year",
        y="distance",
        title="Year vs Flight Distance",
        **common
    )
    fig_year_dist.update_layout(
        height=420,
        showlegend=False,
        xaxis_title="Plane Manufacturing Year",
        yaxis_title="Flight Distance",
        margin=dict(t=70, l=20, r=20, b=20),
    )
    fig_year_dist.update_traces(marker=dict(size=8))

    fig_eng = px.scatter(
        sample.dropna(subset=["engines", "distance"]),
        x="engines",
        y="distance",
        title="Engines vs Flight Distance",
        **common
    )
    fig_eng.update_layout(
        height=420,
        showlegend=False,
        xaxis_title="Number of Engines",
        yaxis_title="Flight Distance",
        margin=dict(t=70, l=20, r=20, b=20),
    )
    fig_eng.update_traces(marker=dict(size=8))
    fig_eng.update_xaxes(
        tickmode="array",
        tickvals=[1, 2, 3, 4],
        range=[0.7, 4.3]
    )

    fig_seats = px.scatter(
        sample.dropna(subset=["seats", "distance"]),
        x="seats",
        y="distance",
        title="Seats vs Flight Distance",
        **common
    )
    fig_seats.update_layout(
        height=420,
        showlegend=False,
        xaxis_title="Number of Seats",
        yaxis_title="Flight Distance",
        margin=dict(t=70, l=20, r=20, b=20),
    )
    fig_seats.update_traces(marker=dict(size=8))

    return fig_year_air, fig_year_dist, fig_eng, fig_seats

# ---------------------------------------------------
# Manufacturer + model summaries
# ---------------------------------------------------

def get_model_capability_df(df: pd.DataFrame):
    out = (
        df.groupby(["manufacturer", "model"], as_index=False)
        .agg(
            max_distance=("distance", "max"),
            max_air_time=("air_time", "max"),
            mean_distance=("distance", "mean"),
            mean_air_time=("air_time", "mean"),
            flights=("distance", "size"),
        )
        .sort_values(["max_distance", "max_air_time"], ascending=[False, False])
    )
    return out


def build_model_capability_figure(model_df: pd.DataFrame):
    plot_df = model_df.copy()
    plot_df["label"] = np.where(
        plot_df["max_distance"].rank(method="dense", ascending=False) <= 6,
        plot_df["model"],
        ""
    )

    fig = px.scatter(
        plot_df,
        x="max_distance",
        y="max_air_time",
        size="flights",
        hover_name="model",
        hover_data={
            "manufacturer": True,
            "max_distance": ":.0f",
            "max_air_time": ":.0f",
            "mean_distance": ":.1f",
            "mean_air_time": ":.1f",
            "flights": True,
        },
        title="Model capability map",
        color_discrete_sequence=["#3aa2ed"],
    )

    fig.update_traces(marker=dict(opacity=0.75, line=dict(width=0.5, color="white")))
    fig.update_layout(
        height=620,
        xaxis_title="Maximum Flight Distance (miles)",
        yaxis_title="Maximum Air Time (min)",
        margin=dict(t=70, l=20, r=20, b=20),
    )

    for _, row in plot_df[plot_df["label"] != ""].iterrows():
        fig.add_annotation(
            x=row["max_distance"],
            y=row["max_air_time"],
            text=row["label"],
            showarrow=False,
            yshift=10,
            font=dict(size=11),
        )

    return fig


def get_carrier_manufacturer_table(dest=None):
    dest_sql = ""
    params = []

    if dest is not None:
        dest_sql = "AND f.dest = ?"
        params.append(dest)

    df = query_df(
        f"""
        SELECT
            a.name AS carrier,
            COALESCE(NULLIF(TRIM(p.manufacturer), ''), 'Unknown') AS manufacturer
        FROM flights f
        LEFT JOIN airlines a ON a.carrier = f.carrier
        LEFT JOIN planes p ON p.tailnum = f.tailnum
        WHERE a.name IS NOT NULL
          {dest_sql}
        """,
        params=tuple(params)
    )

    if df.empty:
        return df

    out = (
        df.groupby("carrier")["manufacturer"]
        .apply(lambda x: ", ".join(sorted(pd.Series(x).dropna().astype(str).unique().tolist())))
        .reset_index(name="fleet_mix")
        .sort_values("carrier")
    )
    return out


# ---------------------------------------------------
# Correlation matrix
# ---------------------------------------------------

def get_corr_matrix(df: pd.DataFrame):
    corr_cols = [
        "plane_year",
        "air_time",
        "distance",
        "seats",
        "dep_delay",
        "arr_delay",
        "speed",
    ]

    label_map = {
        "plane_year": "Plane Year",
        "air_time": "Flight Duration",
        "distance": "Flight Distance",
        "seats": "Number of Seats",
        "dep_delay": "Departure Delay",
        "arr_delay": "Arrival Delay",
        "speed": "Speed (mph)",
    }

    corr = df[corr_cols].corr(numeric_only=True).round(2)
    corr = corr.rename(index=label_map, columns=label_map)
    return corr


def build_corr_figure(df: pd.DataFrame):
    corr = get_corr_matrix(df)

    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
    z = corr.mask(mask)

    fig = go.Figure(
        data=go.Heatmap(
            z=z.values,
            x=corr.columns.tolist(),
            y=corr.index.tolist(),
            colorscale="Greens",
            zmin=0,
            zmax=1,
            text=z.where(~z.isna(), ""),
            texttemplate="%{text}",
            textfont={"size": 11},
            colorbar=dict(title="Correlation"),
            hoverongaps=False,
        )
    )

    fig.update_layout(
        height=620,
        margin=dict(t=20, l=20, r=20, b=20),
    )
    fig.update_xaxes(tickangle=35)
    fig.update_yaxes(autorange="reversed")

    return fig, corr


def get_corr_conclusion(corr: pd.DataFrame):
    corr_long = corr.copy()

    values = []
    cols = corr_long.columns.tolist()
    for i in range(len(cols)):
        for j in range(i):
            a = cols[i]
            b = cols[j]
            val = corr_long.loc[a, b]
            if pd.notna(val):
                values.append((a, b, float(val)))

    if not values:
        return "Within the selected filters, there is not enough data to summarize the strongest relationships."

    strongest = sorted(values, key=lambda x: abs(x[2]), reverse=True)[0]
    a, b, val = strongest

    return (
        f"Within the current filters, the strongest relationship is between **{a}** and **{b}** "
        f"with a correlation of **{val:.2f}**. This means these two variables tend to move together "
        f"more clearly than the others in the filtered subset, but the pattern can change when the destination filter changes."
    )