"""
Converts HHMM time fields to datetimes and validates consistency across
dep_time, arr_time, air_time, delays, and distance.
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = str(PROJECT_ROOT / 'data' / 'flights_database.db')


def convert_time_to_datetime(year, month, day, time_value):
    """HHMM int (e.g. 517 → 05:17, 2400+ → next day) to datetime. Returns None for nulls."""
    if pd.isna(time_value):
        return None
    
    time_int = int(time_value)
    hours = time_int // 100
    minutes = time_int % 100
    
    # times >= 2400 roll over to the next day
    if hours >= 24:
        day_offset = hours // 24
        hours = hours % 24
        base_date = datetime(year, month, day)
        return base_date + timedelta(days=day_offset, hours=hours, minutes=minutes)
    
    return datetime(year, month, day, hours, minutes)


def add_datetime_columns():
    """Add datetime columns for easier time calculations."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("adding datetime columns\n")

    datetime_columns = [
        'sched_dep_datetime',
        'dep_datetime', 
        'sched_arr_datetime',
        'arr_datetime'
    ]
    
    for col in datetime_columns:
        try:
            cursor.execute(f"ALTER TABLE flights ADD COLUMN {col} TEXT")
            print(f"added: {col}")
        except sqlite3.OperationalError:
            print(f"already exists: {col}")
    
    conn.commit()

    print("\nconverting times...")
    
    df = pd.read_sql_query("""
        SELECT rowid, year, month, day, 
               sched_dep_time, dep_time, sched_arr_time, arr_time
        FROM flights
        WHERE cancelled = 0
        LIMIT 100000
    """, conn)
    
    print(f"{len(df)} flights loaded — starting conversion")

    df['sched_dep_datetime'] = df.apply(
        lambda row: convert_time_to_datetime(row['year'], row['month'], row['day'], row['sched_dep_time']),
        axis=1
    )
    
    df['dep_datetime'] = df.apply(
        lambda row: convert_time_to_datetime(row['year'], row['month'], row['day'], row['dep_time']),
        axis=1
    )
    
    df['sched_arr_datetime'] = df.apply(
        lambda row: convert_time_to_datetime(row['year'], row['month'], row['day'], row['sched_arr_time']),
        axis=1
    )
    
    df['arr_datetime'] = df.apply(
        lambda row: convert_time_to_datetime(row['year'], row['month'], row['day'], row['arr_time']),
        axis=1
    )
    
    print("writing to db...")
    for idx, row in df.iterrows():
        cursor.execute("""
            UPDATE flights
            SET sched_dep_datetime = ?,
                dep_datetime = ?,
                sched_arr_datetime = ?,
                arr_datetime = ?
            WHERE rowid = ?
        """, (
            row['sched_dep_datetime'].isoformat() if row['sched_dep_datetime'] else None,
            row['dep_datetime'].isoformat() if row['dep_datetime'] else None,
            row['sched_arr_datetime'].isoformat() if row['sched_arr_datetime'] else None,
            row['arr_datetime'].isoformat() if row['arr_datetime'] else None,
            row['rowid']
        ))
        
        if (idx + 1) % 10000 == 0:
            print(f"  {idx + 1} rows...")
            conn.commit()
    
    conn.commit()
    print(f"done — {len(df)} rows converted")

    sample = pd.read_sql_query("""
        SELECT year, month, day, carrier, flight,
               dep_time, dep_datetime,
               arr_time, arr_datetime
        FROM flights
        WHERE dep_datetime IS NOT NULL
        LIMIT 10
    """, conn)
    
    print("\nsample:")
    print(sample.to_string(index=False))
    
    conn.close()
    return df


