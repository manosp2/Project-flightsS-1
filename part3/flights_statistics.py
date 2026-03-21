from .db import query_df

NYC_AIRPORTS = {"JFK", "LGA", "EWR"}


def flight_stats_for_day(origin: str, month: int, day: int) -> dict:
    """
    Bullet 4:
    stats for flights from a NYC airport on a given month/day.
    """
    origin = origin.upper().strip()
    if origin not in NYC_AIRPORTS:
        raise ValueError("origin must be one of: JFK, LGA, EWR")

    df = query_df(
        """
        WITH day_flights AS (
            SELECT dest
            FROM flights
            WHERE origin = ? AND month = ? AND day = ?
        ),
        top_dest AS (
            SELECT dest, COUNT(*) AS n
            FROM day_flights
            GROUP BY dest
            ORDER BY n DESC
            LIMIT 1
        )
        SELECT
            (SELECT COUNT(*) FROM day_flights) AS total_flights,
            (SELECT COUNT(DISTINCT dest) FROM day_flights) AS unique_destinations,
            (SELECT dest FROM top_dest) AS most_visited_dest,
            (SELECT n FROM top_dest) AS most_visited_count;
        """,
        params=(origin, int(month), int(day)),
    )

    total_flights = int(df.loc[0, "total_flights"] or 0)
    unique_destinations = int(df.loc[0, "unique_destinations"] or 0)
    most_dest = df.loc[0, "most_visited_dest"]
    most_count = int(df.loc[0, "most_visited_count"] or 0)

    return {
        "origin": origin,
        "month": int(month),
        "day": int(day),
        "total_flights": total_flights,
        "unique_destinations": unique_destinations,
        "most_visited_dest": most_dest,
        "most_visited_count": most_count,
    }