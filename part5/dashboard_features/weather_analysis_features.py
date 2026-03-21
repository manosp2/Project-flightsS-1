import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from part3.db import query_df
from part3.wind_speed_analysis import bearing_deg, wind_dot_flight

try:
    from scipy.stats import gaussian_kde, pointbiserialr
except Exception:
    gaussian_kde = None
    pointbiserialr = None


HEADWIND_COLOR = "#ff9bb4"
TAILWIND_COLOR = "#80c9fd"
DARK_BLUE_COLOR = "#588dff"

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTH_TO_NUM = {m: i + 1 for i, m in enumerate(MONTH_LABELS)}

def get_filter_options():
    return query_df(
        """
        SELECT DISTINCT dest
        FROM flights
        WHERE dest IS NOT NULL
        ORDER BY dest
        """
    )["dest"].dropna().tolist()


def get_wind_effect_df(
    origins: tuple[str, ...],
    months: tuple[int, ...],
    dest_filter: str | None,
    day_sql: str,
    day_params: tuple,
    n_limit: int = 120000,
) -> pd.DataFrame:
    o_ph = ",".join(["?"] * len(origins))
    m_ph = ",".join(["?"] * len(months))

    dest_sql = ""
    params = [*origins, *months, *day_params]
    if dest_filter is not None:
        dest_sql = "AND f.dest = ?"
        params.append(dest_filter)

    df = query_df(
        f"""
        SELECT
            f.origin,
            f.dest,
            f.distance,
            f.air_time,
            w.wind_dir,
            w.wind_speed
        FROM flights f
        JOIN weather w
          ON w.origin = f.origin
         AND w.time_hour = f.time_hour
        WHERE f.origin IN ({o_ph})
          AND f.month IN ({m_ph})
          {day_sql}
          {dest_sql}
          AND f.air_time IS NOT NULL
          AND f.air_time > 0
          AND f.distance IS NOT NULL
          AND f.distance > 50
          AND w.wind_dir IS NOT NULL
          AND w.wind_speed IS NOT NULL
        LIMIT ?
        """,
        params=tuple([*params, int(n_limit)])
    )

    if df.empty:
        return df

    airports = query_df(
        """
        SELECT faa, lat, lon
        FROM airports
        WHERE lat IS NOT NULL AND lon IS NOT NULL
        """
    ).set_index("faa")

    df = df[df["origin"].isin(airports.index) & df["dest"].isin(airports.index)].copy()

    if df.empty:
        return df

    def flight_bearing(row):
        o = airports.loc[row["origin"]]
        d = airports.loc[row["dest"]]
        return bearing_deg(o["lat"], o["lon"], d["lat"], d["lon"])

    df["bearing"] = df.apply(flight_bearing, axis=1)
    df["inner_product"] = df.apply(
        lambda r: wind_dot_flight(r["bearing"], r["wind_dir"], r["wind_speed"]),
        axis=1
    )
    df["air_time_per_100_miles"] = (df["air_time"] / df["distance"]) * 100
    df["wind_condition"] = np.where(df["inner_product"] < 0, "Headwind", "Tailwind")

    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=["inner_product", "air_time_per_100_miles"])
    df = df[df["air_time_per_100_miles"].between(8, 80)].copy()

    return df


