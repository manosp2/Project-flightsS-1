from __future__ import annotations

import pandas as pd

from part3.db import query_df

NYC_AIRPORTS = ["JFK", "LGA", "EWR"]

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


def get_comparison_kpis(
    months: list[int],
    day_sql: str,
    day_params: list,
    dest: str | None
) -> pd.DataFrame:
    m_ph = build_placeholders(months)
    dest_sql = ""
    params = [*months, *day_params]

    if dest is not None:
        dest_sql = "AND dest = ?"
        params.append(dest)

    return query_df(
        f"""
        SELECT
            origin,
            COUNT(*) AS total_flights,
            ROUND(AVG(dep_delay), 2) AS avg_dep_delay,
            ROUND(AVG(arr_delay), 2) AS avg_arr_delay,
            ROUND(
                100.0 * SUM(CASE WHEN dep_delay IS NOT NULL AND dep_delay > 15 THEN 1 ELSE 0 END)
                / NULLIF(SUM(CASE WHEN dep_delay IS NOT NULL THEN 1 ELSE 0 END), 0),
                2
            ) AS pct_dep_delay_15,
            ROUND(
                100.0 * SUM(CASE WHEN dep_delay IS NOT NULL AND dep_delay > 30 THEN 1 ELSE 0 END)
                / NULLIF(SUM(CASE WHEN dep_delay IS NOT NULL THEN 1 ELSE 0 END), 0),
                2
            ) AS pct_dep_delay_30
        FROM flights
        WHERE origin IN ('JFK', 'LGA', 'EWR')
          AND month IN ({m_ph})
          {day_sql}
          {dest_sql}
        GROUP BY origin
        ORDER BY origin;
        """,
        params=tuple(params)
    )


def get_cancellation_rate_df(
    months: list[int],
    day_sql: str,
    day_params: list,
    dest: str | None
) -> pd.DataFrame:
    m_ph = build_placeholders(months)
    dest_sql = ""
    params = [*months, *day_params]

    if dest is not None:
        dest_sql = "AND dest = ?"
        params.append(dest)

    if day_sql:
        return query_df(
            f"""
            SELECT
                origin,
                ROUND(
                    100.0 * SUM(CASE WHEN dep_time IS NULL AND arr_time IS NULL THEN 1 ELSE 0 END) / COUNT(*),
                    2
                ) AS cancellation_rate
            FROM flights
            WHERE origin IN ('JFK', 'LGA', 'EWR')
              AND month IN ({m_ph})
              {day_sql}
              {dest_sql}
            GROUP BY origin
            ORDER BY origin;
            """,
            params=tuple(params)
        )

    df = query_df(
        f"""
        SELECT
            origin,
            month,
            ROUND(
                100.0 * SUM(CASE WHEN dep_time IS NULL AND arr_time IS NULL THEN 1 ELSE 0 END) / COUNT(*),
                2
            ) AS cancellation_rate
        FROM flights
        WHERE origin IN ('JFK', 'LGA', 'EWR')
          AND month IN ({m_ph})
          {dest_sql}
        GROUP BY origin, month
        ORDER BY month, origin;
        """,
        params=tuple([*months] + ([dest] if dest is not None else []))
    )

    if not df.empty:
        month_map = {
            1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
            7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
        }
        df["month_label"] = df["month"].map(month_map)

    return df


def get_top_routes_by_airport(
    months: list[int],
    day_sql: str,
    day_params: list,
    dest: str | None,
    n: int = 5
) -> pd.DataFrame:
    m_ph = build_placeholders(months)
    dest_sql = ""
    params = [*months, *day_params]

    if dest is not None:
        dest_sql = "AND dest = ?"
        params.append(dest)

    df = query_df(
        f"""
        SELECT
            origin,
            dest,
            COUNT(*) AS flights
        FROM flights
        WHERE origin IN ('JFK', 'LGA', 'EWR')
          AND month IN ({m_ph})
          {day_sql}
          {dest_sql}
        GROUP BY origin, dest
        ORDER BY origin, flights DESC;
        """,
        params=tuple(params)
    )

    if df.empty:
        return df

    df = df.groupby("origin", group_keys=False).head(n).reset_index(drop=True)
    df["route"] = df["origin"] + " → " + df["dest"]
    return df


