"""
Parameterised airport analysis functions for the dashboard.
Each function takes an airport code (and optional filters) and returns
a DataFrame or matplotlib figure — ready to plug into any frontend.
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

DB_PATH = str(Path(__file__).parent.parent / 'data' / 'flights_database.db')


def _connect():
    return sqlite3.connect(DB_PATH)


# ---------------------------------------------------------------------------
# Delay stats
# ---------------------------------------------------------------------------

def get_delay_stats(airport: str, role: str = 'origin') -> pd.DataFrame:
    """
    Return delay statistics for an airport as origin or destination.
    role: 'origin' or 'dest'
    """
    col = role if role in ('origin', 'dest') else 'origin'
    with _connect() as conn:
        df = pd.read_sql_query(f"""
            SELECT
                carrier,
                COUNT(*)                          AS total_flights,
                ROUND(AVG(dep_delay), 2)          AS avg_dep_delay,
                ROUND(AVG(arr_delay), 2)          AS avg_arr_delay,
                ROUND(AVG(CASE WHEN cancelled = 1 THEN 1.0 ELSE 0.0 END) * 100, 2)
                                                  AS cancel_pct,
                ROUND(AVG(air_time), 1)           AS avg_air_time
            FROM flights
            WHERE {col} = ?
              AND cancelled = 0
            GROUP BY carrier
            ORDER BY total_flights DESC
        """, conn, params=(airport,))
    return df


def get_cancellation_rate(airport: str, role: str = 'origin') -> pd.DataFrame:
    """Cancellation rate by month for an airport."""
    col = role if role in ('origin', 'dest') else 'origin'
    with _connect() as conn:
        df = pd.read_sql_query(f"""
            SELECT
                month,
                COUNT(*)                          AS total_flights,
                SUM(cancelled)                    AS cancelled_flights,
                ROUND(100.0 * SUM(cancelled) / COUNT(*), 2) AS cancel_pct
            FROM flights
            WHERE {col} = ?
            GROUP BY month
            ORDER BY month
        """, conn, params=(airport,))
    return df


def get_top_routes(airport: str, role: str = 'origin', n: int = 10) -> pd.DataFrame:
    """Most common routes from/to an airport."""
    if role == 'origin':
        select_col, where_col = 'dest', 'origin'
    else:
        select_col, where_col = 'origin', 'dest'

    with _connect() as conn:
        df = pd.read_sql_query(f"""
            SELECT
                {select_col}                       AS airport,
                COUNT(*)                           AS flights,
                ROUND(AVG(arr_delay), 2)           AS avg_arr_delay,
                ROUND(AVG(distance), 0)            AS avg_distance_mi
            FROM flights
            WHERE {where_col} = ?
              AND cancelled = 0
            GROUP BY {select_col}
            ORDER BY flights DESC
            LIMIT ?
        """, conn, params=(airport, n))
    return df


def get_weather_impact(airport: str) -> pd.DataFrame:
    """
    Average delay broken down by wind speed category for flights departing an airport.
    Joins flights with weather on origin + date + hour.
    """
    with _connect() as conn:
        df = pd.read_sql_query("""
            SELECT
                CASE
                    WHEN w.wind_speed < 10  THEN 'calm (<10)'
                    WHEN w.wind_speed < 20  THEN 'moderate (10-20)'
                    WHEN w.wind_speed < 30  THEN 'strong (20-30)'
                    ELSE                         'severe (30+)'
                END                             AS wind_category,
                COUNT(*)                        AS flights,
                ROUND(AVG(f.dep_delay), 2)      AS avg_dep_delay,
                ROUND(AVG(f.arr_delay), 2)      AS avg_arr_delay,
                ROUND(AVG(CASE WHEN f.cancelled = 1 THEN 1.0 ELSE 0.0 END) * 100, 2)
                                                AS cancel_pct
            FROM flights f
            JOIN weather w
              ON f.origin = w.origin
             AND f.year   = w.year
             AND f.month  = w.month
             AND f.day    = w.day
             AND f.hour   = w.hour
            WHERE f.origin = ?
              AND w.wind_speed IS NOT NULL
            GROUP BY wind_category
            ORDER BY MIN(w.wind_speed)
        """, conn, params=(airport,))
    return df


def get_route_summary(origin: str, dest: str) -> pd.DataFrame:
    """All key stats for a specific origin → dest pair."""
    with _connect() as conn:
        df = pd.read_sql_query("""
            SELECT
                carrier,
                COUNT(*)                        AS flights,
                ROUND(AVG(dep_delay), 2)        AS avg_dep_delay,
                ROUND(AVG(arr_delay), 2)        AS avg_arr_delay,
                ROUND(AVG(air_time), 1)         AS avg_air_time_min,
                ROUND(AVG(distance), 0)         AS distance_mi,
                ROUND(AVG(CASE WHEN cancelled = 1 THEN 1.0 ELSE 0.0 END) * 100, 2)
                                                AS cancel_pct
            FROM flights
            WHERE origin = ? AND dest = ?
            GROUP BY carrier
            ORDER BY flights DESC
        """, conn, params=(origin, dest))
    return df


# ---------------------------------------------------------------------------
# Plotting helpers
# ---------------------------------------------------------------------------

def plot_delay_by_month(airport: str, role: str = 'origin') -> plt.Figure:
    """Bar chart of average departure delay by month for an airport."""
    col = role if role in ('origin', 'dest') else 'origin'
    with _connect() as conn:
        df = pd.read_sql_query(f"""
            SELECT month, ROUND(AVG(dep_delay), 2) AS avg_dep_delay
            FROM flights
            WHERE {col} = ? AND cancelled = 0 AND dep_delay IS NOT NULL
            GROUP BY month ORDER BY month
        """, conn, params=(airport,))

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(df['month'], df['avg_dep_delay'], color='steelblue')
    ax.set_xlabel('Month')
    ax.set_ylabel('Avg departure delay (min)')
    ax.set_title(f'Average departure delay by month — {airport}')
    ax.set_xticks(range(1, 13))
    plt.tight_layout()
    return fig


def plot_top_routes(airport: str, role: str = 'origin', n: int = 10) -> plt.Figure:
    """Horizontal bar chart of the busiest routes from/to an airport."""
    df = get_top_routes(airport, role=role, n=n)
    label = 'from' if role == 'origin' else 'to'

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(df['airport'], df['flights'], color='steelblue')
    ax.set_xlabel('Number of flights')
    ax.set_title(f'Top {n} routes {label} {airport}')
    ax.invert_yaxis()
    plt.tight_layout()
    return fig


def plot_weather_impact(airport: str) -> plt.Figure:
    """Grouped bar chart: avg dep/arr delay by wind category for an airport."""
    df = get_weather_impact(airport)

    x = range(len(df))
    width = 0.35
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar([i - width / 2 for i in x], df['avg_dep_delay'], width, label='dep delay', color='steelblue')
    ax.bar([i + width / 2 for i in x], df['avg_arr_delay'], width, label='arr delay', color='tomato')
    ax.set_xticks(list(x))
    ax.set_xticklabels(df['wind_category'])
    ax.set_ylabel('Avg delay (min)')
    ax.set_title(f'Wind speed vs delays — {airport}')
    ax.legend()
    plt.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Quick demo
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    for airport in ('JFK', 'EWR', 'LGA'):
        plot_delay_by_month(airport)
        plot_top_routes(airport)
        plot_weather_impact(airport)

    plt.show()
