from __future__ import annotations

import pandas as pd
import plotly.express as px

from .db import query_df
from .geo import haversine_miles

NYC_AIRPORTS = ["JFK", "LGA", "EWR"]
UNKNOWN_PLANE_TYPE = "Unknown"


# ---------- airports ----------
def airports_by_codes(codes: list[str]) -> pd.DataFrame:
    """Fetch airports (faa, name, lat, lon) for a list of FAA codes."""
    codes = [c.upper().strip() for c in codes if c]
    codes = list(dict.fromkeys(codes))  # unique, keep order
    if not codes:
        return pd.DataFrame(columns=["faa", "name", "lat", "lon"])

    placeholders = ",".join(["?"] * len(codes))
    return query_df(
        f"SELECT faa, name, lat, lon FROM airports WHERE faa IN ({placeholders});",
        params=tuple(codes),
    )

# ---------- bullet 2 ----------
def get_departure_origins() -> pd.DataFrame:
    """Unique origins in flights, merged with airport names (single SQL join)."""
    return query_df(
        """
        SELECT DISTINCT f.origin AS faa, a.name
        FROM flights f
        LEFT JOIN airports a ON a.faa = f.origin
        ORDER BY f.origin;
        """
    )


def nyc_departure_airports() -> pd.DataFrame:
    """The NYC airports that appear as origins."""
    df = get_departure_origins()
    return df[df["faa"].isin(NYC_AIRPORTS)].reset_index(drop=True)


# ---------- bullet 1: distance verification ----------
def verify_distances(n: int = 1000) -> pd.DataFrame:
    """Compare DB 'distance' to haversine distance computed from coords."""
    df = query_df(
        """
        SELECT f.distance,
               a1.lat AS lat1, a1.lon AS lon1,
               a2.lat AS lat2, a2.lon AS lon2
        FROM flights f
        JOIN airports a1 ON f.origin = a1.faa
        JOIN airports a2 ON f.dest   = a2.faa
        WHERE f.distance IS NOT NULL
          AND a1.lat IS NOT NULL AND a1.lon IS NOT NULL
          AND a2.lat IS NOT NULL AND a2.lon IS NOT NULL
        LIMIT ?;
        """,
        params=(int(n),),
    )

    df["computed"] = haversine_miles(df["lat1"], df["lon1"], df["lat2"], df["lon2"])
    df["abs_diff"] = (df["distance"] - df["computed"]).abs()
    df["rel_error"] = df["abs_diff"] / df["distance"]

    print(f"Mean abs diff (miles): {df['abs_diff'].mean():.2f}")
    print(f"Mean relative error: {df['rel_error'].mean():.2%}")
    return df


def sample_flight_distances(n: int = 5) -> pd.DataFrame:
    """Small sample of flights with coords + distance."""
    return query_df(
        """
        SELECT f.distance,
               f.origin,
               f.dest,
               a1.lat AS origin_lat, a1.lon AS origin_lon,
               a2.lat AS dest_lat,   a2.lon AS dest_lon
        FROM flights f
        JOIN airports a1 ON f.origin = a1.faa
        JOIN airports a2 ON f.dest   = a2.faa
        LIMIT ?;
        """,
        params=(int(n),),
    )


# ---------- flights ----------
def nyc_flights() -> pd.DataFrame:
    """Entire flights table (your DB already contains only NYC-origin flights)."""
    return query_df("SELECT * FROM flights;")


def flights_from_origin_on_day(origin: str, month: int, day: int) -> pd.DataFrame:
    """All flights for given origin + month/day."""
    origin = origin.upper().strip()
    if origin not in NYC_AIRPORTS:
        raise ValueError(f"origin must be one of {NYC_AIRPORTS}")

    return query_df(
        """
        SELECT *
        FROM flights
        WHERE origin = ? AND month = ? AND day = ?;
        """,
        params=(origin, int(month), int(day)),
    )


# ---------- destinations ----------
def top_nyc_destinations(n: int = 10) -> pd.DataFrame:
    """Top N destinations for NYC origins (JFK/LGA/EWR)."""
    return query_df(
        """
        SELECT dest, COUNT(*) AS flight_count
        FROM flights
        WHERE origin IN ('JFK', 'LGA', 'EWR')
        GROUP BY dest
        ORDER BY flight_count DESC
        LIMIT ?;
        """,
        params=(int(n),),
    )


def plot_top_destinations(n: int = 10):
    df = top_nyc_destinations(n=n)
    fig = px.bar(df, x="dest", y="flight_count", title=f"Top {n} destinations from NYC")
    fig.update_xaxes(tickangle=45)
    return fig


def plot_destinations_for_day(origin: str, month: int, day: int, limit: int | None = None):
    """
    Bullet 3:
    World map + lines from origin to every destination on that day.
    Similar idea as Part 1 (routes), but data comes from SQL.
    """
    origin = origin.upper().strip()

    flights = flights_from_origin_on_day(origin, month, day)
    dest_codes = sorted(flights["dest"].dropna().unique().tolist())
    if limit is not None:
        dest_codes = dest_codes[: int(limit)]

    airports = airports_by_codes([origin] + dest_codes).copy()
    airports["lat"] = pd.to_numeric(airports["lat"], errors="coerce")
    airports["lon"] = pd.to_numeric(airports["lon"], errors="coerce")
    airports = airports.dropna(subset=["lat", "lon"])

    origin_row = airports[airports["faa"] == origin]
    if origin_row.empty:
        raise ValueError(f"No airport coords found for origin {origin}")

    o_lat = float(origin_row.iloc[0]["lat"])
    o_lon = float(origin_row.iloc[0]["lon"])

    # Base: plot all points (origin + dests)
    fig = px.scatter_geo(
        airports,
        lat="lat",
        lon="lon",
        hover_name="name",
        hover_data={"faa": True},
        title=f"Destinations from {origin} on {month}/{day}",
    )

    # Lines: origin -> each destination 
    for code in dest_codes:
        dest = airports[airports["faa"] == code]
        if dest.empty:
            continue
        d_lat = float(dest.iloc[0]["lat"])
        d_lon = float(dest.iloc[0]["lon"])
        fig.add_scattergeo(
            lat=[o_lat, d_lat],
            lon=[o_lon, d_lon],
            mode="lines",
            showlegend=False,
        )

    return fig


# ---------- bullet 5 ----------
def plane_types_for_route(origin: str, dest: str) -> dict[str, int]:
    """Count how many times each plane type was used on a route origin -> dest."""
    origin = origin.upper().strip()
    dest = dest.upper().strip()

    df = query_df(
        """
        SELECT COALESCE(NULLIF(TRIM(p.type), ''), ?) AS plane_type,
               COUNT(*) AS n
        FROM flights f
        LEFT JOIN planes p ON p.tailnum = f.tailnum
        WHERE f.origin = ? AND f.dest = ?
        GROUP BY plane_type
        ORDER BY n DESC;
        """,
        params=(UNKNOWN_PLANE_TYPE, origin, dest),
    )
    return dict(zip(df["plane_type"], df["n"].astype(int)))