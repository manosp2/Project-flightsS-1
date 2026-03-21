# weather vs. delays/cancellations — broken down by plane type, manufacturer, engine type

import sqlite3
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = str(PROJECT_ROOT / 'data' / 'flights_database.db')

# cut points shared across functions so they stay consistent
_WIND_BINS   = [0, 10, 20, 30, 100]
_WIND_LABELS = ['Calm (0-10)', 'Moderate (10-20)', 'Strong (20-30)', 'Severe (30+)']

_PRECIP_BINS   = [-0.01, 0, 0.1, 0.5, 10]
_PRECIP_LABELS = ['None', 'Light', 'Moderate', 'Heavy']

_VIS_BINS   = [0, 1, 5, 10, 20]
_VIS_LABELS = ['Poor (<1mi)', 'Low (1-5mi)', 'Moderate (5-10mi)', 'Good (10+mi)']


def _query(sql: str) -> pd.DataFrame:
    """Fire a query at the local DB, return a DataFrame."""
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(sql, conn)


def analyze_wind_effects_by_plane_type():
    print("--- wind vs. delays by plane type ---")

    df = _query("""
        SELECT p.type as plane_type, p.manufacturer, p.engines,
               w.wind_speed, w.wind_gust, w.wind_dir,
               f.dep_delay, f.arr_delay, f.air_time, f.distance, f.cancelled
        FROM flights f
        JOIN planes p ON f.tailnum = p.tailnum
        LEFT JOIN weather w ON f.origin = w.origin
            AND f.year = w.year AND f.month = w.month
            AND f.day = w.day AND f.hour = w.hour
        WHERE w.wind_speed IS NOT NULL AND p.type IS NOT NULL
        LIMIT 100000
    """)

    print(f"{len(df)} rows matched\n")

    df['wind_category'] = pd.cut(df['wind_speed'], bins=_WIND_BINS, labels=_WIND_LABELS)

    print("dep/arr delay by plane type x wind bucket:")
    delay_by_wind = df.groupby(['plane_type', 'wind_category'], observed=True).agg(
        avg_dep_delay=('dep_delay', 'mean'),
        avg_arr_delay=('arr_delay', 'mean'),
        num_flights=('cancelled', 'count'),
    ).round(2)
    print(delay_by_wind)

    print("\ncancellations by wind bucket:")
    cancel_by_wind = df.groupby('wind_category', observed=True).agg(
        cancellation_rate=('cancelled', 'mean'),
        num_flights=('cancelled', 'count'),
    ).round(4)
    print(cancel_by_wind)

    return df


def analyze_precipitation_effects():
    print("--- precipitation vs. delays ---")

    df = _query("""
        SELECT p.type as plane_type, p.manufacturer, p.engine,
               w.precip, w.visib as visibility,
               f.dep_delay, f.arr_delay, f.cancelled, f.carrier
        FROM flights f
        JOIN planes p ON f.tailnum = p.tailnum
        LEFT JOIN weather w ON f.origin = w.origin
            AND f.year = w.year AND f.month = w.month
            AND f.day = w.day AND f.hour = w.hour
        WHERE w.precip IS NOT NULL AND p.type IS NOT NULL
        LIMIT 100000
    """)

    print(f"{len(df)} rows matched\n")

    df['precip_category'] = pd.cut(df['precip'], bins=_PRECIP_BINS, labels=_PRECIP_LABELS)

    print("delay + cancellations by precip bucket:")
    delay_by_precip = df.groupby('precip_category', observed=True).agg(
        avg_dep_delay=('dep_delay', 'mean'),
        avg_arr_delay=('arr_delay', 'mean'),
        cancel_rate=('cancelled', 'mean'),
        num_flights=('cancelled', 'count'),
    ).round(2)
    print(delay_by_precip)

    print("\nrainy flights only — delay by plane type:")
    type_precip = df[df['precip'] > 0].groupby('plane_type').agg(
        avg_dep_delay=('dep_delay', 'mean'),
        num_flights=('dep_delay', 'count'),
        avg_arr_delay=('arr_delay', 'mean'),
    ).round(2)
    print(type_precip)

    return df


def analyze_manufacturer_weather_performance():
    print("--- manufacturer performance in weather ---")

    df = _query("""
        SELECT p.manufacturer,
               COUNT(DISTINCT p.model) as num_models,
               COUNT(*) as total_flights,
               AVG(w.wind_speed) as avg_wind_speed,
               AVG(w.precip) as avg_precip,
               AVG(f.dep_delay) as avg_dep_delay,
               AVG(f.arr_delay) as avg_arr_delay,
               AVG(CASE WHEN f.cancelled = 1 THEN 1.0 ELSE 0.0 END) as cancel_rate
        FROM flights f
        JOIN planes p ON f.tailnum = p.tailnum
        LEFT JOIN weather w ON f.origin = w.origin
            AND f.year = w.year AND f.month = w.month
            AND f.day = w.day AND f.hour = w.hour
        WHERE p.manufacturer IS NOT NULL
        GROUP BY p.manufacturer
        HAVING total_flights > 1000
        ORDER BY total_flights DESC
        LIMIT 20
    """)

    print("top 20 manufacturers (>1k flights):")
    print(df.round(3).to_string(index=False))

    return df