def check_data_consistency():
    """
    Whether the data in flights is in order
    checking: air_time, delays, temporal order, and implied speed."""
    conn = sqlite3.connect(DB_PATH)
    
    print("consistency checks\n")

    df = pd.read_sql_query("""
        SELECT 
            year, month, day, carrier, flight, origin, dest,
            dep_time, sched_dep_time, dep_delay,
            arr_time, sched_arr_time, arr_delay,
            air_time, distance
        FROM flights
        WHERE cancelled = 0
        AND dep_time IS NOT NULL
        AND arr_time IS NOT NULL
        AND air_time IS NOT NULL
        LIMIT 50000
    """, conn)
    
    print(f"{len(df)} flights to check\n")

    # need datetimes for the arithmetic below
    print("converting...")
    df['dep_datetime'] = df.apply(
        lambda row: convert_time_to_datetime(int(row['year']), int(row['month']), int(row['day']), row['dep_time']),
        axis=1
    )
    df['arr_datetime'] = df.apply(
        lambda row: convert_time_to_datetime(int(row['year']), int(row['month']), int(row['day']), row['arr_time']),
        axis=1
    )
    
    # air_time vs calculated — big gaps are usually tz-related
    df['calculated_air_time'] = (df['arr_datetime'] - df['dep_datetime']).dt.total_seconds() / 60
    df['air_time_diff'] = abs(df['calculated_air_time'] - df['air_time'])

    inconsistent_airtime = df[df['air_time_diff'] > 10]

    print(f"air_time off by >10 min: {len(inconsistent_airtime)} ({len(inconsistent_airtime)/len(df)*100:.1f}%)")
    if len(inconsistent_airtime) > 0:
        print(f"  avg diff {df['air_time_diff'].mean():.0f} min, max {df['air_time_diff'].max():.0f} min")
        print(inconsistent_airtime[['carrier', 'flight', 'origin', 'dest', 'air_time', 'calculated_air_time', 'air_time_diff']].head(10).to_string(index=False))
    
    df['calculated_dep_delay'] = (df['dep_time'] - df['sched_dep_time']) / 100 * 60
    df['dep_delay_diff'] = abs(df['calculated_dep_delay'] - df['dep_delay'])
    inconsistent_dep_delay = df[df['dep_delay_diff'] > 5]
    print(f"\ndep_delay mismatch >5 min: {len(inconsistent_dep_delay)} ({len(inconsistent_dep_delay)/len(df)*100:.1f}%)")

    df['calculated_arr_delay'] = (df['arr_time'] - df['sched_arr_time']) / 100 * 60
    df['arr_delay_diff'] = abs(df['calculated_arr_delay'] - df['arr_delay'])
    inconsistent_arr_delay = df[df['arr_delay_diff'] > 5]
    print(f"arr_delay mismatch >5 min: {len(inconsistent_arr_delay)} ({len(inconsistent_arr_delay)/len(df)*100:.1f}%)")
    
    df['flight_duration'] = (df['arr_datetime'] - df['dep_datetime']).dt.total_seconds() / 60
    impossible_flights = df[df['flight_duration'] <= 0]
    print(f"\narrival before departure: {len(impossible_flights)}")
    if len(impossible_flights) > 0:
        print(impossible_flights[['carrier', 'flight', 'origin', 'dest', 'dep_datetime', 'arr_datetime', 'flight_duration']].head(5).to_string(index=False))
    
    df['avg_speed_mph'] = (df['distance'] / df['air_time']) * 60
    unusual_speed = df[(df['avg_speed_mph'] < 200) | (df['avg_speed_mph'] > 600)]
    print(f"\nspeed outliers (<200 or >600 mph): {len(unusual_speed)}")
    if len(unusual_speed) > 0:
        print(unusual_speed[['carrier', 'flight', 'origin', 'dest', 'distance', 'air_time', 'avg_speed_mph']].head(10).to_string(index=False))
    
    conn.close()
    
    return {
        'inconsistent_airtime': inconsistent_airtime,
        'inconsistent_dep_delay': inconsistent_dep_delay,
        'inconsistent_arr_delay': inconsistent_arr_delay,
        'impossible_flights': impossible_flights,
        'unusual_speed': unusual_speed
    }


def resolve_inconsistencies():
    """Print notes on what's causing each inconsistency and how to handle it."""
    solutions = """
inconsistency notes:

  air_time gaps       most are timezone-related; recalc from arr-dep datetimes
  delay mismatches    midnight crossover; recalc from sched vs actual datetimes
  arrival before dep  overnight flights hitting tz boundaries; add 24h to arr_time
  unusual speeds      bad air_time or distance; cross-check against aircraft type

general approach:
  - add calculated_* columns, keep originals for audit
  - use a data_quality_flag for suspicious rows
  - create views with corrected values rather than overwriting
"""

    print(solutions)


def main():
    # add_datetime_columns() is slow on 400k rows — uncomment to run
    # add_datetime_columns()

    inconsistencies = check_data_consistency()
    resolve_inconsistencies()


if __name__ == "__main__":
    main()
