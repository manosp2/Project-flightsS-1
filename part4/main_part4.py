"""
Part 4 — single entry point.
Run this file to see every analysis and every plot from part 4.

  
Note: datetime_consistency.py and local_time_timezone.py arent included here 
— they are one off DB setup scripts. Run them separately if you need.
"""

import sys
from pathlib import Path
import matplotlib.pyplot as plt

# make sure imports resolve relative to this folder
sys.path.insert(0, str(Path(__file__).parent))

SEP = "\n" + "-" * 60 + "\n"


# ─── 1. Missing value breakdown ───────────────────────────────────────────────
print(SEP + "1. MISSING VALUE BREAKDOWN" + SEP)
import check_missing_values  # executes top-level code on import


# ─── 2. Duplicate flights ─────────────────────────────────────────────────────
print(SEP + "2. DUPLICATE FLIGHTS" + SEP)
from duplicates import main as duplicates_main
duplicates_main()


# ─── 3. Missing value solutions ───────────────────────────────────────────────
print(SEP + "3. MISSING VALUE SOLUTIONS" + SEP)
from missing_values_solutions import main as mv_solutions_main
mv_solutions_main()


# ─── 4. Weather & plane type analysis ─────────────────────────────────────────
print(SEP + "4. WEATHER & PLANE TYPE ANALYSIS" + SEP)
from weather_plane_analysis import main as weather_main
weather_main()


# ─── 5. General insights — tables ─────────────────────────────────────────────
print(SEP + "5. GENERAL INSIGHTS — TABLES" + SEP)
from insights import (
    most_delayed_airports,
    delay_by_carrier,
    delay_by_month,
    delay_by_hour,
    busiest_routes,
    longest_routes,
    fastest_plane_types,
    manufacturer_delay_summary,
    weather_delay_correlation,
    visibility_vs_delay,
    plot_delay_by_month   as ins_plot_delay_by_month,
    plot_delay_by_hour,
    plot_delay_by_carrier,
    plot_visibility_vs_delay,
)

print("Most delayed airports (origin):")
print(most_delayed_airports().to_string(index=False))

print("\nDelay by carrier:")
print(delay_by_carrier().to_string(index=False))

print("\nDelay by month:")
print(delay_by_month().to_string(index=False))

print("\nDelay by hour (first 24 rows):")
print(delay_by_hour().to_string(index=False))

print("\nBusiest routes (top 15):")
print(busiest_routes().to_string(index=False))

print("\nLongest routes (top 10):")
print(longest_routes().to_string(index=False))

print("\nFastest plane types:")
print(fastest_plane_types().to_string(index=False))

print("\nManufacturer delay summary:")
print(manufacturer_delay_summary().to_string(index=False))

print("\nWeather delay correlation (first 20 rows):")
print(weather_delay_correlation().head(20).to_string(index=False))

print("\nVisibility vs delay:")
print(visibility_vs_delay().to_string(index=False))


# ─── 6. General insights — plots ──────────────────────────────────────────────
print(SEP + "6. GENERAL INSIGHTS — PLOTS (4 figures)" + SEP)
ins_plot_delay_by_month()
plot_delay_by_hour()
plot_delay_by_carrier()
plot_visibility_vs_delay()
plt.show(block=False)
print("plots shown — close windows to continue to airport analysis\n")
input("Press Enter to continue...")
plt.close('all')


# ─── 7. Airport analysis — tables & plots (JFK / EWR / LGA) ───────────────────
print(SEP + "7. AIRPORT ANALYSIS — JFK / EWR / LGA" + SEP)
from airport_analysis import (
    get_delay_stats,
    get_cancellation_rate,
    get_top_routes,
    get_weather_impact,
    plot_delay_by_month as aa_plot_delay_by_month,
    plot_top_routes,
    plot_weather_impact,
)

for airport in ('JFK', 'EWR', 'LGA'):
    print(f"\n{'─'*40}")
    print(f"  {airport}")
    print(f"{'─'*40}")

    print(f"\nDelay stats by carrier ({airport}):")
    print(get_delay_stats(airport).to_string(index=False))

    print(f"\nCancellation rate by month ({airport}):")
    print(get_cancellation_rate(airport).to_string(index=False))

    print(f"\nTop 10 routes from {airport}:")
    print(get_top_routes(airport).to_string(index=False))

    print(f"\nWeather impact — wind vs delays ({airport}):")
    print(get_weather_impact(airport).to_string(index=False))

    aa_plot_delay_by_month(airport)
    plot_top_routes(airport)
    plot_weather_impact(airport)

plt.show(block=False)
print("\nairport plots shown — close windows when done\n")
input("Press Enter to finish...")
plt.close('all')

print("\nAll done.")
