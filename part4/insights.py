"""
Standalone findings for the dashboard's general results tab.
Each function returns a DataFrame or matplotlib figure with no side effects.
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

DB_PATH = str(Path(__file__).parent.parent / 'data' / 'flights_database.db')


def _connect():
    return sqlite3.connect(DB_PATH)


# ---------------------------------------------------------------------------
# Delay insights
# ---------------------------------------------------------------------------

def most_delayed_airports(n: int = 10, role: str = 'origin') -> pd.DataFrame:
    """Airports ranked by average departure delay."""
    col = role if role in ('origin', 'dest') else 'origin'
    delay_col = 'dep_delay' if role == 'origin' else 'arr_delay'
    with _connect() as conn:
        return pd.read_sql_query(f"""
            SELECT
                {col}                              AS airport,
                COUNT(*)                           AS flights,
                ROUND(AVG({delay_col}), 2)         AS avg_delay_min,
                ROUND(100.0 * SUM(cancelled) / COUNT(*), 2) AS cancel_pct
            FROM flights
            WHERE {delay_col} IS NOT NULL
            GROUP BY {col}
            ORDER BY avg_delay_min DESC
            LIMIT ?
        """, conn, params=(n,))


def delay_by_carrier() -> pd.DataFrame:
    """Average departure and arrival delay per carrier, with flight counts."""
    with _connect() as conn:
        return pd.read_sql_query("""
            SELECT
                carrier,
                COUNT(*)                        AS flights,
                ROUND(AVG(dep_delay), 2)        AS avg_dep_delay,
                ROUND(AVG(arr_delay), 2)        AS avg_arr_delay,
                ROUND(100.0 * SUM(cancelled) / COUNT(*), 2) AS cancel_pct
            FROM flights
            GROUP BY carrier
            ORDER BY avg_dep_delay DESC
        """, conn)


def delay_by_month() -> pd.DataFrame:
    """Average departure delay and cancellation rate by month."""
    with _connect() as conn:
        return pd.read_sql_query("""
            SELECT
                month,
                COUNT(*)                        AS flights,
                ROUND(AVG(dep_delay), 2)        AS avg_dep_delay,
                ROUND(100.0 * SUM(cancelled) / COUNT(*), 2) AS cancel_pct
            FROM flights
            GROUP BY month
            ORDER BY month
        """, conn)


def delay_by_hour() -> pd.DataFrame:
    """Average departure delay by scheduled departure hour — shows typical day pattern."""
    with _connect() as conn:
        return pd.read_sql_query("""
            SELECT
                hour,
                COUNT(*)                        AS flights,
                ROUND(AVG(dep_delay), 2)        AS avg_dep_delay
            FROM flights
            WHERE cancelled = 0 AND dep_delay IS NOT NULL
            GROUP BY hour
            ORDER BY hour
        """, conn)


# ---------------------------------------------------------------------------
# Route insights
# ---------------------------------------------------------------------------

def busiest_routes(n: int = 15) -> pd.DataFrame:
    """Most frequently flown origin → dest pairs."""
    with _connect() as conn:
        return pd.read_sql_query("""
            SELECT
                origin, dest,
                COUNT(*)                        AS flights,
                ROUND(AVG(arr_delay), 2)        AS avg_arr_delay,
                ROUND(AVG(distance), 0)         AS distance_mi
            FROM flights
            GROUP BY origin, dest
            ORDER BY flights DESC
            LIMIT ?
        """, conn, params=(n,))


def longest_routes(n: int = 10) -> pd.DataFrame:
    """Longest routes by distance, with avg air time and speed."""
    with _connect() as conn:
        return pd.read_sql_query("""
            SELECT
                origin, dest,
                COUNT(*)                                       AS flights,
                ROUND(AVG(distance), 0)                        AS avg_distance_mi,
                ROUND(AVG(air_time), 1)                        AS avg_air_time_min,
                ROUND(AVG(distance) / AVG(air_time) * 60, 1)  AS avg_speed_mph
            FROM flights
            WHERE air_time IS NOT NULL AND cancelled = 0
            GROUP BY origin, dest
            ORDER BY avg_distance_mi DESC
            LIMIT ?
        """, conn, params=(n,))


# ---------------------------------------------------------------------------
# Plane / aircraft insights
# ---------------------------------------------------------------------------

def fastest_plane_types(min_flights: int = 200) -> pd.DataFrame:
    """Plane types ranked by average implied speed (distance / air_time)."""
    with _connect() as conn:
        return pd.read_sql_query("""
            SELECT
                p.type                                          AS plane_type,
                p.manufacturer,
                COUNT(*)                                        AS flights,
                ROUND(AVG(f.distance / f.air_time * 60), 1)    AS avg_speed_mph,
                ROUND(AVG(f.air_time), 1)                       AS avg_air_time_min
            FROM flights f
            JOIN planes p ON f.tailnum = p.tailnum
            WHERE f.air_time IS NOT NULL AND f.cancelled = 0
            GROUP BY p.type, p.manufacturer
            HAVING flights >= ?
            ORDER BY avg_speed_mph DESC
        """, conn, params=(min_flights,))


def manufacturer_delay_summary(min_flights: int = 500) -> pd.DataFrame:
    """Average delay by plane manufacturer — useful for spotting fleet patterns."""
    with _connect() as conn:
        return pd.read_sql_query("""
            SELECT
                p.manufacturer,
                COUNT(*)                        AS flights,
                ROUND(AVG(f.dep_delay), 2)      AS avg_dep_delay,
                ROUND(AVG(f.arr_delay), 2)      AS avg_arr_delay,
                ROUND(100.0 * SUM(f.cancelled) / COUNT(*), 2) AS cancel_pct
            FROM flights f
            JOIN planes p ON f.tailnum = p.tailnum
            GROUP BY p.manufacturer
            HAVING flights >= ?
            ORDER BY avg_dep_delay DESC
        """, conn, params=(min_flights,))


# ---------------------------------------------------------------------------
# Weather correlation
# ---------------------------------------------------------------------------

def weather_delay_correlation() -> pd.DataFrame:
    """
    Pearson-style summary: avg delay at each wind_speed / precip / visib bucket.
    Returns one row per weather condition bucket — good for a heatmap or scatter.
    """
    with _connect() as conn:
        return pd.read_sql_query("""
            SELECT
                ROUND(w.wind_speed / 5) * 5         AS wind_speed_bucket,
                ROUND(w.precip * 10) / 10           AS precip_bucket,
                COUNT(*)                            AS flights,
                ROUND(AVG(f.dep_delay), 2)          AS avg_dep_delay,
                ROUND(AVG(f.arr_delay), 2)          AS avg_arr_delay
            FROM flights f
            JOIN weather w
              ON f.origin = w.origin
             AND f.year   = w.year
             AND f.month  = w.month
             AND f.day    = w.day
             AND f.hour   = w.hour
            WHERE f.cancelled = 0
              AND w.wind_speed IS NOT NULL
              AND w.precip IS NOT NULL
            GROUP BY wind_speed_bucket, precip_bucket
            HAVING flights >= 30
            ORDER BY wind_speed_bucket, precip_bucket
        """, conn)


def visibility_vs_delay() -> pd.DataFrame:
    """Average delay at different visibility levels."""
    with _connect() as conn:
        return pd.read_sql_query("""
            SELECT
                ROUND(w.visib) AS visibility_mi,
                COUNT(*)       AS flights,
                ROUND(AVG(f.dep_delay), 2) AS avg_dep_delay,
                ROUND(AVG(f.arr_delay), 2) AS avg_arr_delay
            FROM flights f
            JOIN weather w
              ON f.origin = w.origin
             AND f.year   = w.year
             AND f.month  = w.month
             AND f.day    = w.day
             AND f.hour   = w.hour
            WHERE f.cancelled = 0 AND w.visib IS NOT NULL
            GROUP BY visibility_mi
            ORDER BY visibility_mi DESC
        """, conn)


def plot_delay_by_month() -> plt.Figure:
    """Line chart of avg departure delay and cancellation rate by month."""
    df = delay_by_month()

    fig, ax1 = plt.subplots(figsize=(9, 4))
    ax2 = ax1.twinx()

    ax1.bar(df['month'], df['avg_dep_delay'], color='steelblue', alpha=0.7, label='avg dep delay')
    ax2.plot(df['month'], df['cancel_pct'], color='tomato', marker='o', label='cancel %')

    ax1.set_xlabel('Month')
    ax1.set_ylabel('Avg departure delay (min)')
    ax2.set_ylabel('Cancellation rate (%)')
    ax1.set_xticks(range(1, 13))
    ax1.set_title('Departure delay and cancellation rate by month')

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2)
    plt.tight_layout()
    return fig


def plot_delay_by_hour() -> plt.Figure:
    """Bar chart showing how delays build up throughout the day."""
    df = delay_by_hour()

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(df['hour'], df['avg_dep_delay'], color='steelblue')
    ax.set_xlabel('Scheduled departure hour')
    ax.set_ylabel('Avg departure delay (min)')
    ax.set_title('Average departure delay by hour of day')
    ax.set_xticks(df['hour'])
    plt.tight_layout()
    return fig


def plot_delay_by_carrier() -> plt.Figure:
    """Horizontal bar chart of average departure delay per carrier."""
    df = delay_by_carrier().sort_values('avg_dep_delay')

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(df['carrier'], df['avg_dep_delay'], color='steelblue')
    ax.set_xlabel('Avg departure delay (min)')
    ax.set_title('Average departure delay by carrier')
    plt.tight_layout()
    return fig


def plot_visibility_vs_delay() -> plt.Figure:
    """Line chart: how delay changes as visibility drops."""
    df = visibility_vs_delay()

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(df['visibility_mi'], df['avg_dep_delay'], marker='o', color='steelblue', label='dep delay')
    ax.plot(df['visibility_mi'], df['avg_arr_delay'], marker='s', color='tomato', label='arr delay')
    ax.set_xlabel('Visibility (miles)')
    ax.set_ylabel('Avg delay (min)')
    ax.set_title('Visibility vs average delay')
    ax.invert_xaxis()  # low visibility on the right
    ax.legend()
    plt.tight_layout()
    return fig


if __name__ == '__main__':
    plot_delay_by_month()
    plot_delay_by_hour()
    plot_delay_by_carrier()
    plot_visibility_vs_delay()

    plt.show()