from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from part3.db import query_df

MONTH_LABELS = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
    5: "May", 6: "Jun", 7: "Jul", 8: "Aug",
    9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}

# ---------------------------------------------------------------------------
# Carrier overview scorecard
# ---------------------------------------------------------------------------

def get_carrier_overview_df() -> pd.DataFrame:
    sql = """
        SELECT
            f.carrier,
            a.name AS airline,
            COUNT(*) AS total_flights,
            ROUND(AVG(CASE WHEN f.dep_delay <= 15 AND f.cancelled = 0 THEN 100.0 ELSE 0.0 END), 1) AS on_time_pct,
            ROUND(AVG(CASE WHEN f.dep_delay > 0 AND f.cancelled = 0 THEN f.dep_delay END), 1) AS avg_dep_delay,
            ROUND(AVG(CASE WHEN f.arr_delay > 0 AND f.cancelled = 0 THEN f.arr_delay END), 1) AS avg_arr_delay,
            ROUND(100.0 * SUM(f.cancelled) / COUNT(*), 2) AS cancellation_pct,
            ROUND(AVG(CASE WHEN f.cancelled = 0 THEN f.air_time END), 1) AS avg_air_time,
            ROUND(AVG(CASE WHEN f.cancelled = 0 THEN f.distance END), 0) AS avg_distance
        FROM flights f
        LEFT JOIN airlines a ON f.carrier = a.carrier
        GROUP BY f.carrier, a.name
        ORDER BY total_flights DESC
    """
    return query_df(sql)


# ---------------------------------------------------------------------------
# KPI aggregates for selected carriers + origin
# ---------------------------------------------------------------------------

def get_carrier_kpis(carriers: list[str], origin: str) -> dict:
    carrier_filter = "AND f.carrier IN ({})".format(
        ", ".join(f"'{c}'" for c in carriers)
    ) if carriers else ""
    origin_filter = f"AND f.origin = '{origin}'" if origin != "All" else ""

    sql = f"""
        SELECT
            COUNT(*) AS total_flights,
            ROUND(AVG(CASE WHEN f.dep_delay <= 15 AND f.cancelled = 0 THEN 100.0 ELSE 0.0 END), 1) AS on_time_pct,
            ROUND(AVG(CASE WHEN f.dep_delay > 0 AND f.cancelled = 0 THEN f.dep_delay END), 1) AS avg_dep_delay,
            ROUND(100.0 * SUM(f.cancelled) / COUNT(*), 2) AS cancellation_pct
        FROM flights f
        WHERE 1=1 {carrier_filter} {origin_filter}
    """
    df = query_df(sql)
    return df.iloc[0].to_dict()


# ---------------------------------------------------------------------------
# On-time / Slightly Late / Delayed / Cancelled breakdown per carrier
# ---------------------------------------------------------------------------

def get_carrier_status_breakdown_df(carriers: list[str], origin: str) -> pd.DataFrame:
    carrier_filter = "AND f.carrier IN ({})".format(
        ", ".join(f"'{c}'" for c in carriers)
    ) if carriers else ""
    origin_filter = f"AND f.origin = '{origin}'" if origin != "All" else ""

    sql = f"""
        SELECT
            f.carrier,
            a.name AS airline,
            ROUND(100.0 * SUM(CASE WHEN f.cancelled = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS cancelled_pct,
            ROUND(100.0 * SUM(CASE WHEN f.cancelled = 0 AND f.dep_delay > 15 THEN 1 ELSE 0 END) / COUNT(*), 2) AS delayed_pct,
            ROUND(100.0 * SUM(CASE WHEN f.cancelled = 0 AND f.dep_delay > 0 AND f.dep_delay <= 15 THEN 1 ELSE 0 END) / COUNT(*), 2) AS slightly_late_pct,
            ROUND(100.0 * SUM(CASE WHEN f.cancelled = 0 AND (f.dep_delay <= 0 OR f.dep_delay IS NULL) THEN 1 ELSE 0 END) / COUNT(*), 2) AS on_time_pct
        FROM flights f
        LEFT JOIN airlines a ON f.carrier = a.carrier
        WHERE 1=1 {carrier_filter} {origin_filter}
        GROUP BY f.carrier, a.name
        ORDER BY on_time_pct DESC
    """
    return query_df(sql)


# ---------------------------------------------------------------------------
# Average dep/arr delay per carrier
# ---------------------------------------------------------------------------

