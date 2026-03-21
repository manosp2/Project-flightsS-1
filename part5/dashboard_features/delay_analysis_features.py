from __future__ import annotations

import numpy as np
import pandas as pd

from part3.db import query_df
from part3.wind_speed_analysis import bearing_deg, wind_dot_flight


MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTH_TO_NUM = {m: i + 1 for i, m in enumerate(MONTH_LABELS)}


def build_placeholders(values: list) -> str:
    return ",".join(["?"] * len(values))


def build_day_filter_sql(day_sql: str, alias: str) -> str:
    return (
        day_sql.replace("AND year", f"AND {alias}.year")
               .replace("AND month", f"AND {alias}.month")
               .replace("AND day", f"AND {alias}.day")
    )


def hour_to_label(h: int) -> str:
    if h == 0:
        return "12 AM"
    if h < 12:
        return f"{h} AM"
    if h == 12:
        return "12 PM"
    return f"{h - 12} PM"


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


def get_base_params(
    origins: list[str],
    months: list[int],
    day_params: list,
    dest_filter: str | None,
) -> tuple:
    params = [*origins, *months, *day_params]
    if dest_filter is not None:
        params.append(dest_filter)
    return tuple(params)


def get_base_filters_sql(
    origins: list[str],
    months: list[int],
    day_sql: str,
    dest_filter: str | None,
    table_alias: str = "",
) -> tuple[str, str, str]:
    prefix = f"{table_alias}." if table_alias else ""
    o_ph = build_placeholders(origins)
    m_ph = build_placeholders(months)

    dest_sql = ""
    if dest_filter is not None:
        dest_sql = f"AND {prefix}dest = ?"

    if table_alias:
        day_sql = build_day_filter_sql(day_sql, table_alias)

    base_sql = f"""
        WHERE {prefix}origin IN ({o_ph})
          AND {prefix}month IN ({m_ph})
          {day_sql}
          {dest_sql}
    """
    return o_ph, m_ph, base_sql


def get_kpi_summary(
    origins: list[str],
    months: list[int],
    dest_filter: str | None,
    day_sql: str,
    day_params: list,
) -> pd.Series:
    _, _, base_sql = get_base_filters_sql(origins, months, day_sql, dest_filter)
    params = get_base_params(origins, months, day_params, dest_filter)

    df = query_df(
        f"""
        SELECT
            COUNT(*) AS total_flights,
            SUM(CASE WHEN dep_delay IS NOT NULL AND dep_delay > 0 THEN 1 ELSE 0 END) AS delayed_flights,
            ROUND(AVG(CASE WHEN dep_delay IS NOT NULL THEN dep_delay END), 2) AS avg_dep_delay,
            ROUND(
                100.0 * SUM(CASE WHEN dep_delay IS NOT NULL AND dep_delay > 15 THEN 1 ELSE 0 END)
                / NULLIF(SUM(CASE WHEN dep_delay IS NOT NULL THEN 1 ELSE 0 END), 0),
                2
            ) AS pct_delayed_15,
            ROUND(
                100.0 * SUM(CASE WHEN dep_delay IS NOT NULL AND dep_delay > 30 THEN 1 ELSE 0 END)
                / NULLIF(SUM(CASE WHEN dep_delay IS NOT NULL THEN 1 ELSE 0 END), 0),
                2
            ) AS pct_delayed_30
        FROM flights
        {base_sql};
        """,
        params=params,
    )
    return df.iloc[0]


def get_delay_values(
    origins: list[str],
    months: list[int],
    dest_filter: str | None,
    day_sql: str,
    day_params: list,
) -> pd.DataFrame:
    _, _, base_sql = get_base_filters_sql(origins, months, day_sql, dest_filter)
    params = get_base_params(origins, months, day_params, dest_filter)

    return query_df(
        f"""
        SELECT dep_delay
        FROM flights
        {base_sql}
          AND dep_delay IS NOT NULL;
        """,
        params=params,
    )


def get_delay_histogram_df(
    origins: list[str],
    months: list[int],
    dest_filter: str | None,
    day_sql: str,
    day_params: list,
    max_delay_cap: int,
) -> pd.DataFrame:
    _, _, base_sql = get_base_filters_sql(origins, months, day_sql, dest_filter)
    params = [*get_base_params(origins, months, day_params, dest_filter), int(max_delay_cap)]

    return query_df(
        f"""
        SELECT dep_delay
        FROM flights
        {base_sql}
          AND dep_delay IS NOT NULL
          AND dep_delay BETWEEN -60 AND ?;
        """,
        params=tuple(params),
    )


