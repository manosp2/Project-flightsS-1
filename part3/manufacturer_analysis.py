import pandas as pd
import plotly.express as px

from .db import query_df


def top_manufacturers_for_destination(dest: str, n: int = 5) -> pd.DataFrame:
    """
    Assignment:
    destination -> top N manufacturers by number of flights to dest.
    Unknown happens when tailnum in flights is missing or not found in planes.
    """
    dest = dest.upper().strip()
    n = int(n)

    return query_df(
        """
        SELECT
            COALESCE(NULLIF(TRIM(p.manufacturer), ''), 'Unknown') AS manufacturer,
            COUNT(*) AS flight_count
        FROM flights f
        LEFT JOIN planes p ON p.tailnum = f.tailnum
        WHERE f.dest = ?
        GROUP BY manufacturer
        ORDER BY flight_count DESC
        LIMIT ?;
        """,
        params=(dest, n),
    )


def plot_top_manufacturers_for_destination(dest: str, n: int = 5):
    df = top_manufacturers_for_destination(dest, n=n)
    fig = px.bar(
        df,
        x="manufacturer",
        y="flight_count",
        title=f"Top {n} manufacturers for flights to {dest}",
        labels={"manufacturer": "Manufacturer", "flight_count": "Number of flights"},
    )
    fig.update_xaxes(tickangle=45)
    return fig