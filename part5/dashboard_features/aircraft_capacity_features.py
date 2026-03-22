from __future__ import annotations

import pandas as pd
from part3.db import query_df

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTH_TO_NUM = {m: i + 1 for i, m in enumerate(MONTH_LABELS)}


def get_destinations() -> list[str]:
    df = query_df(
        """
        SELECT DISTINCT dest
        FROM flights
        WHERE dest IS NOT NULL
        ORDER BY dest
        """
    )
    return df["dest"].dropna().tolist()


def build_placeholders(values: list) -> str:
    return ",".join(["?"] * len(values))


def _filter_sql(
    origins: list[str],
    months: list[int],
    dest_filter: str | None,
):
    origin_ph = build_placeholders(origins)
    month_ph = build_placeholders(months)

    params = [*origins, *months]
    dest_sql = ""

    if dest_filter is not None:
        dest_sql = "AND f.dest = ?"
        params.append(dest_filter)

    where_sql = f"""
        WHERE f.origin IN ({origin_ph})
          AND f.month IN ({month_ph})
          {dest_sql}
            AND f.dep_time IS NOT NULL
          AND p.seats IS NOT NULL
    """
    return where_sql, tuple(params)


def get_capacity_kpis(
    origins: list[str],
    months: list[int],
    dest_filter: str | None,
) -> dict:
    where_sql, params = _filter_sql(origins, months, dest_filter)

    df = query_df(
        f"""
        SELECT
            COUNT(*) AS flights,
            ROUND(AVG(p.seats), 2) AS avg_seats,
            ROUND(SUM(p.seats), 0) AS est_passenger_capacity,
            COUNT(DISTINCT f.carrier) AS airlines,
            COUNT(DISTINCT f.dest) AS destinations
        FROM flights f
        JOIN planes p
          ON f.tailnum = p.tailnum
        {where_sql}
        """,
        params=params
    )

    if df.empty:
        return {
            "flights": 0,
            "avg_seats": 0.0,
            "est_passenger_capacity": 0,
            "airlines": 0,
            "destinations": 0,
        }

    row = df.iloc[0]
    return {
        "flights": int(row["flights"]) if pd.notna(row["flights"]) else 0,
        "avg_seats": float(row["avg_seats"]) if pd.notna(row["avg_seats"]) else 0.0,
        "est_passenger_capacity": int(row["est_passenger_capacity"]) if pd.notna(row["est_passenger_capacity"]) else 0,
        "airlines": int(row["airlines"]) if pd.notna(row["airlines"]) else 0,
        "destinations": int(row["destinations"]) if pd.notna(row["destinations"]) else 0,
    }


def get_airport_capacity_df(
    months: list[int],
    dest_filter: str | None,
) -> pd.DataFrame:
    origins = ["JFK", "LGA", "EWR"]
    where_sql, params = _filter_sql(origins, months, dest_filter)

    return query_df(
        f"""
        SELECT
            f.origin,
            COUNT(*) AS flights,
            ROUND(AVG(p.seats), 2) AS avg_seats,
            ROUND(SUM(p.seats), 0) AS est_passenger_capacity
        FROM flights f
        JOIN planes p
          ON f.tailnum = p.tailnum
        {where_sql}
        GROUP BY f.origin
        ORDER BY est_passenger_capacity DESC
        """,
        params=params
    )


def get_airline_capacity_df(
    origins: list[str],
    months: list[int],
    dest_filter: str | None,
    min_flights: int = 100,
) -> pd.DataFrame:
    where_sql, params = _filter_sql(origins, months, dest_filter)

    return query_df(
        f"""
        SELECT
            COALESCE(a.name, f.carrier) AS airline,
            f.carrier,
            COUNT(*) AS flights,
            ROUND(AVG(p.seats), 2) AS avg_seats,
            ROUND(SUM(p.seats), 0) AS est_passenger_capacity
        FROM flights f
        JOIN planes p
          ON f.tailnum = p.tailnum
        LEFT JOIN airlines a
          ON f.carrier = a.carrier
        {where_sql}
        GROUP BY COALESCE(a.name, f.carrier), f.carrier
        HAVING COUNT(*) >= ?
        ORDER BY est_passenger_capacity DESC
        """,
        params=tuple([*params, min_flights])
    )


def get_route_capacity_df(
    origins: list[str],
    months: list[int],
    dest_filter: str | None,
    top_n: int = 10,
) -> pd.DataFrame:
    where_sql, params = _filter_sql(origins, months, dest_filter)

    df = query_df(
        f"""
        SELECT
            f.origin,
            f.dest,
            COUNT(*) AS flights,
            ROUND(AVG(p.seats), 2) AS avg_seats,
            ROUND(SUM(p.seats), 0) AS est_passenger_capacity
        FROM flights f
        JOIN planes p
          ON f.tailnum = p.tailnum
        {where_sql}
        GROUP BY f.origin, f.dest
        HAVING COUNT(*) >= 20
        ORDER BY est_passenger_capacity DESC
        LIMIT ?
        """,
        params=tuple([*params, top_n])
    )

    if not df.empty:
        df["route"] = df["origin"] + " → " + df["dest"]

    return df


def get_monthly_capacity_df(
    origins: list[str],
    dest_filter: str | None,
) -> pd.DataFrame:
    origin_ph = build_placeholders(origins)
    params = [*origins]
    dest_sql = ""

    if dest_filter is not None:
        dest_sql = "AND f.dest = ?"
        params.append(dest_filter)

    df = query_df(
        f"""
        SELECT
            f.month,
            ROUND(SUM(p.seats), 0) AS est_passenger_capacity
        FROM flights f
        JOIN planes p
          ON f.tailnum = p.tailnum
        WHERE f.origin IN ({origin_ph})
          {dest_sql}
                    AND f.dep_time IS NOT NULL
          AND p.seats IS NOT NULL
        GROUP BY f.month
        ORDER BY f.month
        """,
        params=tuple(params)
    )

    if not df.empty:
        month_map = {i + 1: m for i, m in enumerate(MONTH_LABELS)}
        df["month_label"] = df["month"].map(month_map)

    return df


def get_capacity_conclusion_text(kpis: dict) -> str:
    if kpis["flights"] == 0:
        return "No aircraft capacity data is available for the selected filters."

    return (
        f"This filtered view contains <b>{kpis['flights']:,} flights</b> linked to aircraft records, "
        f"representing an estimated <b>{kpis['est_passenger_capacity']:,} seats</b> and an average aircraft size of "
        f"<b>{kpis['avg_seats']:.1f} seats</b>. These values are used as a proxy for potential passenger throughput, not exact passenger counts."
    )