def get_weather_impact_by_airport_df(
    months: list[int],
    day_sql: str,
    day_params: list,
    dest: str | None
) -> pd.DataFrame:
    m_ph = build_placeholders(months)
    dest_sql = ""
    params = [*months, *day_params]

    if dest is not None:
        dest_sql = "AND f.dest = ?"
        params.append(dest)

    day_sql_f = build_day_filter_sql(day_sql, "f")

    return query_df(
        f"""
        WITH f2 AS (
            SELECT
                f.origin,
                f.dest,
                f.year,
                f.month,
                f.day,
                CAST(f.sched_dep_time / 100 AS INT) AS sched_hour,
                f.dep_delay
            FROM flights f
            WHERE f.origin IN ('JFK', 'LGA', 'EWR')
              AND f.month IN ({m_ph})
              {day_sql_f}
              {dest_sql}
              AND f.sched_dep_time IS NOT NULL
              AND f.dep_delay IS NOT NULL
        )
        SELECT
            f2.origin,
            CASE
                WHEN w.wind_speed < 10 THEN 'Calm'
                WHEN w.wind_speed < 20 THEN 'Moderate'
                ELSE 'Strong'
            END AS wind_category,
            ROUND(AVG(f2.dep_delay), 2) AS avg_dep_delay
        FROM f2
        JOIN weather w
          ON f2.origin = w.origin
         AND f2.year = w.year
         AND f2.month = w.month
         AND f2.day = w.day
         AND f2.sched_hour = w.hour
        WHERE w.wind_speed IS NOT NULL
        GROUP BY f2.origin, wind_category
        ORDER BY f2.origin, wind_category;
        """,
        params=tuple(params)
    )


def get_kpi_takeaway_text(kpi_df: pd.DataFrame) -> str:
    if kpi_df.empty:
        return "No KPI comparison data is available for the selected filters."

    busiest = kpi_df.sort_values("total_flights", ascending=False).iloc[0]
    highest_delay = kpi_df.sort_values("avg_dep_delay", ascending=False).iloc[0]
    lowest_delay = kpi_df.sort_values("avg_dep_delay", ascending=True).iloc[0]

    return (
        f"<b>{busiest['origin']}</b> is the busiest airport in the current filtered view, while "
        f"<b>{highest_delay['origin']}</b> has the highest average departure delay "
        f"(<b>{float(highest_delay['avg_dep_delay']):.1f} min</b>). "
        f"<b>{lowest_delay['origin']}</b> is currently the most delay-efficient of the three."
    )


def get_cancellation_conclusion_text(cancel_df: pd.DataFrame, use_specific_day: bool) -> str:
    if cancel_df.empty:
        return "No cancellation data is available for the selected filters."

    if use_specific_day:
        worst = cancel_df.sort_values("cancellation_rate", ascending=False).iloc[0]
        return (
            f"For this filtered day, <b>{worst['origin']}</b> shows the highest cancellation rate "
            f"at <b>{worst['cancellation_rate']:.1f}%</b>."
        )

    grouped = (
        cancel_df.groupby("origin", as_index=False)["cancellation_rate"]
        .mean()
        .sort_values("cancellation_rate", ascending=False)
    )
    worst = grouped.iloc[0]
    return (
        f"Across the selected months, <b>{worst['origin']}</b> has the highest average cancellation level "
        f"at about <b>{worst['cancellation_rate']:.1f}%</b>."
    )


def get_weather_conclusion_text(weather_df: pd.DataFrame) -> str:
    if weather_df.empty:
        return "No weather-impact data is available for the selected filters."

    avg_by_wind = (
        weather_df.groupby("wind_category", as_index=False)["avg_dep_delay"]
        .mean()
        .sort_values("avg_dep_delay", ascending=False)
    )
    top = avg_by_wind.iloc[0]
    return (
        f"Stronger wind conditions tend to be linked with higher delays in this filtered view. "
        f"On average, <b>{top['wind_category'].lower()}</b> conditions show the highest departure delay "
        f"at about <b>{top['avg_dep_delay']:.1f} minutes</b>."
    )


def get_routes_conclusion_text(routes_df: pd.DataFrame) -> str:
    if routes_df.empty:
        return "No route data is available for the selected filters."

    top_row = routes_df.sort_values("flights", ascending=False).iloc[0]
    return (
        f"The busiest route in this filtered view is <b>{top_row['route']}</b>, "
        f"with <b>{int(top_row['flights']):,} flights</b>."
    )