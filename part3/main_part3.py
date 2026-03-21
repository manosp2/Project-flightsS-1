# Part3_airports/main_part3.py

from .db import query_df
from .flights_analysis import (
    verify_distances,
    nyc_departure_airports,
    sample_flight_distances,
    plot_top_destinations,
    plot_destinations_for_day,
    plane_types_for_route,
)
from .flights_statistics import flight_stats_for_day
from .delay_analysis import (
    avg_dep_delay_per_airline,
    plot_avg_dep_delay_per_airline,
    count_delayed_flights_to_destination,
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
    summarize_airtime_by_wind_sign,
)


def main():
    print("=== PART 3: Flights Project ===")

    # 0) Quick DB sanity
    tables = query_df("SELECT name FROM sqlite_master WHERE type='table';")
    print("\n[0] Tables in database:")
    print(tables.to_string(index=False))

    # 1) Distance verification
    print("\n[1] Verify distances (sample):")
    df1 = verify_distances(n=1000)
    print(df1.head(5).to_string(index=False))

    # 2) NYC airports
    print("\n[2] NYC departure airports:")
    print(nyc_departure_airports().to_string(index=False))

    # 3) Destinations map for a day (example)
    print("\n[3] Destinations map for JFK on 1/1 (showing figure)...")
    plot_destinations_for_day("JFK", 1, 1, limit=50).show()

    # 4) Day statistics (example)
    print("\n[4] Flight stats for JFK on 1/1:")
    stats = flight_stats_for_day("JFK", 1, 1)
    for k, v in stats.items():
        print(f"{k}: {v}")

    # 5) Plane types for a route (example)
    print("\n[5] Plane types for JFK -> LAX:")
    d = plane_types_for_route("JFK", "LAX")
    print(d)
    print("Unique plane types:", len(d))
    print("Total flights counted:", sum(d.values()))

    # 6) Avg departure delay per airline
    print("\n[6] Avg departure delay per airline (df + plot):")
    df_delay = avg_dep_delay_per_airline()
    print(df_delay.to_string(index=False))
    plot_avg_dep_delay_per_airline().show()

    # 7) Delayed flights to destination in month range
    print("\n[7] Delayed flights to destination in month range (dep_delay > 0):")
    for dest in ["LAX", "ATL", "MIA"]:
        n_delayed = count_delayed_flights_to_destination(dest, 1, 3)
        print(f"Delayed flights to {dest} (Jan–Mar): {n_delayed}")

    # 8) Top manufacturers for destination
    print("\n[8] Top 5 manufacturers for flights to LAX (df + plot):")
    df_m = top_manufacturers_for_destination("LAX", n=5)
    print(df_m.to_string(index=False))
    plot_top_manufacturers_for_destination("LAX", n=5).show()

    # 9) Distance vs arrival delay
    print("\n[9] Distance vs arrival delay (scatter + binned mean)...")
    plot_distance_vs_arrival_delay(n=20000).show()
    plot_distance_delay_binned(bin_width=250).show()

    # 10) Speed column fill + wind relation
    print("\n[10] Model avg speeds (head):")
    df_speed = model_avg_speeds()
    print(df_speed.head(10).to_string(index=False))
    print(f"Rows (models): {len(df_speed)}")

    print("\n[11] Filling planes.speed from model averages...")
    fill_planes_speed_from_model_avg()
    sample_speed = query_df("SELECT tailnum, model, speed FROM planes WHERE speed IS NOT NULL LIMIT 10;")
    print("Updated planes.speed (sample):")
    print(sample_speed.to_string(index=False))

    print("\n[12] Wind dot sign vs air_time (summary):")
    df_wind = summarize_airtime_by_wind_sign(n=50000)
    print(df_wind.to_string(index=False))

    # Small extra: show a small sample flight coords
    print("\n[Extra] Sample flights with coordinates:")
    print(sample_flight_distances(n=5).to_string(index=False))

    print("\n=== DONE ===")


if __name__ == "__main__":
    main()