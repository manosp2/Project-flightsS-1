import sqlite3
import os
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "flights_database.db")


def connect(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Open a connection to the SQLite database."""
    return sqlite3.connect(db_path)


def query_df(query: str, params=(), db_path: str = DB_PATH) -> pd.DataFrame:
    """
    open connection -> run query -> close -> return DataFrame
    """
    with connect(db_path) as conn:
        return pd.read_sql_query(query, conn, params=params)


def sql_df(conn: sqlite3.Connection, query: str, params=()) -> pd.DataFrame:
    """Run SQL using an existing connection and return a DataFrame."""
    return pd.read_sql_query(query, conn, params=params)