def get_carrier_avg_delay_df(carriers: list[str], origin: str) -> pd.DataFrame:
    carrier_filter = "AND f.carrier IN ({})".format(
        ", ".join(f"'{c}'" for c in carriers)
    ) if carriers else ""
    origin_filter = f"AND f.origin = '{origin}'" if origin != "All" else ""

    sql = f"""
        SELECT
            f.carrier,
            a.name AS airline,
            ROUND(AVG(CASE WHEN f.dep_delay > 0 AND f.cancelled = 0 THEN f.dep_delay END), 1) AS avg_dep_delay,
            ROUND(AVG(CASE WHEN f.arr_delay > 0 AND f.cancelled = 0 THEN f.arr_delay END), 1) AS avg_arr_delay
        FROM flights f
        LEFT JOIN airlines a ON f.carrier = a.carrier
        WHERE 1=1 {carrier_filter} {origin_filter}
        GROUP BY f.carrier, a.name
        ORDER BY avg_dep_delay DESC
    """
    return query_df(sql)


# ---------------------------------------------------------------------------
# Monthly on-time rate trend per carrier
# ---------------------------------------------------------------------------

def get_carrier_monthly_trend_df(carriers: list[str], origin: str) -> pd.DataFrame:
    carrier_filter = "AND f.carrier IN ({})".format(
        ", ".join(f"'{c}'" for c in carriers)
    ) if carriers else ""
    origin_filter = f"AND f.origin = '{origin}'" if origin != "All" else ""

    sql = f"""
        SELECT
            f.month,
            f.carrier,
            a.name AS airline,
            ROUND(AVG(CASE WHEN f.dep_delay <= 15 AND f.cancelled = 0 THEN 100.0 ELSE 0.0 END), 1) AS on_time_pct
        FROM flights f
        LEFT JOIN airlines a ON f.carrier = a.carrier
        WHERE 1=1 {carrier_filter} {origin_filter}
        GROUP BY f.month, f.carrier, a.name
        ORDER BY f.month, f.carrier
    """
    df = query_df(sql)
    df["month_label"] = df["month"].map(MONTH_LABELS)
    return df


# ---------------------------------------------------------------------------
# Flights per carrier per origin airport
# ---------------------------------------------------------------------------

def get_carrier_airport_share_df(carriers: list[str]) -> pd.DataFrame:
    carrier_filter = "AND f.carrier IN ({})".format(
        ", ".join(f"'{c}'" for c in carriers)
    ) if carriers else ""

    sql = f"""
        SELECT
            f.origin,
            f.carrier,
            a.name AS airline,
            COUNT(*) AS total_flights
        FROM flights f
        LEFT JOIN airlines a ON f.carrier = a.carrier
        WHERE 1=1 {carrier_filter}
        GROUP BY f.origin, f.carrier, a.name
        ORDER BY f.origin, total_flights DESC
    """
    return query_df(sql)


# ---------------------------------------------------------------------------
# Delay distribution buckets per carrier
# ---------------------------------------------------------------------------

def get_carrier_delay_buckets_df(carriers: list[str], origin: str) -> pd.DataFrame:
    carrier_filter = "AND f.carrier IN ({})".format(
        ", ".join(f"'{c}'" for c in carriers)
    ) if carriers else ""
    origin_filter = f"AND f.origin = '{origin}'" if origin != "All" else ""

    sql = f"""
        SELECT
            f.carrier,
            a.name AS airline,
            SUM(CASE WHEN f.dep_delay <= 0 THEN 1 ELSE 0 END) AS on_time_or_early,
            SUM(CASE WHEN f.dep_delay > 0 AND f.dep_delay <= 15 THEN 1 ELSE 0 END) AS delay_1_15,
            SUM(CASE WHEN f.dep_delay > 15 AND f.dep_delay <= 30 THEN 1 ELSE 0 END) AS delay_16_30,
            SUM(CASE WHEN f.dep_delay > 30 AND f.dep_delay <= 60 THEN 1 ELSE 0 END) AS delay_31_60,
            SUM(CASE WHEN f.dep_delay > 60 THEN 1 ELSE 0 END) AS delay_over_60
        FROM flights f
        LEFT JOIN airlines a ON f.carrier = a.carrier
        WHERE f.cancelled = 0 {carrier_filter} {origin_filter}
        GROUP BY f.carrier, a.name
    """
    return query_df(sql)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_all_carriers() -> pd.DataFrame:
    return query_df("SELECT carrier, name FROM airlines ORDER BY name")