def analyze_engine_type_weather():
    print("--- engine type: delay sensitivity to wind/precip ---")

    df = _query("""
        SELECT p.engine as engine_type,
               COUNT(*) as total_flights,
               AVG(w.wind_speed) as avg_wind_speed,
               AVG(CASE WHEN w.wind_speed > 20  THEN f.dep_delay END) as delay_high_wind,
               AVG(CASE WHEN w.wind_speed <= 20 THEN f.dep_delay END) as delay_normal_wind,
               AVG(CASE WHEN w.precip > 0.1  THEN f.dep_delay END) as delay_with_precip,
               AVG(CASE WHEN w.precip <= 0.1 THEN f.dep_delay END) as delay_no_precip,
               AVG(f.cancelled) as cancel_rate
        FROM flights f
        JOIN planes p ON f.tailnum = p.tailnum
        LEFT JOIN weather w ON f.origin = w.origin
            AND f.year = w.year AND f.month = w.month
            AND f.day = w.day AND f.hour = w.hour
        WHERE p.engine IS NOT NULL AND w.wind_speed IS NOT NULL
        GROUP BY p.engine
        HAVING total_flights > 500
        ORDER BY total_flights DESC
    """)

    print("raw numbers:")
    print(df.round(2).to_string(index=False))

    if not df.empty:
        df['wind_sensitivity']  = df['delay_high_wind']   - df['delay_normal_wind']
        df['precip_sensitivity'] = df['delay_with_precip'] - df['delay_no_precip']

        # positive = worse in bad weather vs baseline
        print("\nextra delay in bad weather vs baseline:")
        print(df[['engine_type', 'wind_sensitivity', 'precip_sensitivity', 'total_flights']].round(2).to_string(index=False))

    return df


def analyze_visibility_effects():
    print("--- visibility vs. delays by plane type ---")

    df = _query("""
        SELECT p.type as plane_type, w.visib as visibility,
               AVG(f.dep_delay) as avg_dep_delay,
               AVG(f.arr_delay) as avg_arr_delay,
               AVG(f.cancelled) as cancel_rate,
               COUNT(*) as num_flights
        FROM flights f
        JOIN planes p ON f.tailnum = p.tailnum
        LEFT JOIN weather w ON f.origin = w.origin
            AND f.year = w.year AND f.month = w.month
            AND f.day = w.day AND f.hour = w.hour
        WHERE w.visib IS NOT NULL AND p.type IS NOT NULL
        GROUP BY p.type, w.visib
        HAVING num_flights > 100
        ORDER BY w.visib, p.type
        LIMIT 50
    """)

    df['visibility_category'] = pd.cut(df['visibility'], bins=_VIS_BINS, labels=_VIS_LABELS)

    print("delay + cancel rate by vis bucket x plane type:")
    vis_summary = df.groupby(['plane_type', 'visibility_category'], observed=True).agg(
        avg_dep_delay=('avg_dep_delay', 'mean'),
        cancel_rate=('cancel_rate', 'mean'),
        num_flights=('num_flights', 'sum'),
    ).round(3)
    print(vis_summary)

    return df

def create_weather_insights_summary():
    summary = """
quick takeaways that we found:

  wind          regional jets take more of a hit; delays tick up past ~20 mph
  precip        cancellations jump when is rainning and all types are affected
  manufacturers Boeing/Airbus roughly even; Because of the aircraft size(mainly) smaller makers look worse
  engines       props more sensitive to wind than fans, which is expected because of the size
  visibility    sub-1-mile is rough across the board; differences by type are marginal

Also confounders to keep in mind:
  1) aircraft size muddies manufacturer comparisons
  2) some airports just handle bad weather better
  3) winter ice vs summer storms behave a lot differently
  4) departure-end weather matters more than destination
"""
    print(summary)
    return summary

def main():
    wind_df = analyze_wind_effects_by_plane_type()
    precip_df = analyze_precipitation_effects()
    manuf_df = analyze_manufacturer_weather_performance()
    engine_df = analyze_engine_type_weather()
    vis_df = analyze_visibility_effects()
    create_weather_insights_summary()


if __name__ == "__main__":
    main()