import pandas as pd
import plotly.express as px

from .db import query_df


def avg_dep_delay_per_airline() -> pd.DataFrame:
    """Average departure delay per airline (full airline names)."""
    return query_df(
        """
        SELECT a.name AS airline,
               AVG(f.dep_delay) AS avg_dep_delay
        FROM flights f
        JOIN airlines a ON a.carrier = f.carrier
        WHERE f.dep_delay IS NOT NULL
        GROUP BY a.name
        ORDER BY avg_dep_delay DESC;
        """
    )


def plot_avg_dep_delay_per_airline():
    df = avg_dep_delay_per_airline()
    fig = px.bar(
        df,
        x="airline",
        y="avg_dep_delay",
        title="Average departure delay per airline",
        labels={"airline": "Airline", "avg_dep_delay": "Avg departure delay (minutes)"},
    )
    fig.update_xaxes(tickangle=45)
    return fig

def count_delayed_flights_to_destination(dest: str, start_month: int, end_month: int) -> int:
    """
    Count delayed flights (dep_delay > 0) to dest for month range [start_month, end_month].
    """
    dest = dest.upper().strip()
    start_month = int(start_month)
    end_month = int(end_month)

    if not (1 <= start_month <= 12 and 1 <= end_month <= 12):
        raise ValueError("Months must be between 1 and 12")
    if start_month > end_month:
        raise ValueError("start_month must be <= end_month")

    df = query_df(
        """
        SELECT COUNT(*) AS n
        FROM flights
        WHERE dest = ?
          AND month BETWEEN ? AND ?
          AND dep_delay IS NOT NULL
          AND dep_delay > 0;
        """,
        params=(dest, start_month, end_month),
    )
    return int(df.loc[0, "n"])


def distance_vs_arrival_delay(n: int | None = 20000) -> pd.DataFrame:
    """Dataset for distance vs arrival delay."""
    q = """
    SELECT distance, arr_delay
    FROM flights
    WHERE distance IS NOT NULL
      AND arr_delay IS NOT NULL
    """
    if n is not None:
        q += " LIMIT ?"
        return query_df(q, params=(int(n),))
    return query_df(q)


def plot_distance_vs_arrival_delay(n: int | None = 20000):
    """Scatter plot distance vs arrival delay (no statsmodels trendline dependency)."""
    df = distance_vs_arrival_delay(n=n)
    fig = px.scatter(
        df,
        x="distance",
        y="arr_delay",
        opacity=0.25,
        title="Distance vs Arrival Delay",
        labels={"distance": "Distance (miles)", "arr_delay": "Arrival delay (minutes)"},
    )
    return fig


def plot_distance_delay_binned(bin_width: int = 250):
    """
    Optional helper: average arrival delay per distance bin (reduces noise).
    """
    df = query_df(
        """
        SELECT distance, arr_delay
        FROM flights
        WHERE distance IS NOT NULL
          AND arr_delay IS NOT NULL;
        """
    )

    df = df[(df["arr_delay"] > 0) & (df["arr_delay"] <= 300)].copy()
    df["dist_bin"] = (df["distance"] // int(bin_width)) * int(bin_width)

    grouped = (
        df.groupby("dist_bin", as_index=False)["arr_delay"]
        .mean()
        .sort_values("dist_bin")
    )

    fig = px.line(
        grouped,
        x="dist_bin",
        y="arr_delay",
        markers=True,
        title=f"Mean arrival delay vs distance (bin = {bin_width} miles)",
        labels={"dist_bin": "Distance (miles)", "arr_delay": "Mean arrival delay (minutes)"},
    )
    return fig