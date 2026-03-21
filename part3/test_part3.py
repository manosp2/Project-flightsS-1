from .db import connect, sql_df, query_df

from .flights_analysis import (
    verify_distances,
    nyc_departure_airports,
    sample_flight_distances,
    nyc_flights,
    plot_top_destinations,
    plot_destinations_for_day,
    plane_types_for_route,
)

from .flights_statistics import flight_stats_for_day

from .delay_analysis import (
    avg_dep_delay_per_airline,
    plot_avg_dep_delay_per_airline,
    count_delayed_flights_to_destination,
    distance_vs_arrival_delay,
    plot_distance_vs_arrival_delay,
    plot_distance_delay_binned,
)

from .manufacturer_analysis import (
    top_manufacturers_for_destination,
    plot_top_manufacturers_for_destination,
)

from .wind_speed_analysis import (
    model_avg_speeds,
    fill_planes_speed_from_model_avg,
    bearing_deg,
    wind_dot_flight,
    summarize_airtime_by_wind_sign,
)


def main():
    print("=== TEST PART 3 ===")

    # A) DB works: list tables
    conn = connect()
    tables = sql_df(conn, "SELECT name FROM sqlite_master WHERE type='table';")
    print("\n[A] Tables in database:")
    print(tables.to_string(index=False))
    conn.close()

    # B) Bullet 1: distance verification
    print("\n[B] Verify distances (first 5 rows):")
    df_dist = verify_distances(n=1000)
    print(df_dist.head().to_string(index=False))

    # C) NYC departure airports
    print("\n[C] NYC departure airports:")
    dep = nyc_departure_airports()
    print(dep.to_string(index=False))

    # D) Sample flights with coords
    print("\n[D] Sample flights with coordinates:")
    samp = sample_flight_distances(n=5)
    print(samp.to_string(index=False))

    # E) All flights
    print("\n[E] Flights sample:")
    allf = nyc_flights()
    print(allf.head(5).to_string(index=False))
    print(f"Total flights: {len(allf)}")

    # F) Plot: top destinations from NYC
    print("\n[F] Plot: Top destinations from NYC")
    plot_top_destinations(n=10).show()

    # G) Bullet 4: stats for that day
    print("\n[G] Bullet 4: Flight stats for JFK on 1/1")
    stats = flight_stats_for_day("JFK", 1, 1)
    for k, v in stats.items():
        print(f"{k}: {v}")

    # H) Bullet 3: map for that day
    print("\n[H] Bullet 3: Destinations map for JFK on 1/1")
    plot_destinations_for_day("JFK", 1, 1, limit=50).show()

    # I) Bullet 5: plane types for route
    print("\n[I] Bullet 5: Plane types for JFK -> LAX")
    d = plane_types_for_route("JFK", "LAX")
    print(d)
    print("Unique plane types:", len(d))
    print("Total flights counted:", sum(d.values()))

    total = int(
        query_df(
            "SELECT COUNT(*) AS n FROM flights WHERE origin=? AND dest=?;",
            params=("JFK", "LAX"),
        ).loc[0, "n"]
    )
    print("Total flights JFK->LAX (all):", total)

    

    # K) Delayed flights to destination in month range
    print("\n[K] Delayed flights to LAX from Jan–Mar (dep_delay > 0)")
    n_delayed = count_delayed_flights_to_destination("LAX", 1, 3)
    print("Delayed flights:", n_delayed)

    # L) Top manufacturers for destination + plot
    print("\n[L] Top 5 manufacturers for flights to LAX")
    mf = top_manufacturers_for_destination("LAX", n=5)
    print(mf.to_string(index=False))
    plot_top_manufacturers_for_destination("LAX", n=5).show()

    # M) Debug manufacturers (planes table)
    print("\n[M] Raw manufacturers in planes table")
    df_m1 = query_df(
        """
        SELECT COALESCE(NULLIF(TRIM(manufacturer), ''), 'Unknown') AS manufacturer,
               COUNT(*) AS n_planes
        FROM planes
        GROUP BY COALESCE(NULLIF(TRIM(manufacturer), ''), 'Unknown')
        ORDER BY n_planes DESC
        LIMIT 20;
        """
    )
    print(df_m1.to_string(index=False))

    # N) Manufacturers used for flights to LAX (JOIN)
    print("\n[N] Manufacturers for flights to LAX (joined)")
    df_m2 = query_df(
        """
        SELECT COALESCE(NULLIF(TRIM(p.manufacturer), ''), 'Unknown') AS manufacturer,
               COUNT(*) AS n_flights
        FROM flights f
        LEFT JOIN planes p ON p.tailnum = f.tailnum
        WHERE f.dest = ?
        GROUP BY manufacturer
        ORDER BY n_flights DESC
        LIMIT 20;
        """,
        params=("LAX",),
    )
    print(df_m2.to_string(index=False))

    print("\n[N2] Why 'Unknown' (missing planes match) for flights to LAX?")
    df_unknown = query_df(
        """
        SELECT
          COUNT(*) AS total_flights_to_dest,
          SUM(CASE WHEN f.tailnum IS NULL OR TRIM(f.tailnum) = '' THEN 1 ELSE 0 END) AS tailnum_missing_in_flights,
          SUM(CASE WHEN p.tailnum IS NULL THEN 1 ELSE 0 END) AS no_match_in_planes
        FROM flights f
        LEFT JOIN planes p ON p.tailnum = f.tailnum
        WHERE f.dest = ?;
        """,
        params=("LAX",),
    )
    print(df_unknown.to_string(index=False))

    # O) Distance vs arrival delay
    print("\n[O] Distance vs arrival delay")
    plot_distance_vs_arrival_delay(n=20000).show()

    print("\n[J] Avg departure delay per airline (df + plot)")
    df_air = avg_dep_delay_per_airline()
    print(df_air.head(10).to_string(index=False))
    print("Rows (airlines):", len(df_air))
    plot_avg_dep_delay_per_airline().show()

    print("\n[K] Delayed flights to destination in month range")
    for dest in ["LAX", "ATL", "MIA"]:
        n_del = count_delayed_flights_to_destination(dest, 1, 3)
        print(f"Delayed flights to {dest} (Jan–Mar): {n_del}")

    print("\n[M] Distance vs arrival delay (df + scatter)")
    df_dist = distance_vs_arrival_delay(n=20000)
    print(df_dist.head(5).to_string(index=False))
    print("Rows:", len(df_dist))
    plot_distance_vs_arrival_delay(n=20000).show()

    print("\n[M2] Binned mean arrival delay vs distance (line)")
    plot_distance_delay_binned(bin_width=250).show()

    print("\n[Z1] Model avg speeds (head)")
    df_speed = model_avg_speeds()
    print(df_speed.head(10).to_string(index=False))
    print("Rows:", len(df_speed))

    print("\n[Z2] Fill planes.speed from model averages")
    fill_planes_speed_from_model_avg()
    print("Updated planes.speed (sample):")
    print(query_df("SELECT tailnum, model, speed FROM planes WHERE speed IS NOT NULL LIMIT 10;").to_string(index=False))

    print("\n[Z2.1] Bullet 11: Test bearing_deg() function")
    # trying JFK to LAX first
    jfk_lat, jfk_lon = 40.6413, -73.7781
    lax_lat, lax_lon = 33.9416, -118.4085
    bearing_jfk_lax = bearing_deg(jfk_lat, jfk_lon, lax_lat, lax_lon)
    print(f"Bearing from JFK to LAX: {bearing_jfk_lax:.2f}° (should be around 250°, going southwest)")
    
    # now checking basic directions
    bearing_north = bearing_deg(40.0, -74.0, 41.0, -74.0)
    print(f"Bearing due north: {bearing_north:.2f}° (expected ~0°)")
    
    bearing_east = bearing_deg(40.0, -74.0, 40.0, -73.0)
    print(f"Bearing due east: {bearing_east:.2f}° (should be 90°)")

    print("\n[Z2.2] Bullet 12: Test wind_dot_flight() function")
    # flying east with wind pushing from behind (tailwind)
    dot_tailwind = wind_dot_flight(flight_bearing=90.0, wind_dir_from=270.0, wind_speed=10.0)
    print(f"Tailwind (flying east, wind from west): dot={dot_tailwind:.2f} (should be ~10, positive)")
    
    # flying east but wind coming at you (headwind)
    dot_headwind = wind_dot_flight(flight_bearing=90.0, wind_dir_from=90.0, wind_speed=10.0)
    print(f"Headwind (flying east, wind from east): dot={dot_headwind:.2f} (should be ~-10, negative)")
    
    # flying north with wind from the side
    dot_crosswind = wind_dot_flight(flight_bearing=0.0, wind_dir_from=90.0, wind_speed=10.0)
    print(f"Crosswind (flying north, wind from east): dot={dot_crosswind:.2f} (should be ~0)")

    print("\n[Z3] Wind dot sign vs air_time")
    print(summarize_airtime_by_wind_sign(n=50000).to_string(index=False))

    print("\n=== DONE ===")


if __name__ == "__main__":
    main()