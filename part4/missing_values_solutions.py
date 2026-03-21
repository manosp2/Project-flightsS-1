"""
Flags and fixes missing values in the flights table.

dep_time/dep_delay  10,738 missing  (cancelled flights, no dep or arr)
arr_time            11,453 missing
arr_delay/air_time  12,534 missing
tailnum              1,913 missing  (all cancelled)
"""

import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = str(Path(__file__).parent.parent / 'data' / 'flights_database.db')


def _connect():
    return sqlite3.connect(DB_PATH)


def _add_column(cursor, column, col_type, default):
    try:
        cursor.execute(f"ALTER TABLE flights ADD COLUMN {column} {col_type} DEFAULT {default}")
        print(f"added '{column}'")
    except sqlite3.OperationalError:
        print(f"'{column}' already exists")


def flag_cancelled():
    with _connect() as conn:
        _add_column(conn.cursor(), "cancelled", "INTEGER", 0)
        conn.execute("UPDATE flights SET cancelled = 1 WHERE dep_time IS NULL AND arr_time IS NULL")
        count = conn.execute("SELECT COUNT(*) FROM flights WHERE cancelled = 1").fetchone()[0]
        result = pd.read_sql_query(
            "SELECT cancelled, COUNT(*) as count FROM flights GROUP BY cancelled", conn
        )
    print(f"marked {count} as cancelled")
    print(result.to_string(index=False))
    return result


def flag_incomplete_arrivals():
    # departed but no arrival data — likely diverted or data gap
    with _connect() as conn:
        _add_column(conn.cursor(), "incomplete_arrival", "INTEGER", 0)
        conn.execute(
            "UPDATE flights SET incomplete_arrival = 1 "
            "WHERE dep_time IS NOT NULL AND arr_time IS NULL"
        )
        count = conn.execute(
            "SELECT COUNT(*) FROM flights WHERE incomplete_arrival = 1"
        ).fetchone()[0]
        analysis = pd.read_sql_query("""
            SELECT carrier, origin, dest, COUNT(*) as count, AVG(distance) as avg_distance
            FROM flights WHERE incomplete_arrival = 1
            GROUP BY carrier, origin, dest ORDER BY count DESC LIMIT 10
        """, conn)
    print(f"marked {count} with incomplete arrival data")
    print("top routes:")
    print(analysis.to_string(index=False))
    return analysis


def analyse_missing_tailnum():
    # can't fill these in — just understand the pattern
    with _connect() as conn:
        by_carrier = pd.read_sql_query("""
            SELECT carrier,
                   COUNT(*) as missing_tailnum_count,
                   ROUND(100.0 * COUNT(*) /
                       (SELECT COUNT(*) FROM flights WHERE carrier = f.carrier), 2
                   ) as pct_of_carrier_flights
            FROM flights f WHERE tailnum IS NULL
            GROUP BY carrier ORDER BY missing_tailnum_count DESC
        """, conn)
        by_month = pd.read_sql_query(
            "SELECT month, COUNT(*) as missing_tailnum_count "
            "FROM flights WHERE tailnum IS NULL GROUP BY month ORDER BY month", conn
        )
        correlation = pd.read_sql_query("""
            SELECT CASE WHEN dep_time IS NULL THEN 'Cancelled' ELSE 'Operated' END as flight_status,
                   COUNT(*) as count
            FROM flights WHERE tailnum IS NULL GROUP BY flight_status
        """, conn)
    print("by carrier:")
    print(by_carrier.to_string(index=False))
    print("\nby month:")
    print(by_month.to_string(index=False))
    print("\nflight status breakdown:")
    print(correlation.to_string(index=False))
    return by_carrier, by_month, correlation


def impute_delays():
    # recalculate from scheduled vs actual — only for non-cancelled flights
    with _connect() as conn:
        conn.execute("""
            UPDATE flights SET dep_delay = (dep_time - sched_dep_time) / 100.0
            WHERE dep_delay IS NULL AND dep_time IS NOT NULL
              AND sched_dep_time IS NOT NULL AND cancelled = 0
        """)
        dep_fixed = conn.execute("SELECT changes()").fetchone()[0]
        conn.execute("""
            UPDATE flights SET arr_delay = (arr_time - sched_arr_time) / 100.0
            WHERE arr_delay IS NULL AND arr_time IS NOT NULL
              AND sched_arr_time IS NOT NULL AND cancelled = 0
        """)
        arr_fixed = conn.execute("SELECT changes()").fetchone()[0]
    print(f"imputed {dep_fixed} dep_delay, {arr_fixed} arr_delay values")
    return dep_fixed, arr_fixed


def create_clean_view():
    with _connect() as conn:
        conn.execute("DROP VIEW IF EXISTS flights_clean")
        conn.execute("""
            CREATE VIEW flights_clean AS
            SELECT * FROM flights
            WHERE cancelled = 0 AND incomplete_arrival = 0
              AND dep_time IS NOT NULL AND arr_time IS NOT NULL
        """)
        result = pd.read_sql_query("""
            SELECT COUNT(*) as clean_flights,
                   (SELECT COUNT(*) FROM flights) as total_flights,
                   ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM flights), 2) as pct_retained
            FROM flights_clean
        """, conn)
    print("created flights_clean view")
    print(result.to_string(index=False))
    return result


def print_guidelines():
    print("""
missing value handling — notes:

  dep_time     exclude cancelled=1                       (~424,614 usable)
  arr_time     exclude cancelled + incomplete_arrival    (~423,899)
  delays       exclude cancelled; use flights_clean      (~424,614)
  tailnum      exclude tailnum IS NULL                   (~433,439)
  air_time     exclude cancelled + air_time IS NULL      (~422,818)
  carrier      keep all; flag cancelled; drop incomplete for arrivals
  time series  flights_clean for general work; full table for cancellation rates

default: use flights_clean. document any additional exclusions.
""")


def main():
    print("\n--- cancelled flights ---")
    flag_cancelled()

    print("\n--- incomplete arrivals ---")
    flag_incomplete_arrivals()

    print("\n--- missing tailnum ---")
    analyse_missing_tailnum()

    print("\n--- impute delays ---")
    impute_delays()

    print("\n--- clean view ---")
    create_clean_view()

    print_guidelines()

    # sanity check counts
    with _connect() as conn:
        summary = pd.read_sql_query("""
            SELECT 'Total flights'        as category, COUNT(*) as count FROM flights UNION ALL
            SELECT 'Cancelled flights',   COUNT(*) FROM flights WHERE cancelled = 1 UNION ALL
            SELECT 'Incomplete arrivals', COUNT(*) FROM flights WHERE incomplete_arrival = 1 UNION ALL
            SELECT 'Clean flights (view)',COUNT(*) FROM flights_clean UNION ALL
            SELECT 'Missing tailnum',     COUNT(*) FROM flights WHERE tailnum IS NULL
        """, conn)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()

