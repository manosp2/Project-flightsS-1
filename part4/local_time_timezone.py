"""
Adds local_arr_time and local_arr_datetime columns to flights,
adjusted for destination timezone.
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = str(PROJECT_ROOT / 'data' / 'flights_database.db')


# UTC offsets for US airports (standard time, no DST adjustment)
AIRPORT_TIMEZONES = {
    # Eastern (UTC-5)
    'EWR': -5, 'JFK': -5, 'LGA': -5,  # New York airports
    'ATL': -5, 'BOS': -5, 'BWI': -5, 'CLT': -5, 'DCA': -5,
    'DTW': -5, 'FLL': -5, 'IAD': -5, 'MIA': -5, 'MCO': -5,
    'PHL': -5, 'PIT': -5, 'RDU': -5, 'TPA': -5, 'BDL': -5,
    'BNA': -5, 'BUF': -5, 'CLE': -5, 'CMH': -5, 'CVG': -5,
    'IND': -5, 'JAX': -5, 'MEM': -5, 'MSY': -5, 'ORF': -5,
    'PBI': -5, 'RIC': -5, 'ROC': -5, 'RSW': -5, 'SAV': -5,
    'SRQ': -5, 'STL': -5, 'SYR': -5,
    
    # Central (UTC-6)
    'ORD': -6, 'DFW': -6, 'IAH': -6, 'MSP': -6, 'DTW': -6,
    'MCI': -6, 'MKE': -6, 'OMA': -6, 'SAT': -6, 'AUS': -6,
    'HOU': -6, 'OKC': -6, 'TUL': -6, 'DSM': -6,
    
    # Mountain (UTC-7)
    'DEN': -7, 'PHX': -7, 'SLC': -7, 'ABQ': -7, 'BZN': -7,
    'BOI': -7, 'TUS': -7, 'ELP': -7, 'MTJ': -7,
    
    # Pacific (UTC-8)
    'LAX': -8, 'SFO': -8, 'SEA': -8, 'SAN': -8, 'PDX': -8,
    'LAS': -8, 'SNA': -8, 'OAK': -8, 'SJC': -8, 'SMF': -8,
    'BUR': -8, 'ONT': -8, 'RNO': -8, 'PSP': -8,
    
    # Alaska (UTC-9)
    'ANC': -9, 'FAI': -9,

    # Hawaii (UTC-10)
    'HNL': -10,

    # Puerto Rico / US territories (UTC-4)
    'SJU': -4,  # Puerto Rico
    'STT': -4,  # US Virgin Islands
    'BQN': -4,  # Puerto Rico
    'PSE': -4,  # Puerto Rico
}

def get_timezone_offset(airport_code):
    """Look up UTC offset for an airport. Falls back to Eastern if not in the list."""
    return AIRPORT_TIMEZONES.get(airport_code, -5)

def add_timezone_info():
    """Tag each flight row with the UTC offset for its origin and destination airports."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("adding timezone offset columns")
    # Add timezone columns to flights table
    try:
        cursor.execute("ALTER TABLE flights ADD COLUMN origin_tz_offset INTEGER")
        cursor.execute("ALTER TABLE flights ADD COLUMN dest_tz_offset INTEGER")
        print("added")
    except sqlite3.OperationalError:
        print("already exist")
    
    # Get unique airports from flights
    airports_query = """
        SELECT DISTINCT origin as airport FROM flights
        UNION
        SELECT DISTINCT dest as airport FROM flights
    """
    airports = pd.read_sql_query(airports_query, conn)
    
    print(f"{len(airports)} airports found")
    print("updating origin offsets")
    for airport in airports['airport']:
        tz_offset = get_timezone_offset(airport)
        cursor.execute("""
            UPDATE flights
            SET origin_tz_offset = ?
            WHERE origin = ?
        """, (tz_offset, airport))
    print("updating dest offsets")
    for airport in airports['airport']:
        tz_offset = get_timezone_offset(airport)
        cursor.execute("""
            UPDATE flights
            SET dest_tz_offset = ?
            WHERE dest = ?
        """, (tz_offset, airport))
    conn.commit()
    
    # Verify
    sample = pd.read_sql_query("""
        SELECT origin, origin_tz_offset, dest, dest_tz_offset, COUNT(*) as flights
        FROM flights
        WHERE origin_tz_offset IS NOT NULL
        GROUP BY origin, dest
        LIMIT 10
    """, conn)
    
    print("\nsample:")
    print(sample.to_string(index=False))
    
    conn.close()

