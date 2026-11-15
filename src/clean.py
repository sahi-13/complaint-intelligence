"""
Load, clean, and store CFPB Consumer Complaint data in SQLite.

Run from VS Code (Run button) or:  python src/clean.py
Defaults: reads data/raw/complaints_recent.csv (made by filter_raw.py)

What it does (in order):
    1. Reads the raw CSV (everything as text, so nothing is silently changed)
    2. Standardizes column names to snake_case
    3. Trims whitespace, parses dates, removes duplicates and unusable rows
    4. Adds helper columns used by the SQL analysis (flags, year_month, ...)
    5. Writes a data-quality report and loads the cleaned table into SQLite
"""
import argparse
import re
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent  # the project folder, wherever you run from


def to_snake(col: str) -> str:
    """'Timely response?' -> 'timely_response'"""
    return re.sub(r"[^0-9a-zA-Z]+", "_", col.strip().lower()).strip("_")


def load_raw(path: str) -> pd.DataFrame:
    # dtype=str keeps ZIP codes, IDs, etc. exactly as they appear in the file
    return pd.read_csv(path, dtype=str, low_memory=False)


def clean(df: pd.DataFrame):
    """Return (cleaned_df, log) where log records what was removed and why."""
    log = {"raw_rows": len(df)}
    df = df.copy()
    df.columns = [to_snake(c) for c in df.columns]
    df = df.rename(columns={
        "consumer_complaint_narrative": "narrative",
        "company_response_to_consumer": "company_response",
    })

    # Trim whitespace in all text columns
    for c in df.columns:
        df[c] = df[c].str.strip()
    df = df.replace({"": pd.NA})

    # Parse dates (bad values become NaT instead of crashing)
    df["date_received"] = pd.to_datetime(df["date_received"], errors="coerce")
    df["date_sent_to_company"] = pd.to_datetime(df["date_sent_to_company"], errors="coerce")

    # Drop rows we cannot analyse
    required = ["complaint_id", "date_received", "product", "company"]
    before = len(df)
    df = df.dropna(subset=required)
    log["dropped_missing_required"] = before - len(df)

    # Drop duplicate complaints
    before = len(df)
    df = df.drop_duplicates(subset="complaint_id")
    log["dropped_duplicates"] = before - len(df)

    # Standardize company names (uppercase) so they group correctly
    df["company"] = df["company"].str.upper()

    # Helper columns
    df["year_month"] = df["date_received"].dt.strftime("%Y-%m")
    df["year"] = df["date_received"].dt.year
    df["timely_flag"] = (df["timely_response"].str.lower() == "yes").astype(int)
    df["relief_flag"] = (
        df["company_response"].fillna("").str.lower().str.startswith("closed with monetary relief")
    ).astype(int)
    df["has_narrative"] = df["narrative"].notna().astype(int)
    df["days_to_company"] = (df["date_sent_to_company"] - df["date_received"]).dt.days

    log["clean_rows"] = len(df)
    return df, log


def quality_report(df: pd.DataFrame, log: dict, out_path: str) -> None:
    missing = (df.isna().mean() * 100).round(1).sort_values(ascending=False)
    lines = [
        "# Data Quality Report\n",
        f"- Raw rows: {log['raw_rows']:,}",
        f"- Dropped (missing key fields): {log['dropped_missing_required']:,}",
        f"- Dropped (duplicate complaint_id): {log['dropped_duplicates']:,}",
        f"- Clean rows: {log['clean_rows']:,}",
        f"- Date range: {df['date_received'].min().date()} to {df['date_received'].max().date()}",
        f"- Distinct companies: {df['company'].nunique():,}",
        f"- Distinct products: {df['product'].nunique():,}",
        "",
        "## Missing values (% of rows)\n",
        "| Column | Missing % |",
        "|---|---|",
    ]
    lines += [f"| {col} | {pct} |" for col, pct in missing.items()]
    lines += [
        "",
        "## Notes",
        "- Narratives were removed before analysis to keep the file small, so they show as missing.",
        "- Company names were uppercased to group variants together.",
    ]
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text("\n".join(lines), encoding="utf-8")


def write_sqlite(df: pd.DataFrame, db_path: str) -> None:
    out = df.copy()
    # SQLite has no date type: store dates as ISO text (YYYY-MM-DD)
    for c in ["date_received", "date_sent_to_company"]:
        out[c] = out[c].dt.strftime("%Y-%m-%d")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        out.to_sql("complaints", conn, if_exists="replace", index=False, chunksize=50_000)
        for col in ["company", "product", "issue", "state", "year_month"]:
            conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{col} ON complaints({col})")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", default=str(ROOT / "data" / "raw" / "complaints_recent.csv"),
                   help="Path to the (filtered) CFPB CSV")
    p.add_argument("--db", default=str(ROOT / "data" / "complaints.db"))
    p.add_argument("--report", default=str(ROOT / "reports" / "data_quality_report.md"))
    p.add_argument("--since", default=None, help="Keep complaints received on/after YYYY-MM-DD")
    args = p.parse_args()

    print(f"Reading: {args.input}")
    raw = load_raw(args.input)
    df, log = clean(raw)
    if args.since:
        df = df[df["date_received"] >= pd.Timestamp(args.since)]
        log["clean_rows"] = len(df)
    quality_report(df, log, args.report)
    write_sqlite(df, args.db)
    print(f"Done. {log['clean_rows']:,} clean rows -> {args.db}")
    print(f"Quality report -> {args.report}")


if __name__ == "__main__":
    main()