"""
Checks for duplicate flights in the dataset.
A flight is identified by (carrier, flight number, date, origin, dest).
"""

import sqlite3
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = str(PROJECT_ROOT / 'data' / 'flights_database.db')


def find_duplicate_flights():
    """Find flights with more than one row for the same (date, carrier, flight, route)."""
    conn = sqlite3.connect(DB_PATH)
    
    print("duplicate flights\n")

    duplicate_query = """
        SELECT 
            year, month, day, carrier, flight, origin, dest,
            COUNT(*) as occurrence_count
        FROM flights
        GROUP BY year, month, day, carrier, flight, origin, dest
        HAVING COUNT(*) > 1
        ORDER BY occurrence_count DESC, year, month, day
    """
    
    duplicates = pd.read_sql_query(duplicate_query, conn)
    
    print(f"{len(duplicates)} duplicate flight groups found")

    if len(duplicates) > 0:
        print(f"\ntop 20:")
        print(duplicates.head(20).to_string(index=False))

        # drill into the first one
        print(f"\nfirst duplicate group:")
        if len(duplicates) > 0:
            first_dup = duplicates.iloc[0]
            detail_query = """
                SELECT year, month, day, carrier, flight, tailnum, origin, dest,
                       dep_time, sched_dep_time, arr_time, sched_arr_time,
                       dep_delay, arr_delay, air_time, distance
                FROM flights
                WHERE year = ? AND month = ? AND day = ? 
                AND carrier = ? AND flight = ? AND origin = ? AND dest = ?
                ORDER BY dep_time
            """
            
            details = pd.read_sql_query(
                detail_query, 
                conn,
                params=(first_dup['year'], first_dup['month'], first_dup['day'],
                       first_dup['carrier'], first_dup['flight'], 
                       first_dup['origin'], first_dup['dest'])
            )
            print(details.to_string(index=False))

        total_extra = (duplicates['occurrence_count'] - 1).sum()
        print(f"\nappearing 2x: {len(duplicates[duplicates['occurrence_count'] == 2])}")
        print(f"appearing 3+: {len(duplicates[duplicates['occurrence_count'] >= 3])}")
        print(f"max occurrences: {duplicates['occurrence_count'].max()}")
        print(f"extra rows: {total_extra}")

    else:
        print("no duplicates — each flight appears once")
    
    conn.close()
    return duplicates


def check_exact_duplicates():
    """Check for rows that are completely identical across all columns."""
    conn = sqlite3.connect(DB_PATH)
    
    print("\nexact duplicate rows\n")

    exact_dup_query = """
        SELECT 
            year, month, day, dep_time, sched_dep_time, dep_delay,
            arr_time, sched_arr_time, arr_delay, carrier, flight, tailnum,
            origin, dest, air_time, distance, hour, minute,
            COUNT(*) as duplicate_count
        FROM flights
        GROUP BY 
            year, month, day, dep_time, sched_dep_time, dep_delay,
            arr_time, sched_arr_time, arr_delay, carrier, flight, tailnum,
            origin, dest, air_time, distance, hour, minute
        HAVING COUNT(*) > 1
    """
    
    exact_dups = pd.read_sql_query(exact_dup_query, conn)
    
    if len(exact_dups) > 0:
        print(f"{len(exact_dups)} groups of identical rows")
        print(f"extra entries: {(exact_dups['duplicate_count'] - 1).sum()}")
        print("\nsample:")
        print(exact_dups.head(10).to_string(index=False))
    else:
        print("no exact duplicate rows")
    
    conn.close()
    return exact_dups


def analyze_duplicate_patterns():
    """Look at whether duplicates share the same plane / departure time."""
    conn = sqlite3.connect(DB_PATH)
    
    print("\nduplicate patterns\n")

    # do the duplicates use different planes or different dep times?
    pattern_query = """
        WITH DuplicateFlights AS (
            SELECT year, month, day, carrier, flight, origin, dest
            FROM flights
            GROUP BY year, month, day, carrier, flight, origin, dest
            HAVING COUNT(*) > 1
        )
        SELECT 
            df.carrier,
            df.flight,
            df.origin,
            df.dest,
            COUNT(DISTINCT f.tailnum) as unique_planes,
            COUNT(DISTINCT f.dep_time) as unique_dep_times,
            COUNT(*) as total_occurrences
        FROM DuplicateFlights df
        JOIN flights f 
            ON df.year = f.year 
            AND df.month = f.month 
            AND df.day = f.day
            AND df.carrier = f.carrier 
            AND df.flight = f.flight
            AND df.origin = f.origin 
            AND df.dest = f.dest
        GROUP BY df.carrier, df.flight, df.origin, df.dest
        LIMIT 20
    """
    
    patterns = pd.read_sql_query(pattern_query, conn)
    
    if len(patterns) > 0:
        print(patterns.to_string(index=False))

        same_plane = patterns[patterns['unique_planes'] == 1]
        diff_plane = patterns[patterns['unique_planes'] > 1]

        print(f"\nsame plane: {len(same_plane)} (likely data errors)")
        print(f"different planes: {len(diff_plane)} (multiple ops per day)")
    
    conn.close()
    return patterns


def recommend_duplicate_resolution():
    """Print notes on how to handle each duplicate type."""
    recommendations = """
duplicate handling notes:

  exact duplicates (all cols match)     -> drop extras, keep one
  same flight, different tailnum        -> keep all (multiple ops same day)
  same flight, same plane, diff times   -> keep the one with dep_time not null
  same flight, same plane, same time    -> data error, drop extras

  quick fix: unique constraint on (year, month, day, carrier, flight, tailnum, dep_time)
  for analysis: GROUP BY or DISTINCT is usually enough
"""

    print(recommendations)
    return recommendations


def main():
    duplicates = find_duplicate_flights()
    exact_dups = check_exact_duplicates()
    patterns = analyze_duplicate_patterns()
    recommend_duplicate_resolution()


if __name__ == "__main__":
    main()