def get_carrier_delay_df(
    origins: list[str],
    months: list[int],
    dest_filter: str | None,
    day_sql: str,
    day_params: list,
) -> pd.DataFrame:
    _, _, base_sql = get_base_filters_sql(origins, months, day_sql, dest_filter, table_alias="f")
    params = get_base_params(origins, months, day_params, dest_filter)

    return query_df(
        f"""
        SELECT
            a.name AS airline,
            f.carrier,
            COUNT(*) AS flights,
            ROUND(AVG(f.dep_delay), 2) AS avg_dep_delay,
            ROUND(AVG(f.arr_delay), 2) AS avg_arr_delay
        FROM flights f
        JOIN airlines a
            ON f.carrier = a.carrier
        {base_sql}
          AND f.dep_delay IS NOT NULL
        GROUP BY a.name, f.carrier
        HAVING COUNT(*) >= 500
        ORDER BY avg_dep_delay DESC
        LIMIT 15;
        """,
        params=params,
    )


def get_routes_delay_df(
    origins: list[str],
    months: list[int],
    dest_filter: str | None,
    day_sql: str,
    day_params: list,
) -> pd.DataFrame:
    _, _, base_sql = get_base_filters_sql(origins, months, day_sql, dest_filter)
    params = get_base_params(origins, months, day_params, dest_filter)

    df = query_df(
        f"""
        SELECT
            origin,
            dest,
            COUNT(*) AS number_of_flights,
            ROUND(AVG(CASE WHEN dep_delay IS NOT NULL THEN dep_delay END), 2) AS avg_dep_delay
        FROM flights
        {base_sql}
          AND dep_delay IS NOT NULL
        GROUP BY origin, dest
        HAVING COUNT(*) >= 200
        ORDER BY avg_dep_delay DESC
        LIMIT 10;
        """,
        params=params,
    )

    if not df.empty:
        df["route"] = df["origin"] + " → " + df["dest"]

    return df


def get_time_of_day_df(
    origins: list[str],
    months: list[int],
    dest_filter: str | None,
    day_sql: str,
    day_params: list,
) -> pd.DataFrame:
    _, _, base_sql = get_base_filters_sql(origins, months, day_sql, dest_filter)
    params = get_base_params(origins, months, day_params, dest_filter)

    df = query_df(
        f"""
        SELECT
            CAST(sched_dep_time / 100 AS INT) AS dep_hour,
            ROUND(AVG(CASE WHEN dep_delay IS NOT NULL THEN dep_delay END), 2) AS avg_dep_delay,
            COUNT(*) AS flights
        FROM flights
        {base_sql}
          AND sched_dep_time IS NOT NULL
        GROUP BY dep_hour
        ORDER BY dep_hour;
        """,
        params=params,
    )

    if not df.empty:
        df["dep_hour_label"] = df["dep_hour"].apply(hour_to_label)

    return df


def get_wind_category_df(
    origins: list[str],
    months: list[int],
    dest_filter: str | None,
    day_sql: str,
    day_params: list,
) -> pd.DataFrame:
    params = get_base_params(origins, months, day_params, dest_filter)

    return query_df(
        f"""
        WITH f2 AS (
            SELECT
                origin, dest, year, month, day,
                CAST(sched_dep_time / 100 AS INT) AS sched_hour,
                dep_delay, arr_delay
            FROM flights
            WHERE origin IN ({build_placeholders(origins)})
              AND month IN ({build_placeholders(months)})
              {day_sql}
              {"AND dest = ?" if dest_filter is not None else ""}
              AND sched_dep_time IS NOT NULL
        )
        SELECT
            CASE
                WHEN w.wind_speed < 10  THEN 'Calm (<10 mph)'
                WHEN w.wind_speed < 20  THEN 'Moderate (10-20 mph)'
                WHEN w.wind_speed < 30  THEN 'Strong (20-30 mph)'
                ELSE 'Severe (30+ mph)'
            END AS wind_category,
            COUNT(*) AS flights,
            ROUND(AVG(f2.dep_delay), 2) AS avg_dep_delay,
            ROUND(AVG(f2.arr_delay), 2) AS avg_arr_delay
        FROM f2
        JOIN weather w
          ON f2.origin = w.origin
         AND f2.year   = w.year
         AND f2.month  = w.month
         AND f2.day    = w.day
         AND f2.sched_hour = w.hour
        WHERE w.wind_speed IS NOT NULL
          AND f2.dep_delay IS NOT NULL
        GROUP BY wind_category
        ORDER BY MIN(w.wind_speed);
        """,
        params=params,
    )


