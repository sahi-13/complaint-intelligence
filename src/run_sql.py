"""
Run a .sql file against the SQLite database and print the result.

Usage:
    python src/run_sql.py sql/02_monthly_trend.sql
"""
import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "complaints.db"

if __name__ == "__main__":
    query = open(sys.argv[1], encoding="utf-8").read()
    with sqlite3.connect(DB_PATH) as conn:
        result = pd.read_sql_query(query, conn)
    pd.set_option("display.width", 200, "display.max_columns", 20)
    print(result.to_string(index=False))