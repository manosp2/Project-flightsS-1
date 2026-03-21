import sqlite3
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / 'data' / 'flights_database.db'

conn = sqlite3.connect(DB_PATH)

print('missing value breakdown\n')

# how many flights are missing dep_time
print('dep_time nulls:')
missing_dep = pd.read_sql_query('''
    SELECT COUNT(*) as count,
           COUNT(DISTINCT carrier) as carriers,
           COUNT(DISTINCT origin) as origins,
           COUNT(DISTINCT dest) as destinations
    FROM flights 
    WHERE dep_time IS NULL
''', conn)
print(missing_dep.to_string(index=False))

# missing both — almost certainly cancelled
cancelled = pd.read_sql_query('''
    SELECT COUNT(*) as fully_cancelled
    FROM flights 
    WHERE dep_time IS NULL AND arr_time IS NULL
''', conn)
print(f'\nmissing both dep_time and arr_time (cancelled): {cancelled["fully_cancelled"][0]}')

# departed but no arrival — diverted or data gap
print('\narr_time missing (has dep_time):')
missing_arr = pd.read_sql_query('''
    SELECT COUNT(*) as count
    FROM flights 
    WHERE arr_time IS NULL AND dep_time IS NOT NULL
''', conn)
print(f'{missing_arr["count"][0]} departed with no arrival recorded')

# missing tailnum by carrier
print('\ntailnum nulls by carrier:')
missing_tail = pd.read_sql_query('''
    SELECT carrier, COUNT(*) as count
    FROM flights 
    WHERE tailnum IS NULL
    GROUP BY carrier
    ORDER BY count DESC
    LIMIT 10
''', conn)
print(missing_tail.to_string(index=False))

# check whether missing fields tend to cluster together
print('\nmissing value overlap:')
corr_analysis = pd.read_sql_query('''
    SELECT 
        'dep_time & arr_time both NULL' as scenario,
        COUNT(*) as count
    FROM flights 
    WHERE dep_time IS NULL AND arr_time IS NULL
    UNION ALL
    SELECT 
        'dep_delay & arr_delay both NULL' as scenario,
        COUNT(*) as count
    FROM flights 
    WHERE dep_delay IS NULL AND arr_delay IS NULL
    UNION ALL
    SELECT 
        'arr_time NULL & arr_delay NULL & air_time NULL' as scenario,
        COUNT(*) as count
    FROM flights 
    WHERE arr_time IS NULL AND arr_delay IS NULL AND air_time IS NULL
''', conn)
print(corr_analysis.to_string(index=False))

# quick look at what these rows actually contain
print('\nsample rows with nulls:')
sample = pd.read_sql_query('''
    SELECT year, month, day, carrier, flight, origin, dest, 
           dep_time, arr_time, dep_delay, arr_delay, tailnum, air_time
    FROM flights 
    WHERE dep_time IS NULL OR arr_time IS NULL OR tailnum IS NULL
    LIMIT 10
''', conn)
print(sample.to_string(index=False))

conn.close()