def add_local_arrival_time():
    """Add local arrival time for each flight based on the destination timezone."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("local arrival time")
    try:
        cursor.execute("ALTER TABLE flights ADD COLUMN local_arr_time REAL")
        cursor.execute("ALTER TABLE flights ADD COLUMN local_arr_datetime TEXT")
        print("added columns")
    except sqlite3.OperationalError:
        print("columns already exist")

    print("\nloading...\n")
    df = pd.read_sql_query("""
        SELECT rowid, year, month, day,
               dep_time, arr_time,
               origin_tz_offset, dest_tz_offset
        FROM flights
        WHERE arr_time IS NOT NULL
        AND origin_tz_offset IS NOT NULL
        AND dest_tz_offset IS NOT NULL
        AND cancelled = 0
        LIMIT 100000
    """, conn)
    
    print(f"{len(df)} flights — converting")
    
    def convert_to_datetime(year, month, day, time_value):
        """Turn an HHMM integer into a datetime. Handles times past midnight."""
        if pd.isna(time_value):
            return None
        time_int = int(time_value)
        hours = time_int // 100
        minutes = time_int % 100
        
        if hours >= 24:
            days_offset = hours // 24
            hours = hours % 24
            return datetime(year, month, day) + timedelta(days=days_offset, hours=hours, minutes=minutes)
        
        return datetime(year, month, day, hours, minutes)
    
    # Calculate local arrival times
    local_arr_times = []
    local_arr_datetimes = []
    
    for idx, row in df.iterrows():
        arr_dt = convert_to_datetime(row['year'], row['month'], row['day'], row['arr_time'])
        if arr_dt:
            # apply the timezone shift
            tz_diff = int(row['dest_tz_offset'] - row['origin_tz_offset'])
            local_arr_dt = arr_dt + timedelta(hours=tz_diff)
            
            # store as HHMM int
            local_arr_time = local_arr_dt.hour * 100 + local_arr_dt.minute
            local_arr_times.append(local_arr_time)
            local_arr_datetimes.append(local_arr_dt.isoformat())
        else:
            local_arr_times.append(None)
            local_arr_datetimes.append(None)
        
        if (idx + 1) % 10000 == 0:
            print(f"  {idx + 1}...")

    df['local_arr_time'] = local_arr_times
    df['local_arr_datetime'] = local_arr_datetimes

    print("\nwriting to db\n")
    for idx, row in df.iterrows():
        cursor.execute("""
            UPDATE flights
            SET local_arr_time = ?,
                local_arr_datetime = ?
            WHERE rowid = ?
        """, (row['local_arr_time'], row['local_arr_datetime'], row['rowid']))
        
        if (idx + 1) % 10000 == 0:
            conn.commit()
            print(f"  {idx + 1}...")

    conn.commit()

    print("\nsample (origin arr_time vs dest local):")
    sample = pd.read_sql_query("""
        SELECT carrier, flight, origin, dest,
               arr_time as arr_time_origin_tz,
               local_arr_time as arr_time_dest_tz,
               (dest_tz_offset - origin_tz_offset) as tz_diff_hours
        FROM flights
        WHERE local_arr_time IS NOT NULL
        AND origin != dest
        LIMIT 20
    """, conn)
    
    print(sample.to_string(index=False))
    print(f"\ndone — {len(df)} flights updated")
    
    conn.close()

def analyze_timezone_effects():
    """Quick look at how timezone gaps vary across routes, and flag cross-country ones."""
    conn = sqlite3.connect(DB_PATH)
    print("timezone spread by route")
    df = pd.read_sql_query("""
        SELECT 
            origin, dest,
            origin_tz_offset, dest_tz_offset,
            (dest_tz_offset - origin_tz_offset) as tz_diff,
            AVG(arr_delay) as avg_arr_delay,
            AVG(air_time) as avg_air_time,
            COUNT(*) as flight_count
        FROM flights
        WHERE local_arr_time IS NOT NULL
        AND cancelled = 0
        GROUP BY origin, dest, origin_tz_offset, dest_tz_offset
        HAVING flight_count > 50
        ORDER BY tz_diff DESC
        LIMIT 20
    """, conn)
    
    print("routes by timezone spread")
    print(df.to_string(index=False))

    print("\ncross-country (3+ hr tz diff):")
    cross_country = df[abs(df['tz_diff']) >= 3]
    if len(cross_country) > 0:
        print(f"Routes: {len(cross_country)}")
        print(f"Average air time: {cross_country['avg_air_time'].mean():.1f} minutes")
    
    conn.close()

def main():
    add_timezone_info()
    add_local_arrival_time()
    analyze_timezone_effects()

if __name__ == "__main__":
    main()