def get_wind_sign_summary_filtered(
    origins: list[str],
    months: list[int],
    dest_filter: str | None,
    day_sql: str,
    day_params: list,
) -> pd.DataFrame:
    o_ph = build_placeholders(origins)
    m_ph = build_placeholders(months)

    dest_sql = ""
    params = [*origins, *months, *day_params]
    if dest_filter is not None:
        dest_sql = "AND f.dest = ?"
        params.append(dest_filter)

    day_sql_f = build_day_filter_sql(day_sql, "f")

    df = query_df(
        f"""
        SELECT f.origin, f.dest, f.air_time, f.distance, w.wind_dir, w.wind_speed
        FROM flights f
        JOIN weather w
          ON w.origin = f.origin
         AND w.time_hour = f.time_hour
        WHERE f.origin IN ({o_ph})
          AND f.month IN ({m_ph})
          {day_sql_f}
          {dest_sql}
          AND f.air_time IS NOT NULL AND f.air_time > 0
          AND f.distance IS NOT NULL
          AND w.wind_dir IS NOT NULL
          AND w.wind_speed IS NOT NULL
        """,
        params=tuple(params),
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
    df["dot"] = df.apply(
        lambda r: wind_dot_flight(r["bearing"], r["wind_dir"], r["wind_speed"]),
        axis=1,
    )

    df["wind_relation"] = np.where(
        df["dot"] > 0,
        "Tailwind",
        np.where(df["dot"] < 0, "Headwind", "Neutral"),
    )

    summary = (
        df.groupby("wind_relation", as_index=False)
        .agg(
            flights=("air_time", "size"),
            mean_air_time=("air_time", "mean"),
            mean_distance=("distance", "mean"),
            mean_dot=("dot", "mean"),
        )
    )

    order = pd.Categorical(summary["wind_relation"], ["Headwind", "Neutral", "Tailwind"], ordered=True)
    summary["wind_relation"] = order
    summary = summary.sort_values("wind_relation")
    summary["wind_relation"] = summary["wind_relation"].astype(str)

    return summary


def get_precipitation_df(
    origins: list[str],
    months: list[int],
    dest_filter: str | None,
    day_sql: str,
    day_params: list,
) -> pd.DataFrame:
    params = get_base_params(origins, months, day_params, dest_filter)

    return query_df(
        f"""
        WITH f2 AS (
            SELECT
                origin, dest, year, month, day,
                CAST(sched_dep_time / 100 AS INT) AS sched_hour,
                dep_delay
            FROM flights
            WHERE origin IN ({build_placeholders(origins)})
              AND month IN ({build_placeholders(months)})
              {day_sql}
              {"AND dest = ?" if dest_filter is not None else ""}
              AND sched_dep_time IS NOT NULL
        )
        SELECT
            CASE
                WHEN w.precip <= 0     THEN 'None (0 in)'
                WHEN w.precip <= 0.1   THEN 'Light (0–0.1 in/hr)'
                WHEN w.precip <= 0.5   THEN 'Moderate (0.1–0.5 in/hr)'
                ELSE 'Heavy (>0.5 in/hr)'
            END AS precip_category,
            COUNT(*) AS flights,
            ROUND(AVG(f2.dep_delay), 2) AS avg_dep_delay
        FROM f2
        JOIN weather w
          ON f2.origin = w.origin
         AND f2.year   = w.year
         AND f2.month  = w.month
         AND f2.day    = w.day
         AND f2.sched_hour = w.hour
        WHERE w.precip IS NOT NULL
          AND f2.dep_delay IS NOT NULL
        GROUP BY precip_category
        ORDER BY AVG(w.precip)
        """,
        params=params,
    )


def get_weather_delay_correlation_filtered(
    origins: list[str],
    months: list[int],
    dest_filter: str | None,
    day_sql: str,
    day_params: list,
) -> pd.DataFrame:
    o_ph = build_placeholders(origins)
    m_ph = build_placeholders(months)

    dest_sql = ""
    params = [*origins, *months, *day_params]
    if dest_filter is not None:
        dest_sql = "AND f.dest = ?"
        params.append(dest_filter)

    day_sql_f = build_day_filter_sql(day_sql, "f")

    return query_df(
        f"""
        SELECT
            ROUND(w.wind_speed / 5.0) * 5 AS wind_speed_bucket,
            ROUND(w.precip * 10.0) / 10.0 AS precip_bucket,
            COUNT(*) AS flights,
            ROUND(AVG(f.dep_delay), 2) AS avg_dep_delay,
            ROUND(AVG(f.arr_delay), 2) AS avg_arr_delay
        FROM flights f
        JOIN weather w
          ON f.origin = w.origin
         AND f.year   = w.year
         AND f.month  = w.month
         AND f.day    = w.day
         AND f.hour   = w.hour
        WHERE f.origin IN ({o_ph})
          AND f.month IN ({m_ph})
          {day_sql_f}
          {dest_sql}
          AND w.wind_speed IS NOT NULL
          AND w.precip IS NOT NULL
        GROUP BY wind_speed_bucket, precip_bucket
        HAVING flights >= 30
        ORDER BY wind_speed_bucket, precip_bucket
        """,
        params=tuple(params),
    )


def get_visibility_df(
    origins: list[str],
    months: list[int],
    dest_filter: str | None,
    day_sql: str,
    day_params: list,
) -> pd.DataFrame:
    params = get_base_params(origins, months, day_params, dest_filter)

    return query_df(
        f"""
        WITH f2 AS (
            SELECT
                origin, dest, year, month, day,
                CAST(sched_dep_time / 100 AS INT) AS sched_hour,
                dep_delay
            FROM flights
            WHERE origin IN ({build_placeholders(origins)})
              AND month IN ({build_placeholders(months)})
              {day_sql}
              {"AND dest = ?" if dest_filter is not None else ""}
              AND sched_dep_time IS NOT NULL
        )
        SELECT
            CASE
                WHEN w.visib < 2 THEN 'Poor (<2 mi)'
                WHEN w.visib < 5 THEN 'Low (2–5 mi)'
                WHEN w.visib < 8 THEN 'Moderate (5–8 mi)'
                ELSE 'Good (>8 mi)'
            END AS vis_category,
            COUNT(*) AS flights,
            ROUND(AVG(f2.dep_delay), 2) AS avg_dep_delay
        FROM f2
        JOIN weather w
          ON f2.origin = w.origin
         AND f2.year   = w.year
         AND f2.month  = w.month
         AND f2.day    = w.day
         AND f2.sched_hour = w.hour
        WHERE w.visib IS NOT NULL
          AND f2.dep_delay IS NOT NULL
        GROUP BY vis_category
        ORDER BY
            CASE vis_category
                WHEN 'Poor (<2 mi)' THEN 0
                WHEN 'Low (2–5 mi)' THEN 1
                WHEN 'Moderate (5–8 mi)' THEN 2
                ELSE 3
            END
        """,
        params=params,
    )


def get_distance_delay_df(
    origins: list[str],
    months: list[int],
    dest_filter: str | None,
    day_sql: str,
    day_params: list,
) -> pd.DataFrame:
    _, _, base_sql = get_base_filters_sql(origins, months, day_sql, dest_filter)
    params = get_base_params(origins, months, day_params, dest_filter)

    return query_df(
        f"""
        SELECT
            CASE
                WHEN distance < 500 THEN '0–500'
                WHEN distance < 1000 THEN '500–1000'
                WHEN distance < 1500 THEN '1000–1500'
                WHEN distance < 2000 THEN '1500–2000'
                ELSE '2000+'
            END AS distance_range,
            COUNT(*) AS flights,
            ROUND(AVG(dep_delay), 2) AS avg_dep_delay
        FROM flights
        {base_sql}
          AND distance IS NOT NULL
          AND dep_delay IS NOT NULL
        GROUP BY distance_range
        ORDER BY MIN(distance);
        """,
        params=params,
    )


def get_manufacturer_delay_summary_filtered(
    origins: list[str],
    months: list[int],
    dest_filter: str | None,
    day_sql: str,
    day_params: list,
    min_flights: int = 500,
) -> pd.DataFrame:
    _, _, base_sql = get_base_filters_sql(origins, months, day_sql, dest_filter, table_alias="f")
    params = [*get_base_params(origins, months, day_params, dest_filter), min_flights]

    return query_df(
        f"""
        SELECT
            p.manufacturer,
            COUNT(*) AS flights,
            ROUND(AVG(f.dep_delay), 2) AS avg_dep_delay,
            ROUND(AVG(f.arr_delay), 2) AS avg_arr_delay,
            ROUND(
                100.0 * SUM(CASE WHEN f.dep_time IS NULL AND f.arr_time IS NULL THEN 1 ELSE 0 END) / COUNT(*),
                2
            ) AS cancel_pct
        FROM flights f
        JOIN planes p
          ON f.tailnum = p.tailnum
        {base_sql}
          AND p.manufacturer IS NOT NULL
        GROUP BY p.manufacturer
        HAVING flights >= ?
        ORDER BY avg_dep_delay DESC
        """,
        params=tuple(params),
    )