def get_weather_delay_df(
    origins: tuple[str, ...],
    months: tuple[int, ...],
    dest_filter: str | None,
    day_sql: str,
    day_params: tuple,
    n_limit: int = 120000,
) -> pd.DataFrame:
    o_ph = ",".join(["?"] * len(origins))
    m_ph = ",".join(["?"] * len(months))

    dest_sql = ""
    params = [*origins, *months, *day_params]
    if dest_filter is not None:
        dest_sql = "AND f.dest = ?"
        params.append(dest_filter)

    df = query_df(
        f"""
        SELECT
            f.dep_delay,
            f.arr_delay,
            f.air_time,
            w.wind_speed,
            w.wind_dir,
            w.precip,
            w.visib,
            w.temp,
            w.pressure,
            w.humid,
            w.wind_gust
        FROM flights f
        JOIN weather w
          ON f.origin = w.origin
         AND f.year   = w.year
         AND f.month  = w.month
         AND f.day    = w.day
         AND CAST(f.hour AS INTEGER) = CAST(w.hour AS INTEGER)
        WHERE f.origin IN ({o_ph})
          AND f.month IN ({m_ph})
          {day_sql}
          {dest_sql}
          AND f.dep_delay IS NOT NULL
          AND f.arr_delay IS NOT NULL
          AND f.air_time IS NOT NULL
          AND w.wind_speed IS NOT NULL
          AND w.wind_dir IS NOT NULL
          AND w.precip IS NOT NULL
          AND w.visib IS NOT NULL
          AND w.temp IS NOT NULL
          AND w.pressure IS NOT NULL
          AND w.humid IS NOT NULL
        LIMIT ?
        """,
        params=tuple([*params, int(n_limit)])
    )

    if df.empty:
        return df

    if "wind_gust" not in df.columns:
        df["wind_gust"] = np.nan

    numeric_cols = [
        "dep_delay", "arr_delay", "air_time", "wind_speed", "wind_dir",
        "precip", "visib", "temp", "pressure", "humid", "wind_gust"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["bad_weather"] = (
        (df["wind_speed"] >= 20) |
        (df["precip"] > 0.10) |
        (df["visib"] < 5) |
        (df["wind_gust"].fillna(0) >= 25)
    ).astype(int)

    return df


def _kde_curve(values: pd.Series, n_points: int = 300):
    values = pd.Series(values).dropna()
    if len(values) < 5:
        return None, None

    x_min = max(8.0, float(values.min()) - 2)
    x_max = min(45.0, float(values.max()) + 2)
    x_grid = np.linspace(x_min, x_max, n_points)

    if gaussian_kde is not None:
        kde = gaussian_kde(values)
        y_grid = kde(x_grid)
    else:
        counts, bins = np.histogram(values, bins=40, density=True)
        mids = (bins[:-1] + bins[1:]) / 2
        y_grid = np.interp(x_grid, mids, counts)
        kernel = np.ones(11) / 11
        y_grid = np.convolve(y_grid, kernel, mode="same")

    return x_grid, y_grid


def build_density_figure(df: pd.DataFrame) -> go.Figure:
    head = df[df["wind_condition"] == "Headwind"]["air_time_per_100_miles"]
    tail = df[df["wind_condition"] == "Tailwind"]["air_time_per_100_miles"]

    x_head, y_head = _kde_curve(head)
    x_tail, y_tail = _kde_curve(tail)

    fig = go.Figure()

    if x_head is not None:
        fig.add_trace(
            go.Scatter(
                x=x_head,
                y=y_head,
                mode="lines",
                name="Headwind",
                line=dict(color=HEADWIND_COLOR, width=3),
                fill="tozeroy",
                fillcolor="rgba(255,155,180,0.35)",
            )
        )

    if x_tail is not None:
        fig.add_trace(
            go.Scatter(
                x=x_tail,
                y=y_tail,
                mode="lines",
                name="Tailwind",
                line=dict(color=TAILWIND_COLOR, width=3),
                fill="tozeroy",
                fillcolor="rgba(98,189,255,0.28)",
            )
        )

    if len(head) > 0:
        fig.add_vline(
            x=float(head.mean()),
            line_width=2,
            line_dash="dash",
            line_color=HEADWIND_COLOR
        )

    if len(tail) > 0:
        fig.add_vline(
            x=float(tail.mean()),
            line_width=2,
            line_dash="dash",
            line_color=TAILWIND_COLOR
        )

    fig.update_layout(
        title="Distribution of Air Time by Wind Condition",
        template="simple_white",
        height=500,
        margin=dict(l=20, r=20, t=60, b=20),
        legend_title="Wind Condition",
    )
    fig.update_xaxes(title="Normalized Air Time (minutes per 100 miles)", range=[8, 45])
    fig.update_yaxes(title="Density", rangemode="tozero")

    return fig


def build_box_figure(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()

    tail = df[df["wind_condition"] == "Tailwind"]["air_time_per_100_miles"]
    head = df[df["wind_condition"] == "Headwind"]["air_time_per_100_miles"]

    fig.add_trace(
        go.Box(
            y=tail,
            name="Tailwind",
            boxpoints="outliers",
            marker=dict(color=TAILWIND_COLOR, size=5, opacity=0.55),
            line=dict(color=TAILWIND_COLOR, width=3),
            fillcolor="rgba(166,217,122,0.28)",
            whiskerwidth=0.8,
            quartilemethod="linear",
        )
    )

    fig.add_trace(
        go.Box(
            y=head,
            name="Headwind",
            boxpoints="outliers",
            marker=dict(color=DARK_BLUE_COLOR, size=5, opacity=0.55),
            line=dict(color=DARK_BLUE_COLOR, width=3),
            fillcolor="rgba(0,146,243,0.25)",
            whiskerwidth=0.8,
            quartilemethod="linear",
        )
    )

    fig.update_layout(
        title="Air Time per 100 Miles by Wind Condition",
        template="simple_white",
        height=500,
        margin=dict(l=20, r=20, t=60, b=20),
        showlegend=False,
    )
    fig.update_xaxes(title="Wind Condition")
    fig.update_yaxes(title="Air Time (min per 100 miles)", range=[0, 60])

    return fig


def _make_scatter_focus_df(df: pd.DataFrame) -> pd.DataFrame:
    plot_df = df.copy()

    threshold = float(plot_df["inner_product"].abs().quantile(0.30))
    plot_df = plot_df[plot_df["inner_product"].abs() >= threshold].copy()

    head = plot_df[plot_df["wind_condition"] == "Headwind"]
    tail = plot_df[plot_df["wind_condition"] == "Tailwind"]

    if head.empty or tail.empty:
        return plot_df

    n = min(len(head), len(tail), 5000)
    head = head.sample(n, random_state=42)
    tail = tail.sample(n, random_state=42)

    return pd.concat([head, tail], ignore_index=True)


def _binned_mean_lines(plot_df: pd.DataFrame, n_bins: int = 18) -> pd.DataFrame:
    all_parts = []

    for cond in ["Headwind", "Tailwind"]:
        sub = plot_df[plot_df["wind_condition"] == cond].copy()
        if sub.empty:
            continue

        sub["ip_bin"] = pd.cut(sub["inner_product"], bins=n_bins)

        grouped = (
            sub.groupby("ip_bin", observed=False)
            .agg(
                mean_inner_product=("inner_product", "mean"),
                mean_air_time=("air_time_per_100_miles", "mean"),
                n=("air_time_per_100_miles", "size"),
            )
            .reset_index(drop=True)
        )

        grouped["wind_condition"] = cond
        grouped = grouped.dropna(subset=["mean_inner_product", "mean_air_time"])
        grouped = grouped[grouped["n"] >= 20].copy()

        all_parts.append(grouped)

    if not all_parts:
        return pd.DataFrame(columns=["wind_condition", "mean_inner_product", "mean_air_time", "n"])

    return pd.concat(all_parts, ignore_index=True).sort_values(["wind_condition", "mean_inner_product"])


def build_scatter_figure(df: pd.DataFrame) -> go.Figure:
    plot_df = _make_scatter_focus_df(df)

    low = float(plot_df["inner_product"].quantile(0.01))
    high = float(plot_df["inner_product"].quantile(0.99))
    low = max(low, -80)
    high = min(high, 80)

    plot_df = plot_df[plot_df["inner_product"].between(low, high)].copy()
    line_df = _binned_mean_lines(plot_df)

    fig = px.scatter(
        plot_df,
        x="inner_product",
        y="air_time_per_100_miles",
        color="wind_condition",
        color_discrete_map={
            "Headwind": HEADWIND_COLOR,
            "Tailwind": TAILWIND_COLOR,
        },
        opacity=0.32,
        title="Inner Product vs Normalized Air Time",
        labels={
            "inner_product": "Inner Product",
            "air_time_per_100_miles": "Air Time (min per 100 miles)",
            "wind_condition": "Wind Condition",
        },
        hover_data=["origin", "dest", "distance", "air_time"],
    )

    fig.update_traces(marker=dict(size=6))

    for cond, color in [("Headwind", HEADWIND_COLOR), ("Tailwind", TAILWIND_COLOR)]:
        sub = line_df[line_df["wind_condition"] == cond]
        if not sub.empty:
            fig.add_trace(
                go.Scatter(
                    x=sub["mean_inner_product"],
                    y=sub["mean_air_time"],
                    mode="lines+markers",
                    line=dict(color=color, width=4),
                    marker=dict(size=7, color=color),
                    name=f"{cond} Mean",
                )
            )

    summary = (
        plot_df.groupby("wind_condition", as_index=False)
        .agg(
            mean_inner_product=("inner_product", "mean"),
            mean_air_time=("air_time_per_100_miles", "mean"),
        )
    )

    for _, row in summary.iterrows():
        fig.add_trace(
            go.Scatter(
                x=[row["mean_inner_product"]],
                y=[row["mean_air_time"]],
                mode="markers",
                marker=dict(
                    symbol="star",
                    size=24,
                    color=HEADWIND_COLOR if row["wind_condition"] == "Headwind" else TAILWIND_COLOR,
                    line=dict(color="white", width=2),
                ),
                name=f"{row['wind_condition']} Overall Mean",
            )
        )

    fig.update_layout(
        template="simple_white",
        height=500,
        margin=dict(l=20, r=20, t=60, b=20),
        legend_title="Wind Condition",
    )
    fig.update_xaxes(title="Inner Product", range=[low, high])
    fig.update_yaxes(title="Air Time (min per 100 miles)", range=[10, 50])

    return fig


def wind_stats_table(df: pd.DataFrame) -> pd.DataFrame:
    out = (
        df.groupby("wind_condition", as_index=False)
        .agg(
            Count=("air_time_per_100_miles", "size"),
            Mean_Air_Time=("air_time_per_100_miles", "mean"),
            Median_Air_Time=("air_time_per_100_miles", "median"),
            Std_Dev=("air_time_per_100_miles", "std"),
        )
        .rename(columns={"wind_condition": "Wind Condition"})
    )

    out["Count"] = out["Count"].astype(int).map(lambda x: f"{x:,}")
    out["Mean Air Time"] = out["Mean_Air_Time"].round(1).map(lambda x: f"{x:.1f}")
    out["Median Air Time"] = out["Median_Air_Time"].round(1).map(lambda x: f"{x:.1f}")
    out["Std Dev"] = out["Std_Dev"].round(1).map(lambda x: f"{x:.1f}")

    return out[["Wind Condition", "Count", "Mean Air Time", "Median Air Time", "Std Dev"]]


def build_corr_heatmap(df: pd.DataFrame) -> go.Figure:
    corr_cols = [
        "dep_delay", "arr_delay", "air_time", "wind_speed", "wind_dir",
        "precip", "visib", "temp", "pressure", "humid", "bad_weather", "wind_gust"
    ]
    labels = [
        "Departure Delay", "Arrival Delay", "Flight Time", "Wind Speed", "Wind Direction",
        "Precipitation", "Visibility", "Temperature", "Pressure", "Humidity",
        "Bad Weather", "Wind Gust"
    ]

    corr = df[corr_cols].corr(numeric_only=True).round(2)
    corr.index = labels
    corr.columns = labels

    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
    z = corr.mask(mask)

    fig = go.Figure(
        data=go.Heatmap(
            z=z.values,
            x=labels,
            y=labels,
            colorscale=[
                [0.0, "#91ef81"],
                [0.3, "#ffeb79"],
                [0.6, "#ff934c"],
                [1.0, "#E82A2A"],
            ],
            zmin=-1,
            zmax=1,
            text=z.where(~z.isna(), ""),
            texttemplate="%{text}",
            textfont={"size": 11},
            colorbar=dict(title="Correlation"),
            hoverongaps=False,
        )
    )

    fig.update_layout(
        title="Correlation Heatmap: Flight & Weather Variables (Bottom Triangle)",
        template="simple_white",
        height=680,
        margin=dict(l=20, r=20, t=70, b=20),
    )
    fig.update_xaxes(tickangle=90)
    fig.update_yaxes(autorange="reversed")
    return fig


def build_bad_weather_boxplot(df: pd.DataFrame) -> go.Figure:
    plot_df = df.copy()

    lower = float(plot_df["arr_delay"].quantile(0.01))
    upper = float(plot_df["arr_delay"].quantile(0.99))
    plot_df["arr_delay_clipped"] = plot_df["arr_delay"].clip(lower=lower, upper=upper)
    plot_df["Bad Weather"] = plot_df["bad_weather"].astype(str)

    arr0 = plot_df.loc[plot_df["Bad Weather"] == "0", "arr_delay_clipped"]
    arr1 = plot_df.loc[plot_df["Bad Weather"] == "1", "arr_delay_clipped"]

    fig = go.Figure()

    fig.add_trace(
        go.Box(
            y=arr0,
            name="0",
            boxpoints=False,
            line=dict(color=TAILWIND_COLOR, width=3),
            fillcolor="rgba(98,189,255,0.30)",
        )
    )
    fig.add_trace(
        go.Box(
            y=arr1,
            name="1",
            boxpoints=False,
            line=dict(color=DARK_BLUE_COLOR, width=3),
            fillcolor="rgba(0,146,243,0.28)",
        )
    )

    fig.update_layout(
        title="Arrival Delay vs. Bad Weather Indicator",
        template="simple_white",
        showlegend=False,
        height=480,
        margin=dict(l=20, r=20, t=60, b=20),
    )
    fig.update_xaxes(title="Bad Weather (1 = Yes, 0 = No)")
    fig.update_yaxes(title="Arrival Delay (minutes)")

    return fig


def get_wind_conclusion_stats(df: pd.DataFrame):
    head_mean = df.loc[df["wind_condition"] == "Headwind", "air_time_per_100_miles"].mean()
    tail_mean = df.loc[df["wind_condition"] == "Tailwind", "air_time_per_100_miles"].mean()
    overall_corr = df["inner_product"].corr(df["air_time_per_100_miles"])
    pct_diff = ((head_mean - tail_mean) / tail_mean) * 100 if tail_mean != 0 else np.nan

    return {
        "head_mean": round(head_mean, 1),
        "tail_mean": round(tail_mean, 1),
        "overall_corr": round(overall_corr, 2),
        "pct_diff": round(pct_diff, 1),
    }


def get_bad_weather_stats(df: pd.DataFrame):
    median_normal = df.loc[df["bad_weather"] == 0, "arr_delay"].median()
    median_bad = df.loc[df["bad_weather"] == 1, "arr_delay"].median()
    corr_bad = df["bad_weather"].corr(df["arr_delay"])
    dep_arr_corr = df["dep_delay"].corr(df["arr_delay"])

    if pointbiserialr is not None:
        try:
            r_val, p_val = pointbiserialr(df["bad_weather"], df["arr_delay"])
            p_text = f"{p_val:.3f}"
        except Exception:
            r_val = corr_bad
            p_text = "n/a"
    else:
        r_val = corr_bad
        p_text = "n/a"

    return {
        "median_normal": round(median_normal, 1),
        "median_bad": round(median_bad, 1),
        "corr_bad": round(corr_bad, 2),
        "dep_arr_corr": round(dep_arr_corr, 2),
        "r_val": round(r_val, 2),
        "p_text": p_text,
    }