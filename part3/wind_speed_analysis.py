import pandas as pd
import numpy as np

from .db import connect, query_df


# ---------- planes.speed ----------
def ensure_speed_column_exists() -> None:
    """Add planes.speed column if missing (one-connection safe)."""
    with connect() as conn:
        cols = pd.read_sql_query("PRAGMA table_info(planes);", conn)["name"].tolist()
        if "speed" not in cols:
            conn.execute("ALTER TABLE planes ADD COLUMN speed REAL;")
            conn.commit()


def model_avg_speeds() -> pd.DataFrame:
    """Average speed per model (mph) using distance / (air_time/60)."""
    return query_df(
        """
        SELECT p.model,
               AVG(f.distance / (f.air_time / 60.0)) AS avg_speed_mph,
               COUNT(*) AS n_flights
        FROM flights f
        JOIN planes p ON p.tailnum = f.tailnum
        WHERE f.distance IS NOT NULL
          AND f.air_time IS NOT NULL
          AND f.air_time > 0
          AND p.model IS NOT NULL
        GROUP BY p.model
        ORDER BY n_flights DESC;
        """
    )


def fill_planes_speed_from_model_avg() -> None:
    """Fill planes.speed using model average speeds (updates table planes)."""
    ensure_speed_column_exists()

    with connect() as conn:
        conn.execute("DROP TABLE IF EXISTS model_speeds;")
        conn.execute(
            """
            CREATE TEMP TABLE model_speeds AS
            SELECT p.model AS model,
                   AVG(f.distance / (f.air_time / 60.0)) AS avg_speed_mph
            FROM flights f
            JOIN planes p ON p.tailnum = f.tailnum
            WHERE f.distance IS NOT NULL
              AND f.air_time IS NOT NULL
              AND f.air_time > 0
              AND p.model IS NOT NULL
            GROUP BY p.model;
            """
        )

        conn.execute(
            """
            UPDATE planes
            SET speed = (
                SELECT ms.avg_speed_mph
                FROM model_speeds ms
                WHERE ms.model = planes.model
            )
            WHERE model IS NOT NULL;
            """
        )
        conn.commit()


# ---------- bearings / wind dot ----------
def bearing_deg(lat1, lon1, lat2, lon2) -> float:
    """Initial bearing (deg) from point1 to point2, 0=N, 90=E."""
    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)

    dlon = lon2 - lon1
    x = np.sin(dlon) * np.cos(lat2)
    y = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(dlon)
    brng = np.degrees(np.arctan2(x, y))
    return (brng + 360) % 360


def unit_vec_from_deg(deg: float) -> np.ndarray:
    """
    Convert bearing degrees (0=N, 90=E) to a unit vector [E, N].
    """
    rad = np.radians(deg)
    return np.array([np.sin(rad), np.cos(rad)])  # [E, N]


def wind_dot_flight(flight_bearing: float, wind_dir_from: float, wind_speed: float) -> float:
    """
    Inner product between flight direction (unit) and wind vector.
    wind_dir_from is meteorological: direction wind comes FROM.
    Positive dot => tailwind component.
    """
    wind_to = (wind_dir_from + 180.0) % 360.0
    u_flight = unit_vec_from_deg(flight_bearing)
    v_wind = float(wind_speed) * unit_vec_from_deg(wind_to)
    return float(u_flight @ v_wind)


def destination_bearings_from_jfk() -> pd.DataFrame:
    """Bearing from JFK to every airport (for the assignment direction question)."""
    airports = query_df(
        """
        SELECT faa, name, lat, lon
        FROM airports
        WHERE lat IS NOT NULL AND lon IS NOT NULL;
        """
    )
    jfk = airports[airports["faa"] == "JFK"]
    if jfk.empty:
        raise ValueError("JFK not found in airports table")
    jfk = jfk.iloc[0]

    out = airports.copy()
    out["bearing_from_JFK"] = out.apply(
        lambda r: bearing_deg(jfk["lat"], jfk["lon"], r["lat"], r["lon"]),
        axis=1,
    )
    return out[["faa", "name", "bearing_from_JFK"]]


def wind_effect_dataset(n: int | None = 50000) -> pd.DataFrame:
    """
    Join flights + weather on (origin, time_hour),
    compute flight bearing + wind dot product.
    """
    base = """
    SELECT f.origin, f.dest, f.air_time, f.distance, f.time_hour,
           w.wind_dir, w.wind_speed
    FROM flights f
    JOIN weather w
      ON w.origin = f.origin
     AND w.time_hour = f.time_hour
    WHERE f.air_time IS NOT NULL AND f.air_time > 0
      AND f.distance IS NOT NULL
      AND w.wind_dir IS NOT NULL
      AND w.wind_speed IS NOT NULL
    """
    if n is not None:
        base += " LIMIT ?"
        df = query_df(base, params=(int(n),))
    else:
        df = query_df(base)

    airports = query_df(
        "SELECT faa, lat, lon FROM airports WHERE lat IS NOT NULL AND lon IS NOT NULL;"
    ).set_index("faa")

    # FIX: parentheses around boolean conditions
    df = df[df["origin"].isin(airports.index) & df["dest"].isin(airports.index)].copy()

    def flight_bearing(row):
        o = airports.loc[row["origin"]]
        d = airports.loc[row["dest"]]
        return bearing_deg(o["lat"], o["lon"], d["lat"], d["lon"])

    df["bearing"] = df.apply(flight_bearing, axis=1)
    df["dot"] = df.apply(
        lambda r: wind_dot_flight(r["bearing"], r["wind_dir"], r["wind_speed"]), axis=1
    )

    # classify sign
    df["wind_relation"] = np.where(
        df["dot"] > 0, "tailwind", np.where(df["dot"] < 0, "headwind", "neutral")
    )
    return df


def summarize_airtime_by_wind_sign(n: int | None = 50000) -> pd.DataFrame:
    """Mean airtime by headwind/tailwind/neutral groups."""
    df = wind_effect_dataset(n=n)
    return (
        df.groupby("wind_relation", as_index=False)
        .agg(
            n=("air_time", "size"),
            mean_air_time=("air_time", "mean"),
            mean_distance=("distance", "mean"),
            mean_dot=("dot", "mean"),
        )
        .sort_values("wind_relation")
    )